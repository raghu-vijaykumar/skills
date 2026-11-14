#!/usr/bin/env python3
"""Build a local foreground matte for the rising text-behind-subject edit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def probe(path: Path) -> dict:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams",
                             "-show_format", "-of", "json", str(path)],
                            capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    video = next((stream for stream in data["streams"]
                  if stream["codec_type"] == "video"), None)
    if not video:
        raise ValueError("Input has no video stream")
    return {"width": int(video["width"]), "height": int(video["height"]),
            "duration": float(data["format"]["duration"])}


def polygon_image(points: list, size: tuple[int, int]) -> Image.Image:
    """Optional ridge or foreground shape; coordinates are fractions of frame."""
    image = Image.new("L", size, 0)
    if not points:
        return image
    if len(points) < 3 or any(not isinstance(point, list) or len(point) != 2
                              or any(not isinstance(v, (int, float))
                                     or not math.isfinite(v) or not 0 <= v <= 1
                                     for v in point) for point in points):
        raise ValueError("foreground_polygon needs at least three normalized points")
    ImageDraw.Draw(image).polygon(
        [(round(x * (size[0] - 1)), round(y * (size[1] - 1)))
         for x, y in points], fill=255)
    return image


def person_model():
    """Torchvision's compact VOC segmentation model runs locally after caching."""
    import torch
    from torchvision.models.segmentation import (
        LRASPP_MobileNet_V3_Large_Weights, lraspp_mobilenet_v3_large)
    weights = LRASPP_MobileNet_V3_Large_Weights.COCO_WITH_VOC_LABELS_V1
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = lraspp_mobilenet_v3_large(weights=weights).to(device).eval()
    return model, weights.transforms(), weights.meta["categories"].index("person"), device


def person_image(frame: Image.Image, prepared: tuple) -> Image.Image:
    import torch
    import torch.nn.functional as functional
    model, transform, person_index, device = prepared
    with torch.inference_mode():
        logits = model(transform(frame).unsqueeze(0).to(device))["out"]
        logits = functional.interpolate(logits, size=(frame.height, frame.width),
                                        mode="bilinear", align_corners=False)
        # The person probability keeps soft edges instead of a jagged class ID.
        probability = torch.softmax(logits, dim=1)[0, person_index]
        alpha = ((probability - .12) / .76).clamp(0, 1)
        pixels = (alpha * 255).byte().cpu().numpy()
    return Image.fromarray(pixels).filter(ImageFilter.GaussianBlur(.7))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def generate(source: Path, output: Path, *, start: float, duration: float,
             fps: float, width: int, polygon: list, include_person: bool) -> dict:
    source, output = source.resolve(), output.resolve()
    if (not source.is_file() or output.exists() or source == output
            or output.with_suffix(".json").exists()):
        raise ValueError("Source must exist and matte output/record must be new files")
    info = probe(source)
    if (not math.isfinite(start) or not math.isfinite(duration)
            or start < 0 or duration <= 0 or start + duration > info["duration"] + .05
            or not math.isfinite(fps) or fps <= 0 or width < 64 or width % 2):
        raise ValueError("Invalid matte range, frame rate, or even width")
    height = max(2, round(info["height"] * width / info["width"] / 2) * 2)
    ridge = polygon_image(polygon, (width, height))
    if not include_person and not polygon:
        raise ValueError("Matte needs person segmentation or a foreground polygon")
    prepared = person_model() if include_person else None
    output.parent.mkdir(parents=True, exist_ok=True)
    count = round(duration * fps)
    if count < 1:
        raise ValueError("Matte duration must include at least one frame")
    with tempfile.TemporaryDirectory(prefix="subject-matte-", dir=output.parent) as scratch:
        temporary = Path(scratch) / "matte.mp4"
        decode = subprocess.Popen([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-ss", str(start), "-t", str(duration), "-i", str(source),
            "-vf", f"scale={width}:{height}:flags=bicubic,fps={fps}",
            "-frames:v", str(count), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        encode = subprocess.Popen([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{width}x{height}",
            "-r", str(fps), "-i", "-", "-frames:v", str(count),
            "-c:v", "libx264", "-crf", "0", "-pix_fmt", "yuv420p",
            str(temporary)], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frame_bytes = width * height * 3
        written = 0
        person_pixels = 0
        try:
            for _ in range(count):
                raw = decode.stdout.read(frame_bytes)
                if len(raw) != frame_bytes:
                    raise RuntimeError("Source ended before the requested matte range")
                frame = Image.frombytes("RGB", (width, height), raw)
                person = person_image(frame, prepared) if prepared else Image.new("L", frame.size, 0)
                if prepared:
                    person_pixels += int(np.count_nonzero(np.asarray(person) > 128))
                matte = np.maximum(np.asarray(person), np.asarray(ridge))
                encode.stdin.write(matte.tobytes())
                written += 1
        except BaseException:
            decode.kill()
            encode.kill()
            raise
        finally:
            decode.stdout.close()
            encode.stdin.close()
            decode_error = decode.stderr.read().decode(errors="replace")
            encode_error = encode.stderr.read().decode(errors="replace")
            decode.stderr.close()
            encode.stderr.close()
            decode_code = decode.wait()
            encode_code = encode.wait()
        if decode_code or encode_code or written != count:
            raise RuntimeError((decode_error + "\n" + encode_error)[-1200:])
        if include_person and person_pixels < 64:
            raise ValueError("No person was detected; review the shot or use --person off for terrain only")
        os.replace(temporary, output)
    record = {"source": str(source), "source_sha256": sha256(source),
              "matte": str(output), "matte_sha256": sha256(output),
              "start": start, "duration": duration, "fps": fps,
              "width": width, "height": height, "frames": written,
              "person_model": "torchvision-lraspp-voc" if include_person else None,
              "foreground_polygon": polygon,
              "review_status": "pending_moving_matte_review"}
    output.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n",
                                           encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--fps", type=float, default=30)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--foreground-polygon", type=Path,
                        help="JSON array of normalized [x,y] ridge points")
    parser.add_argument("--person", choices=["lraspp", "off"], default="lraspp")
    args = parser.parse_args()
    polygon = (json.loads(args.foreground_polygon.read_text(encoding="utf-8"))
               if args.foreground_polygon else [])
    result = generate(args.input, args.output, start=args.start,
                      duration=args.duration, fps=args.fps, width=args.width,
                      polygon=polygon, include_person=args.person == "lraspp")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
