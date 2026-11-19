"""Rebuild the face-only README preview from licensed Pexels footage."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL.parents[1] / "shared"))
from preview_gif import write_comparison  # noqa: E402
import object_blur  # noqa: E402
import compiler  # noqa: E402
import model  # noqa: E402


STOCK_SHA256 = "30c30efe7298b19bfe9ec7aeb9f56e4c4a88ae52dda3a84849d3fb4d0bff9998"
WIDTH, HEIGHT, FPS, FRAMES = 640, 360, 4, 8
# Hand traced face contour at 640x360. Per-frame shifts follow the short source motion.
FACE_POINTS = [
    (297, 54), (352, 48), (406, 57), (441, 84), (451, 119),
    (482, 127), (500, 162), (486, 206), (458, 220), (453, 266),
    (420, 302), (377, 319), (335, 326), (289, 303), (257, 275),
    (251, 236), (243, 189), (249, 152), (275, 125), (282, 91),
]
X_SHIFTS = [0, 0, 4, 7, 11, 14, 15, 15]


def run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-1200:])


def build(source: Path, output: Path) -> None:
    if model.sha256_file(source) != STOCK_SHA256:
        raise ValueError("Expected the documented 1920x1080 Pexels download")
    with tempfile.TemporaryDirectory(prefix="object-blur-face-example-") as scratch:
        root = Path(scratch)
        edit = root / "edit.mp4"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
             "-y", "-ss", "0.5", "-t", "2", "-i", str(source),
             "-f", "lavfi", "-t", "2", "-i", "anullsrc=r=48000:cl=stereo",
             "-vf", "fps=4,scale=640:360", "-frames:v", str(FRAMES),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
             "-shortest", str(edit)])

        # A documentation fixture can exercise the pending preview path; it is
        # not a human-approved draft plan or a coverage review for user footage.
        preflight = root / "preflight"
        preflight.mkdir()
        plan = preflight / "plan.json"
        plan.write_text(json.dumps({"schema_version": 1, "kind": "edited",
                                    "stage": "edited-render", "steps": [{"id": "S01"}]}))
        plan_hash = model.sha256_file(plan)
        (preflight / "approval.json").write_text(json.dumps({
            "plan_sha256": plan_hash, "review_note": "documentation fixture only"}))
        (preflight / "checklist.json").write_text(json.dumps({
            "plan_sha256": plan_hash, "items": [{"id": "S01"}]}))
        timeline = model.make_initial(plan, edit, root / "unused-final.mp4",
                                      fps=FPS, width=WIDTH, height=HEIGHT)
        timeline["picture"][0]["source_out"] = FRAMES / FPS

        analysis_dir = root / "face-mask"
        analysis_dir.mkdir()
        mask = analysis_dir / "mask.mkv"
        blank = Image.new("RGB", (WIDTH, HEIGHT))
        raw_masks = []
        detections = []
        frame_records = []
        for index, shift in enumerate(X_SHIFTS):
            # The correction route uses a traced face polygon and leaves the
            # surrounding shot outside the matte.
            polygon = [[(x + shift) / WIDTH, y / HEIGHT]
                       for x, y in FACE_POINTS]
            face_mask = object_blur._frame_mask(
                blank, [], {"add_polygons": [polygon]})
            raw_masks.append(face_mask.tobytes())
            detections.append(json.dumps({"index": index, "detections": []}))
            frame_records.append(json.dumps({
                "index": index, "detections": 0, "selected": 0,
                "mask_pixels": int((face_mask > 0).sum()), "flagged": True,
                "manual_correction": True}))
        run_mask = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "640x360",
            "-r", "4", "-i", "-", "-frames:v", str(FRAMES),
            "-c:v", "ffv1", "-pix_fmt", "gray", str(mask),
        ], input=b"".join(raw_masks), capture_output=True)
        if run_mask.returncode:
            raise RuntimeError(run_mask.stderr.decode(errors="replace")[-1200:])
        detections_path = analysis_dir / "detections.jsonl"
        records_path = analysis_dir / "frames.jsonl"
        detections_path.write_text("\n".join(detections) + "\n")
        records_path.write_text("\n".join(frame_records) + "\n")
        report = {
            "schema": "content-studio.object-blur.v1", "source": str(edit),
            "source_sha256": model.sha256_file(edit), "target": "face",
            "fps": FPS, "width": WIDTH, "height": HEIGHT,
            "duration": FRAMES / FPS, "frames": FRAMES,
            "detector": {"id": "manual-face-annotation"},
            "masker": {"id": "manual-polygon-correction"},
            "detections_sha256": model.sha256_file(detections_path),
            "frames_sha256": model.sha256_file(records_path),
            "mask_sha256": model.sha256_file(mask),
            "flagged_frames": list(range(FRAMES)),
            "review_status": "pending_full_frame_coverage_review",
        }
        analysis = analysis_dir / "analysis.json"
        analysis.write_text(json.dumps(report, indent=2) + "\n")
        timeline.update(object_blur.changes(timeline, analysis))
        resolved = model.validate(timeline, require_review=False)
        preview = root / "pending-preview.mp4"
        compiler.preview(timeline, resolved, preview, 0, FRAMES / FPS)
        count = write_comparison(
            [edit, preview], ["SOURCE: REAL PERSON", "FACE ONLY: BLURRED"],
            output, duration=FRAMES / FPS, fps=FPS,
            panel=(480, 270), decode_size=(640, 360))
        if count != FRAMES:
            raise RuntimeError(f"Expected {FRAMES} preview frames, got {count}")
        print(f"Wrote {output} ({count} frames)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="The documented HD Pexels download")
    parser.add_argument("--output", type=Path,
                        default=HERE / "face-only-blur.gif")
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
