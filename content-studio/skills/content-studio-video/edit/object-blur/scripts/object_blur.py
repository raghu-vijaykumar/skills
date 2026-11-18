#!/usr/bin/env python3
"""Find named objects in an edited video and prepare a reviewed blur matte."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Installed and source-tree skills share this relative layout.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "timeline" / "scripts"))
import compiler  # noqa: E402
import model as timeline_model  # noqa: E402

DETECTOR_ID = "IDEA-Research/grounding-dino-tiny"
DETECTOR_REVISION = "a2bb814dd30d776dcf7e30523b00659f4f141c71"
MASKER_ID = "facebook/sam2.1-hiera-tiny"
MASKER_REVISION = "de431c4"
DETECTION_THRESHOLD = 0.25
TEXT_THRESHOLD = 0.25


def sha256(path: Path) -> str:
    return timeline_model.sha256_file(path)


def source_contract(timeline: dict) -> tuple[dict, dict]:
    """Only an uncut SDR manual render has a stable frame-to-matte mapping."""
    resolved = timeline_model.validate(timeline, require_review=False)
    clips = resolved["clips"]
    if (len(clips) != 1 or clips[0]["source_in"] != 0
            or resolved["transitions"] or timeline["color_policy"] != "sdr"
            or timeline["video_policy"] != "encode"
            or any(op["method"] not in timeline_model.AUDIO_METHODS
                   for op in resolved["operations"])):
        raise ValueError("Object blur needs one uncut SDR picture without other picture effects")
    source = clips[0]["path"]
    info = compiler.media_info(source)
    video = info["video"]
    if (not video or abs(info["duration"] - resolved["duration"]) > .08
            or video.get("color_transfer") in {"smpte2084", "arib-std-b67"}
            or video.get("color_primaries") == "bt2020"
            or "10" in str(video.get("pix_fmt", ""))
            or "12" in str(video.get("pix_fmt", ""))
            or any(label in json.dumps(video.get("side_data_list", [])).lower()
                   for label in ("dovi", "dolby vision"))):
        raise ValueError("Object blur needs a full-length SDR source")
    return resolved, info


def frame_command(source: Path, *, duration: float, fps: float,
                  width: int, height: int, count: int) -> list[str]:
    # Match the delivery renderer's scale, pad and frame-rate order exactly.
    filters = (f"scale={width}:{height}:force_original_aspect_ratio=decrease:"
               f"flags=bicubic,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
               f"setsar=1,fps={fps:g},format=rgb24")
    return ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-ss", "0", "-t", f"{duration:.6f}", "-i", str(source),
            "-vf", filters, "-frames:v", str(count), "-an", "-f", "rawvideo",
            "-pix_fmt", "rgb24", "-"]


def read_frames(command: list[str], width: int, height: int, count: int):
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    size = width * height * 3
    try:
        for index in range(count):
            raw = process.stdout.read(size)
            if len(raw) != size:
                raise RuntimeError(f"Decoder stopped at frame {index}/{count}")
            yield index, Image.frombytes("RGB", (width, height), raw)
    except BaseException:
        process.kill()
        raise
    finally:
        process.stdout.close()
        errors = process.stderr.read().decode(errors="replace")
        process.stderr.close()
        code = process.wait()
        if code:
            raise RuntimeError(f"Frame decode failed: {errors[-900:]}")


class TextDetector:
    def __init__(self):
        import torch
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = AutoProcessor.from_pretrained(
            DETECTOR_ID, revision=DETECTOR_REVISION)
        self.model = AutoModelForZeroShotObjectDetection.from_pretrained(
            DETECTOR_ID, revision=DETECTOR_REVISION).to(self.device).eval()

    def detect(self, image: Image.Image, target: str) -> list[dict]:
        inputs = self.processor(images=image, text=[[target]],
                                return_tensors="pt").to(self.device)
        with self.torch.inference_mode():
            output = self.model(**inputs)
        result = self.processor.post_process_grounded_object_detection(
            output, inputs.input_ids, threshold=DETECTION_THRESHOLD,
            text_threshold=TEXT_THRESHOLD,
            target_sizes=[(image.height, image.width)])[0]
        return [{"box": [float(x) for x in box.tolist()],
                 "score": float(score.item())}
                for box, score in zip(result["boxes"], result["scores"])]


class BoxMasker:
    def __init__(self):
        import torch
        from transformers import Sam2Model, Sam2Processor
        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = Sam2Processor.from_pretrained(
            MASKER_ID, revision=MASKER_REVISION)
        self.model = Sam2Model.from_pretrained(
            MASKER_ID, revision=MASKER_REVISION).to(self.device).eval()

    def masks(self, image: Image.Image, boxes: list[list[float]]) -> list[np.ndarray]:
        if not boxes:
            return []
        inputs = self.processor(images=image, input_boxes=[boxes],
                                return_tensors="pt").to(self.device)
        with self.torch.inference_mode():
            output = self.model(**inputs, multimask_output=False)
        masks = self.processor.post_process_masks(
            output.pred_masks.cpu(), inputs["original_sizes"])[0]
        return [np.asarray(mask).squeeze() > 0 for mask in masks]


def _load_corrections(path: Path | None, frame_count: int) -> dict[int, dict]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for item in data.get("frames", []):
        index = item.get("index")
        if (not isinstance(index, int) or not 0 <= index < frame_count
                or index in result or set(item) - {"index", "replace_boxes", "add_polygons", "exclude_polygons"}):
            raise ValueError("Invalid or duplicate correction frame")
        result[index] = item
    return result


def _box(box: list, width: int, height: int) -> list[float]:
    if (not isinstance(box, list) or len(box) != 4
            or any(not isinstance(v, (int, float)) or not math.isfinite(v)
                   for v in box)
            or not 0 <= box[0] < box[2] <= 1
            or not 0 <= box[1] < box[3] <= 1):
        raise ValueError("Correction box must be normalized [x1,y1,x2,y2]")
    return [box[0] * width, box[1] * height,
            box[2] * width, box[3] * height]


def _polygon(points: list, width: int, height: int) -> Image.Image:
    if (not isinstance(points, list) or len(points) < 3
            or any(not isinstance(p, list) or len(p) != 2
                   or any(not isinstance(v, (int, float)) or not math.isfinite(v)
                          or not 0 <= v <= 1 for v in p) for p in points)):
        raise ValueError("Correction polygon needs three normalized points")
    image = Image.new("L", (width, height), 0)
    ImageDraw.Draw(image).polygon([(round(x * (width - 1)), round(y * (height - 1)))
                                   for x, y in points], fill=255)
    return image


def _select_one(detections: list[dict], click: tuple[int, float, float] | None,
                index: int, previous: list[float] | None,
                width: int, height: int) -> tuple[list[dict], bool]:
    if click is None:
        return detections, False
    if index == click[0]:
        x, y = click[1] * width, click[2] * height
        matches = [d for d in detections if d["box"][0] <= x <= d["box"][2]
                   and d["box"][1] <= y <= d["box"][3]]
        return (matches[:1], len(matches) != 1)
    if previous is None or not detections:
        return [], bool(detections or previous)
    def overlap(box):
        x1, y1 = max(box[0], previous[0]), max(box[1], previous[1])
        x2, y2 = min(box[2], previous[2]), min(box[3], previous[3])
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        union = ((box[2] - box[0]) * (box[3] - box[1])
                 + (previous[2] - previous[0]) * (previous[3] - previous[1])
                 - intersection)
        return intersection / union if union else 0
    ranked = sorted(detections, key=lambda d: overlap(d["box"]), reverse=True)
    best = overlap(ranked[0]["box"])
    return (ranked[:1], False) if best >= .2 else ([], True)


def _track_selections(rows: list[dict], clicks: list[tuple[int, float, float]],
                      width: int, height: int) -> tuple[dict[int, int], set[int]]:
    """Associate a clicked instance both ways; require a new seed after loss."""
    selected: dict[int, int] = {}
    uncertain: set[int] = set()
    ordered = sorted(clicks)
    for seed_position, click in enumerate(ordered):
        seed = click[0]
        found = rows[seed]["detections"]
        matches, ambiguous = _select_one(found, click, seed, None, width, height)
        if ambiguous or not matches:
            uncertain.add(seed)
            continue
        chosen = found.index(matches[0])
        if seed in selected and selected[seed] != chosen:
            uncertain.add(seed)
            continue
        selected[seed] = chosen
        seed_box = matches[0]["box"]
        for direction in (-1, 1):
            previous = seed_box
            boundary = (ordered[seed_position + 1][0]
                        if direction > 0 and seed_position + 1 < len(ordered)
                        else ordered[seed_position - 1][0]
                        if direction < 0 and seed_position > 0
                        else len(rows) if direction > 0 else -1)
            for index in range(seed + direction, boundary,
                               direction):
                if index in selected:
                    break
                found = rows[index]["detections"]
                matches, ambiguous = _select_one(found, click, index, previous,
                                                  width, height)
                if ambiguous or not matches:
                    uncertain.add(index)
                    break
                selected[index] = found.index(matches[0])
                previous = matches[0]["box"]
    # Other instances cannot silently stand in for the selected one.
    uncertain.update(index for index, row in enumerate(rows)
                     if row["detections"] and index not in selected)
    return selected, uncertain


def _frame_mask(image: Image.Image, masks: list[np.ndarray],
                correction: dict | None) -> np.ndarray:
    width, height = image.size
    combined = np.zeros((height, width), dtype=np.uint8)
    for mask in masks:
        if mask.shape != combined.shape:
            raise ValueError("Segmentation mask dimensions do not match the frame")
        combined[np.asarray(mask, dtype=bool)] = 255
    if correction:
        for points in correction.get("add_polygons", []):
            combined = np.maximum(combined, np.asarray(_polygon(points, width, height)))
        for points in correction.get("exclude_polygons", []):
            combined[np.asarray(_polygon(points, width, height)) > 0] = 0
    # A small margin covers unstable edges without blurring a whole rectangle.
    radius = max(3, round(min(width, height) * .024)) | 1
    return np.asarray(Image.fromarray(combined).filter(
        ImageFilter.MaxFilter(radius)).filter(ImageFilter.GaussianBlur(1.2)))


def analyze(timeline: dict, out_dir: Path, target: str, *,
            click: tuple[int, float, float] | list[tuple[int, float, float]] | None = None,
            corrections_path: Path | None = None,
            detector_factory=TextDetector, masker_factory=BoxMasker) -> dict:
    resolved, _ = source_contract(timeline)
    if not isinstance(target, str) or not target.strip() or len(target) > 120:
        raise ValueError("Target description must contain 1-120 characters")
    source = resolved["clips"][0]["path"]
    width, height, fps = resolved["width"], resolved["height"], resolved["fps"]
    count = round(resolved["duration"] * fps)
    clicks = [click] if isinstance(click, tuple) else (click or [])
    if (count < 1 or any(not 0 <= chosen[0] < count
                         or not 0 <= chosen[1] <= 1 or not 0 <= chosen[2] <= 1
                         for chosen in clicks)
            or len({chosen[0] for chosen in clicks}) != len(clicks)):
        raise ValueError("Invalid frame count or selected point")
    corrections = _load_corrections(corrections_path, count)
    out_dir = out_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError("Analysis output directory must be empty")
    out_dir.mkdir(parents=True, exist_ok=True)
    decode = frame_command(source, duration=resolved["duration"], fps=fps,
                           width=width, height=height, count=count)
    detection_path = out_dir / "detections.jsonl"
    with detection_path.open("x", encoding="utf-8") as stream:
        detector = detector_factory()
        for index, frame in read_frames(decode, width, height, count):
            found = detector.detect(frame, target)
            for candidate in found:
                _box([candidate["box"][0] / width,
                      candidate["box"][1] / height,
                      candidate["box"][2] / width,
                      candidate["box"][3] / height], width, height)
            stream.write(json.dumps({"index": index, "detections": found}) + "\n")
        del detector
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
    matte = out_dir / "mask.mkv"
    records = out_dir / "frames.jsonl"
    flagged: list[int] = []
    previous_boxes: list[list[float]] = []
    previous_pixels = 0
    any_match = False
    rows = [json.loads(line) for line in detection_path.read_text(
        encoding="utf-8").splitlines()]
    if len(rows) != count or any(row["index"] != index
                                 for index, row in enumerate(rows)):
        raise ValueError("Detection frame count or order changed")
    selections, selection_flags = _track_selections(rows, clicks, width, height) if clicks else ({}, set())
    with tempfile.TemporaryDirectory(prefix="object-blur-", dir=out_dir) as scratch:
        temporary = Path(scratch) / "mask.mkv"
        encoder = subprocess.Popen([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
            "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{width}x{height}",
            "-r", f"{fps:g}", "-i", "-", "-frames:v", str(count),
            "-c:v", "ffv1", "-pix_fmt", "gray", str(temporary)],
            stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        masker = masker_factory()
        with records.open("x", encoding="utf-8") as record_file:
            try:
                for index, frame in read_frames(decode, width, height, count):
                    row = rows[index]
                    correction = corrections.get(index)
                    found = row["detections"]
                    if correction and "replace_boxes" in correction:
                        found = [{"box": _box(box, width, height), "score": 1.0}
                                 for box in correction["replace_boxes"]]
                    if clicks:
                        if correction and "replace_boxes" in correction and len(found) == 1:
                            selected = found
                        else:
                            chosen = selections.get(index)
                            selected = found[chosen:chosen + 1] if chosen is not None else []
                        ambiguous = index in selection_flags
                    else:
                        selected, ambiguous = found, False
                    masks = masker.masks(frame, [d["box"] for d in selected])
                    if len(masks) != len(selected):
                        raise ValueError("Segmentation did not return one mask per detection")
                    empty = any(not np.asarray(mask).any() for mask in masks)
                    if empty or ambiguous:
                        flagged.append(index)
                    mask = _frame_mask(frame, masks, correction)
                    pixels = int(np.count_nonzero(mask))
                    any_match |= bool(selected)
                    # Changes in target count, sudden entrances and implausible
                    # mask area jumps all need human inspection for concealment.
                    changed_count = index > 0 and len(selected) != len(previous_boxes)
                    area_jump = (index > 0 and previous_pixels > 0 and pixels > 0
                                 and (pixels > previous_pixels * 3
                                      or previous_pixels > pixels * 3))
                    uncertain = empty or ambiguous or changed_count or area_jump
                    if uncertain and (not flagged or flagged[-1] != index):
                        flagged.append(index)
                    encoder.stdin.write(mask.tobytes())
                    record_file.write(json.dumps({
                        "index": index, "detections": len(found),
                        "selected": len(selected), "mask_pixels": pixels,
                        "flagged": uncertain,
                        "manual_correction": correction is not None}) + "\n")
                    previous_boxes = [candidate["box"] for candidate in selected]
                    previous_pixels = pixels
            except BaseException:
                encoder.kill()
                raise
            finally:
                encoder.stdin.close()
                error = encoder.stderr.read().decode(errors="replace")
                encoder.stderr.close()
                code = encoder.wait()
            if code:
                raise RuntimeError(f"Mask encoding failed: {error[-900:]}")
        os.replace(temporary, matte)
    if not any_match:
        # An entirely empty automatic result is never evidence that a
        # sensitive target was absent from the supplied video.
        flagged = list(range(count))
    analysis = {
        "schema": "content-studio.object-blur.v1", "source": str(source),
        "source_sha256": sha256(source), "target": target.strip(),
        "selection": [{"frame": chosen[0], "x": chosen[1], "y": chosen[2]}
                      for chosen in clicks] if clicks else None,
        "fps": fps, "width": width, "height": height,
        "duration": resolved["duration"], "frames": count,
        "detector": {"id": DETECTOR_ID, "revision": DETECTOR_REVISION},
        "masker": {"id": MASKER_ID, "revision": MASKER_REVISION},
        "detections_sha256": sha256(detection_path),
        "frames_sha256": sha256(records),
        "corrections_sha256": sha256(corrections_path) if corrections_path else None,
        "mask_sha256": sha256(matte), "flagged_frames": flagged,
        "review_status": "pending_full_frame_coverage_review",
    }
    (out_dir / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n",
                                           encoding="utf-8")
    return analysis


def changes(timeline: dict, analysis_path: Path,
            coverage_review: Path | None = None) -> dict:
    resolved, _ = source_contract(timeline)
    analysis_path = analysis_path.resolve()
    coverage_review = coverage_review.resolve() if coverage_review else None
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    mask = analysis_path.with_name("mask.mkv")
    if (analysis.get("schema") != "content-studio.object-blur.v1"
            or analysis.get("source_sha256") != resolved["clips"][0]["sha256"]
            or analysis.get("mask_sha256") != sha256(mask)
            or analysis.get("frames") != round(resolved["duration"] * resolved["fps"])
            or analysis.get("width") != resolved["width"]
            or analysis.get("height") != resolved["height"]):
        raise ValueError("Object-blur analysis is stale or mismatched")
    root = resolved["root"]
    operation = {
        "id": "object-blur-01", "method": "object-blur", "start": 0,
        "end": resolved["duration"], "target": analysis["target"],
        "mask_source": str(mask.relative_to(root)), "mask_sha256": sha256(mask),
        "analysis_source": str(analysis_path.relative_to(root)),
        "analysis_sha256": sha256(analysis_path),
        "review_status": "pending_review",
    }
    if coverage_review:
        operation["coverage_review_source"] = str(coverage_review.relative_to(root))
        operation["coverage_review_sha256"] = sha256(coverage_review)
    proposal = {**timeline, "operations": [*timeline["operations"], operation]}
    timeline_model.validate(proposal, require_review=False)
    return {"operations": proposal["operations"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    analyze_cmd = commands.add_parser("analyze")
    analyze_cmd.add_argument("--timeline", type=Path, required=True)
    analyze_cmd.add_argument("--target", required=True)
    analyze_cmd.add_argument("--out-dir", type=Path, required=True)
    analyze_cmd.add_argument("--click", action="append",
                             help="Select one object: FRAME,X,Y normalized; repeat after a cut")
    analyze_cmd.add_argument("--corrections", type=Path)
    changes_cmd = commands.add_parser("changes")
    changes_cmd.add_argument("--timeline", type=Path, required=True)
    changes_cmd.add_argument("--analysis", type=Path, required=True)
    changes_cmd.add_argument("--coverage-review", type=Path)
    changes_cmd.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        timeline = timeline_model.load(args.timeline)
        if args.command == "analyze":
            clicks = []
            if args.click:
                for item in args.click:
                    pieces = item.split(",")
                    if len(pieces) != 3:
                        raise ValueError("--click needs FRAME,X,Y")
                    clicks.append((int(pieces[0]), float(pieces[1]), float(pieces[2])))
            result = analyze(timeline, args.out_dir, args.target,
                             click=clicks, corrections_path=args.corrections)
            print(json.dumps({"analysis": str(args.out_dir / "analysis.json"),
                              "frames": result["frames"],
                              "flagged_frames": len(result["flagged_frames"])}))
        else:
            result = changes(timeline, args.analysis, args.coverage_review)
            timeline_model.write_new(args.out, result)
            print(json.dumps({"changes": str(args.out)}))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
