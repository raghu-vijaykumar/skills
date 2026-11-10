#!/usr/bin/env python3
"""Show matching input, reference, and output at one source timestamp."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def extract(video: Path, at: float, path: Path) -> Image.Image:
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-ss", str(at), "-i", str(video), "-map", "0:v:0", "-frames:v", "1",
        str(path),
    ], check=True)
    return Image.open(path).convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "before", "after", "out"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--at", type=float, default=0.75)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        panels = [(label, extract(getattr(args, name), args.at,
                                  folder / f"{name}.png"))
                  for name, label in (("reference", "Reference"),
                                      ("before", "Warm-shifted input"),
                                      ("after", "Shot-match output"))]
    width, height = panels[0][1].size
    if any(image.size != (width, height) for _, image in panels):
        raise ValueError("all comparison clips must have the same frame size")
    card = Image.new("RGB", (width * len(panels), height + 38), "#111820")
    draw = ImageDraw.Draw(card)
    font = ImageFont.truetype("arial.ttf", 20)
    for index, (label, panel) in enumerate(panels):
        # Keep every frame at its native 640 x 360 preview size.
        card.paste(panel, (index * width, 38))
        draw.text((index * width + 12, 8), label, font=font, fill="white")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    card.save(args.out, quality=90, optimize=True)


if __name__ == "__main__":
    main()
