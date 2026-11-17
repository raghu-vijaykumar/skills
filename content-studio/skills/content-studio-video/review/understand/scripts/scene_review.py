#!/usr/bin/env python3
"""Sample the exact picture around every narration cue and gate scene alignment.

Frame extraction is automatic. A vision reviewer must describe each cue's
visible beat and set its visual bounds; metadata alone cannot establish that
spoken words match what the viewer sees.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe_duration(video: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def cue_samples(start: float, end: float, duration: float) -> list[tuple[str, float]]:
    """Include both cue edges so a scene change near either edge is visible."""
    width = end - start
    offset = min(0.4, width / 4)
    candidates = [
        ("before", start - 0.4),
        ("start", start + offset),
        ("middle", (start + end) / 2),
        ("end", end - offset),
        ("after", end + 0.4),
    ]
    return [(role, round(max(0.0, min(duration - 0.04, at)), 3))
            for role, at in candidates]


def extract_frame(video: Path, at: float, output: Path, width: int) -> float:
    output.parent.mkdir(parents=True, exist_ok=True)
    for retry in range(5):
        sample_at = max(0.0, at - retry * 0.25)
        output.unlink(missing_ok=True)
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
             "-ss", f"{sample_at:.3f}", "-i", str(video), "-frames:v", "1",
             "-vf", f"scale={width}:-2", "-q:v", "3", str(output)],
            capture_output=True, text=True,
        )
        if result.returncode == 0 and output.is_file():
            # A container may end before its nominal duration or have a low
            # frame rate; record the fallback seek instead of a false time.
            return round(sample_at, 3)
    raise RuntimeError(f"Frame extraction failed near {at:.3f}s: {result.stderr[-500:]}")


def make_sheets(out: Path, cues: list[dict], width: int) -> list[str]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:
        raise RuntimeError("Cue sheets require Pillow") from error
    sheets_dir = out / "sheets"
    sheets_dir.mkdir(exist_ok=True)
    for old in sheets_dir.glob("cue-sheet-*.jpg"):
        old.unlink()
    font = ImageFont.load_default()
    paths = []
    for page, offset in enumerate(range(0, len(cues), 4), start=1):
        chunk = cues[offset:offset + 4]
        with Image.open(out / chunk[0]["frames"][0]["path"]) as first:
            height = first.height
        canvas = Image.new("RGB", (width * 5 + 48, (height + 54) * len(chunk) + 24), "#17191d")
        draw = ImageDraw.Draw(canvas)
        for row, cue in enumerate(chunk):
            top = 12 + row * (height + 54)
            draw.text((8, top), f"{cue['id']}  {cue['start']:.3f}-{cue['end']:.3f}s",
                      fill="white", font=font)
            for column, frame in enumerate(cue["frames"]):
                with Image.open(out / frame["path"]) as image:
                    canvas.paste(image.convert("RGB"), (8 + column * (width + 8), top + 18))
                draw.text((8 + column * (width + 8), top + height + 20),
                          f"{frame['role']} {frame['at_seconds']:.2f}s",
                          fill="#d1d8e0", font=font)
        path = sheets_dir / f"cue-sheet-{page:03d}.jpg"
        canvas.save(path, quality=86)
        paths.append(str(path.relative_to(out)))
    return paths


def generate(video: Path, script_path: Path, out: Path, width: int = 320) -> dict:
    """Create pending review evidence; never auto-approve semantic alignment."""
    if width < 128:
        raise ValueError("frame width must be at least 128 pixels")
    script = json.loads(script_path.read_text(encoding="utf-8-sig"))
    segments = script.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("script must contain narration segments")
    duration = probe_duration(video)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("video duration must be positive")
    out.mkdir(parents=True, exist_ok=True)
    cues = []
    seen = set()
    previous_end = 0.0
    for segment in segments:
        cue_id = str(segment["id"])
        if not re.fullmatch(r"[A-Za-z0-9_-]+", cue_id) or cue_id in seen:
            raise ValueError(f"{cue_id}: cue id must be unique and filename-safe")
        seen.add(cue_id)
        start, end = float(segment["start"]), float(segment["end"])
        if not 0 <= start < end <= duration + 0.05:
            raise ValueError(f"{cue_id}: cue lies outside the video")
        if start < previous_end - 0.05:
            raise ValueError(f"{cue_id}: cue overlaps the previous one")
        previous_end = end
        frames = []
        for role, at in cue_samples(start, end, duration):
            path = Path("frames") / f"{cue_id}-{role}.jpg"
            actual_seek = extract_frame(video, at, out / path, width)
            frames.append({"role": role, "at_seconds": actual_seek, "path": str(path)})
        cues.append({
            "id": cue_id, "start": start, "end": end,
            "visual_start": None, "visual_end": None,
            "visual_description": "", "scene_match": "pending", "frames": frames,
        })
    sheets = make_sheets(out, cues, width)
    review = {
        "schema_version": 1, "picture_sha256": sha256(video),
        "script_sha256": sha256(script_path), "duration_seconds": duration,
        "cue_sheets": sheets, "cues": cues,
    }
    (out / "scene-review.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = ["# Narration cue picture review", "",
             "Set each cue's visual bounds and scene match in `scene-review.json` after inspecting these frames.",
             "Frame times are approximate seek positions; inspect more frames near ambiguous cuts.", ""]
    for cue, segment in zip(cues, segments):
        lines += [f"## {cue['id']} · {cue['start']:.3f}–{cue['end']:.3f}s", "",
                  str(segment.get("text", "")).replace("\n", " "), ""]
        for frame in cue["frames"]:
            lines.append(f"![{cue['id']} {frame['role']} {frame['at_seconds']:.3f}s]({frame['path'].replace(chr(92), '/')})")
        lines += [""]
    (out / "scene-review.md").write_text("\n".join(lines), encoding="utf-8")
    return review


def validate(review: dict, script: dict, script_sha256: str | None = None,
             picture_sha256: str | None = None, review_root: Path | None = None) -> list[str]:
    """Reject missing, stale, unreviewed, or visually out-of-window cues."""
    errors = []
    if script_sha256 and review.get("script_sha256") != script_sha256:
        errors.append("scene review does not match the exact narration script")
    if picture_sha256 and review.get("picture_sha256") != picture_sha256:
        errors.append("scene review does not match the exact picture")
    cues = review.get("cues")
    segments = script.get("segments", [])
    if not isinstance(cues, list) or len(cues) != len(segments):
        return errors + ["scene review must cover every narration cue"]
    for segment, cue in zip(segments, cues):
        cue_id = str(segment.get("id"))
        if cue.get("id") != cue_id:
            errors.append(f"{cue_id}: scene review cue order or id differs")
            continue
        try:
            start, end = float(segment["start"]), float(segment["end"])
            reviewed_start, reviewed_end = float(cue["start"]), float(cue["end"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"{cue_id}: cue timestamps are missing or invalid")
            continue
        if abs(start - reviewed_start) > 0.02 or abs(end - reviewed_end) > 0.02:
            errors.append(f"{cue_id}: cue timing changed after scene review")
        frames = cue.get("frames")
        if not isinstance(frames, list) or len(frames) < 5 or {f.get("role") for f in frames} != {
            "before", "start", "middle", "end", "after"
        }:
            errors.append(f"{cue_id}: missing boundary and middle frame evidence")
        elif review_root is not None:
            for frame in frames:
                relative = Path(str(frame.get("path") or ""))
                if relative.is_absolute() or ".." in relative.parts or not (review_root / relative).is_file():
                    errors.append(f"{cue_id}: missing or unsafe frame {relative}")
        if cue.get("scene_match") != "match" or not str(cue.get("visual_description") or "").strip():
            errors.append(f"{cue_id}: picture and narration meaning need visual review or rewrite")
        try:
            visual_start = float(cue["visual_start"])
            visual_end = float(cue["visual_end"])
        except (TypeError, ValueError, KeyError):
            errors.append(f"{cue_id}: visual start/end must be set from frames")
            continue
        if not 0 <= visual_start < visual_end:
            errors.append(f"{cue_id}: visual bounds are invalid")
        if start < visual_start - 0.5 or end > visual_end + 0.05:
            errors.append(f"{cue_id}: spoken window exceeds reviewed visual bounds")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare or check frame-backed narration cue review")
    sub = parser.add_subparsers(dest="action", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--video", type=Path, required=True)
    prepare.add_argument("--script", type=Path, required=True)
    prepare.add_argument("--out", type=Path, required=True)
    prepare.add_argument("--frame-width", type=int, default=320)
    check = sub.add_parser("check")
    check.add_argument("--review", type=Path, required=True)
    check.add_argument("--script", type=Path, required=True)
    check.add_argument("--video", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "prepare":
        review = generate(args.video.resolve(), args.script.resolve(), args.out.resolve(), args.frame_width)
        print(json.dumps({"status": "awaiting_visual_review", "cues": len(review["cues"]),
                          "review": str(args.out / "scene-review.json"), "sheets": len(review["cue_sheets"])}))
        return
    review = json.loads(args.review.read_text(encoding="utf-8"))
    script = json.loads(args.script.read_text(encoding="utf-8-sig"))
    errors = validate(review, script, sha256(args.script), sha256(args.video), args.review.parent)
    print(json.dumps({"status": "fail" if errors else "pass", "errors": errors}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
