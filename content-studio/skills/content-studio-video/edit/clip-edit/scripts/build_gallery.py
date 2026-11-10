#!/usr/bin/env python3
"""Create small visual evidence from actual bounded trim, cut, and join outputs."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def still(video: Path, at: float, path: Path) -> Image.Image:
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-ss", str(at), "-i", str(video), "-map", "0:v:0", "-frames:v", "1",
        "-vf", "scale=480:270", str(path),
    ], check=True)
    return Image.open(path).convert("RGB")


def gif(video: Path, label: str, path: Path) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-i", str(video), "-map", "0:v:0", "-vf",
            "fps=6,scale=480:270:flags=lanczos", str(folder / "%03d.png"),
        ], check=True)
        font = ImageFont.truetype("arial.ttf", 18)
        frames = []
        for index, file in enumerate(sorted(folder.glob("*.png"))):
            image = Image.new("RGB", (480, 300), "#111820")
            image.paste(Image.open(file).convert("RGB"), (0, 30))
            ImageDraw.Draw(image).text((10, 6), f"{label}  {index / 6:.1f}s",
                                       font=font, fill="white")
            frames.append(image)
        if not frames:
            raise ValueError(f"no frames decoded: {video}")
        frames[0].save(path, save_all=True, append_images=frames[1:],
                       duration=167, loop=0, optimize=True)


def contact(video: Path, path: Path) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        labels = ((0.5, "A: cooking"), (1.5, "B: fountain"),
                  (2.5, "C: cooking"))
        card = Image.new("RGB", (1440, 300), "#111820")
        draw = ImageDraw.Draw(card)
        font = ImageFont.truetype("arial.ttf", 18)
        for index, (at, label) in enumerate(labels):
            card.paste(still(video, at, folder / f"{index}.png"),
                       (480 * index, 30))
            draw.text((480 * index + 10, 6), label, font=font, fill="white")
        card.save(path, quality=88, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("joined", "trim", "cut", "out"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, label in (("joined", "JOIN: A + B + C"),
                        ("trim", "TRIM: 0.4 to 2.2 seconds"),
                        ("cut", "CUT: remove 1 to 2 seconds")):
        gif(getattr(args, name), label, args.out / f"{name}-preview.gif")
    # A static three-point contact sheet is better evidence for reviewing the
    # supplied render's sequence than reusing one edit-operation GIF.
    contact(args.joined, args.out / "review-contact.jpg")


if __name__ == "__main__":
    main()
