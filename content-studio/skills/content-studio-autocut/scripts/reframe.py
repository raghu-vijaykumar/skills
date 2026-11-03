#!/usr/bin/env python3
"""Subject-aware portrait reframing for landscape footage.

Subject boxes from a vision model take priority; otherwise a saliency/edge
heuristic picks a stable crop; center crop is the final fallback.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - optional preview dependency
    Image = ImageDraw = None


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-1800:])
    return result.stdout


def probe_size(path):
    data = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)]))
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise ValueError("No video stream: " + str(path))
    width, height = int(video.get("width") or 0), int(video.get("height") or 0)
    if width <= 0 or height <= 0:
        raise ValueError("Invalid dimensions: " + str(path))
    return width, height


def probe_duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=nw=1:nk=1", str(path)]).strip())


def parse_size(value):
    import re
    match = re.fullmatch(r"(\d+)x(\d+)", str(value).strip().lower())
    if not match:
        raise ValueError("Size must look like 1080x1920")
    width, height = int(match.group(1)), int(match.group(2))
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise ValueError("Size must use positive even dimensions")
    return width, height


def crop_shape(source_width, source_height, target_width, target_height):
    """Return normalized crop width/height for a target aspect."""
    source_ratio = source_width / source_height
    target_ratio = target_width / target_height
    if abs(source_ratio - target_ratio) < 1e-6:
        return 1.0, 1.0
    if source_ratio > target_ratio:
        return target_ratio / source_ratio, 1.0
    return 1.0, source_ratio / target_ratio


def load_subject_boxes(path):
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    items = data.get("subjects", data.get("segments", data)) if isinstance(data, dict) else data
    boxes = {}
    for item in items or []:
        source = Path(str(item.get("source", item.get("file", "")))).name
        box = item.get("box") or {key: item.get(key) for key in ("x", "y", "w", "h")}
        try:
            x, y, w, h = (float(box[key]) for key in ("x", "y", "w", "h"))
        except (KeyError, TypeError, ValueError):
            continue
        if w <= 0 or h <= 0:
            continue
        boxes.setdefault(source, []).append({
            "start": float(item.get("start", 0)),
            "end": float(item.get("end", float("inf"))),
            "x": x, "y": y, "w": w, "h": h,
            "confidence": float(item.get("confidence", 0.8)),
            "label": str(item.get("label", "subject")),
        })
    for values in boxes.values():
        values.sort(key=lambda value: value["start"])
    return boxes


def box_at(boxes, stamp):
    candidates = [box for box in boxes
                  if box["start"] <= stamp <= box["end"]]
    if not candidates:
        return None
    return max(candidates, key=lambda box: (box["confidence"], box["w"] * box["h"]))


def sample_frames(source, start, end, source_width, source_height, fps=2, width=160):
    height = max(2, round(width * source_height / source_width / 2) * 2)
    raw = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-i", str(source),
         "-t", str(max(0.1, end - start)), "-vf", f"fps={fps},scale={width}:{height},format=gray",
         "-f", "rawvideo", "-"], capture_output=True)
    if raw.returncode:
        raise RuntimeError((raw.stderr or b"").decode("utf-8", errors="replace")[-1200:])
    size = width * height
    frames = []
    for index in range(0, len(raw.stdout) // size):
        chunk = raw.stdout[index * size:(index + 1) * size]
        frames.append(np.frombuffer(chunk, dtype=np.uint8).reshape(height, width))
    return frames, start, 1.0 / fps


def saliency_center(frame, crop_width, crop_height):
    height, width = frame.shape
    values = frame.astype(np.float32)
    laplace = np.abs(4 * values[1:-1, 1:-1] - values[:-2, 1:-1] - values[2:, 1:-1]
                     - values[1:-1, :-2] - values[1:-1, 2:])
    if crop_width < 1.0:
        window = max(4, int(round(width * crop_width)))
        if window >= width:
            return 0.5, 0.5, 0.3
        step = max(1, window // 8)
        best = (-1.0, 0.5)
        for x in range(0, width - window + 1, step):
            score = float(laplace[:, x:x + window].mean())
            center = (x + window / 2) / width
            score *= 0.8 + 0.2 * (1 - abs(center - 0.5) * 2)
            if score > best[0]:
                best = (score, center)
        return best[1], 0.5, min(1.0, max(0.2, best[0] / 12.0))
    if crop_height < 1.0:
        window = max(4, int(round(height * crop_height)))
        if window >= height:
            return 0.5, 0.5, 0.3
        step = max(1, window // 8)
        best = (-1.0, 0.5)
        for y in range(0, height - window + 1, step):
            score = float(laplace[y:y + window, :].mean())
            center = (y + window / 2) / height
            score *= 0.8 + 0.2 * (1 - abs(center - 0.5) * 2)
            if score > best[0]:
                best = (score, center)
        return 0.5, best[1], min(1.0, max(0.2, best[0] / 12.0))
    return 0.5, 0.5, 0.3


def clamps(value, low, high):
    return max(low, min(high, value))


def analyze_segment(source, start, end, target_size, mode="auto", subjects_path=None):
    source = Path(source)
    source_width, source_height = probe_size(source)
    target_width, target_height = target_size
    crop_width, crop_height = crop_shape(source_width, source_height,
                                         target_width, target_height)
    boxes = load_subject_boxes(subjects_path).get(source.name, [])
    frames, first_stamp, step = sample_frames(source, start, end, source_width, source_height)
    samples = []
    for index, frame in enumerate(frames):
        stamp = first_stamp + index * step
        box = box_at(boxes, stamp)
        if mode in {"auto", "subjects"} and box:
            center_x = box["x"] + box["w"] / 2
            center_y = box["y"] + box["h"] / 2
            kind, confidence = "subjects", box["confidence"]
        elif mode in {"auto", "saliency"}:
            center_x, center_y, score = saliency_center(frame, crop_width, crop_height)
            kind, confidence = "saliency", score
        elif mode == "center":
            center_x, center_y, kind, confidence = 0.5, 0.5, "center", 0.3
        else:
            raise ValueError("No subject box for this range and mode=" + mode)
        center_x = clamps(center_x, crop_width / 2, 1 - crop_width / 2)
        center_y = clamps(center_y, crop_height / 2, 1 - crop_height / 2)
        samples.append({"t": round(stamp - start, 3), "center_x": round(center_x, 5),
                        "center_y": round(center_y, 5), "kind": kind,
                        "confidence": round(confidence, 3)})
    if not samples:
        samples = [{"t": 0.0, "center_x": 0.5, "center_y": 0.5,
                    "kind": "center", "confidence": 0.3}]
    center_x = float(np.median([sample["center_x"] for sample in samples]))
    center_y = float(np.median([sample["center_y"] for sample in samples]))
    confidence = float(np.mean([sample["confidence"] for sample in samples]))
    mode_used = "hybrid" if len({sample["kind"] for sample in samples}) > 1 \
        else samples[0]["kind"]
    return {
        "schema_version": 1,
        "source": source.name,
        "source_width": source_width,
        "source_height": source_height,
        "target_width": target_width,
        "target_height": target_height,
        "range": [round(start, 3), round(end, 3)],
        "mode": mode_used,
        "crop": {
            "x": round(clamps(center_x - crop_width / 2, 0, 1 - crop_width), 6),
            "y": round(clamps(center_y - crop_height / 2, 0, 1 - crop_height), 6),
            "w": round(crop_width, 6),
            "h": round(crop_height, 6),
        },
        "confidence": round(confidence, 3),
        "samples": samples,
    }


def write_preview(source, record, output, count=3):
    if Image is None:
        return None
    source = Path(source)
    folder = Path(output)
    frames_dir = folder / "preview"
    frames_dir.mkdir(parents=True, exist_ok=True)
    start, end = record["range"]
    times = [start + (end - start) * portion for portion in
             [0.1, 0.5, 0.9][:max(1, min(count, 3))]]
    cards = []
    for index, stamp in enumerate(times):
        raw = frames_dir / f"frame-{index:02d}.jpg"
        run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(stamp),
             "-i", str(source), "-frames:v", "1", "-vf", "scale=960:-2", str(raw)])
        with Image.open(raw) as image:
            image = image.convert("RGB")
            width, height = image.size
            crop = record["crop"]
            box = (round(crop["x"] * width), round(crop["y"] * height),
                   round((crop["x"] + crop["w"]) * width),
                   round((crop["y"] + crop["h"]) * height))
            marked = image.copy()
            ImageDraw.Draw(marked).rectangle(box, outline=(255, 40, 40), width=6)
            marked_path = frames_dir / f"marked-{index:02d}.jpg"
            marked.save(marked_path, quality=88)
            cropped_path = frames_dir / f"cropped-{index:02d}.jpg"
            image.crop(box).save(cropped_path, quality=88)
            cards.append(
                f"<article><h3>{stamp:.2f}s</h3>"
                f"<img src='preview/{marked_path.name}' width='480'>"
                f"<img src='preview/{cropped_path.name}' width='240'></article>")
    page = ("<!doctype html><meta charset='utf-8'><title>Reframe review</title>"
            "<style>body{font:16px system-ui;background:#171923;color:#f8fafc;max-width:1100px;margin:2rem auto}"
            "article{display:inline-block;vertical-align:top;margin:8px;padding:10px;border:1px solid #475569;border-radius:10px}"
            "img{display:block;max-width:100%;margin:4px 0}</style>"
            f"<h1>Reframe review — {record['source']}</h1>"
            f"<p>mode={record['mode']} confidence={record['confidence']} "
            f"crop x={record['crop']['x']:.3f} y={record['crop']['y']:.3f} "
            f"w={record['crop']['w']:.3f} h={record['crop']['h']:.3f}</p>"
            "<p>Red rectangle = 9:16 crop. The narrow image is the framed result.</p>"
            + "".join(cards))
    path = folder / "reframe-review.html"
    path.write_text(page, encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--end", type=float)
    parser.add_argument("--size", default="1080x1920")
    parser.add_argument("--mode", choices=["auto", "subjects", "saliency", "center"],
                        default="auto")
    parser.add_argument("--subjects", type=Path,
                        help="JSON subject boxes with source/start/end/box")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    end = args.end if args.end is not None else probe_duration(args.input)
    if end <= args.start:
        parser.error("--end must be after --start")
    record = analyze_segment(args.input, args.start, end, parse_size(args.size),
                             args.mode, args.subjects)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "reframe.json").write_text(json.dumps(record, indent=2) + "\n",
                                             encoding="utf-8")
    preview = write_preview(args.input, record, args.output)
    print(json.dumps({"record": str(args.output / "reframe.json"),
                      "preview": str(preview) if preview else None,
                      "crop": record["crop"], "mode": record["mode"],
                      "confidence": record["confidence"]}, indent=2))


if __name__ == "__main__":
    main()
