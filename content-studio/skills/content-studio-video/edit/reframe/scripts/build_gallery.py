#!/usr/bin/env python3
"""Lay out the exact marked and cropped frames from bounded reframe previews."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def write_card(work: Path, name: str, output: Path) -> None:
    marked = Image.open(work / "preview" / "marked-01.jpg").convert("RGB")
    crop = Image.open(work / "preview" / "cropped-01.jpg").convert("RGB")
    # The crop is enlarged only for display; the red box is the actual
    # geometry selected by the method's reframe.json record.
    crop = crop.resize((round(crop.width * marked.height / crop.height),
                        marked.height), Image.Resampling.LANCZOS)
    card = Image.new("RGB", (marked.width + crop.width + 24,
                             marked.height + 38), "#111820")
    card.paste(marked, (0, 38))
    card.paste(crop, (marked.width + 24, 38))
    draw = ImageDraw.Draw(card)
    font = ImageFont.truetype("arial.ttf", 20)
    draw.text((12, 8), f"{name}: selected 9:16 crop", font=font, fill="white")
    draw.text((marked.width + 30, 8), "portrait result", font=font, fill="white")
    output.parent.mkdir(parents=True, exist_ok=True)
    card.save(output, quality=88, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for mode in ("subjects", "saliency", "center"):
        parser.add_argument(f"--{mode}", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    for mode in ("subjects", "saliency", "center"):
        write_card(getattr(args, mode), mode, args.out / f"{mode}-crop.jpg")


if __name__ == "__main__":
    main()
