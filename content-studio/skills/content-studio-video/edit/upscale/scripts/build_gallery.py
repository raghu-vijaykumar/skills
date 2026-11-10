#!/usr/bin/env python3
"""Make honest, same-frame preview pairs from bounded upscale outputs."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def frame(video: Path, at: float, output: Path) -> Image.Image:
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-ss", str(at), "-i", str(video), "-map", "0:v:0", "-frames:v", "1",
        str(output),
    ], check=True)
    return Image.open(output).convert("RGB")


def pair(before: Image.Image, after: Image.Image, label: str, output: Path) -> None:
    # Keep native output pixels; nearest-neighbour input enlargement exposes
    # the missing detail rather than smoothing it before the comparison.
    if after.size != (before.width * 2, before.height * 2):
        raise ValueError(f"expected 2x output for {label}: {after.size}")
    width, height = after.size
    image = Image.new("RGB", (width * 2, height + 38), "#111820")
    image.paste(before.resize(after.size, Image.Resampling.NEAREST), (0, 38))
    image.paste(after, (width, 38))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 20)
    draw.text((12, 8), "320 x 180 input, enlarged 2x", font=font, fill="white")
    draw.text((width + 12, 8), f"{label}: 640 x 360 output", font=font, fill="white")
    image.save(output, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--lanczos", type=Path, required=True)
    parser.add_argument("--ncnn", type=Path, required=True)
    parser.add_argument("--pytorch", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--at", type=float, default=0.5)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        cache = Path(temp)
        before = frame(args.source, args.at, cache / "source.png")
        for name, video in (("lanczos", args.lanczos), ("real-esrgan", args.ncnn),
                            ("pytorch", args.pytorch)):
            after = frame(video, args.at, cache / f"{name}.png")
            pair(before, after, name, args.out / f"{name}-before-after.png")


if __name__ == "__main__":
    main()
