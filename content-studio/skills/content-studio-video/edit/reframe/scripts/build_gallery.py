#!/usr/bin/env python3
"""Animate each approved crop geometry over its bounded source range."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if parent.name == "content-studio-video")
sys.path.insert(0, str(ROOT / "shared"))
from preview_gif import write_comparison  # noqa: E402


def write_crop(work: Path, source: Path, name: str, output: Path) -> None:
    record = json.loads((work / "reframe.json").read_text(encoding="utf-8"))
    geometry = record["crop"]
    if record["mode"] != name or record["source_width"] != 640:
        raise ValueError("Gallery input does not match the method crop record")

    def bounds(frame: Image.Image) -> tuple[int, int, int, int]:
        return (round(geometry["x"] * frame.width),
                round(geometry["y"] * frame.height),
                round((geometry["x"] + geometry["w"]) * frame.width),
                round((geometry["y"] + geometry["h"]) * frame.height))

    def marked(frame: Image.Image) -> Image.Image:
        # Use the method's JSON crop on every source frame, not a fixed
        # screenshot, so the editor can inspect the moving subject boundary.
        canvas = Image.new("RGB", (320, 360), "#111820")
        image = frame.resize((320, 180), Image.Resampling.LANCZOS)
        box = bounds(frame)
        draw = ImageDraw.Draw(image)
        draw.rectangle(tuple(round(v / 2) for v in box), outline="#ff4b4b", width=3)
        canvas.paste(image, (0, 90))
        return canvas

    def cropped(frame: Image.Image) -> Image.Image:
        image = frame.crop(bounds(frame)).resize((180, 320),
                                               Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (320, 360), "#111820")
        canvas.paste(image, (70, 20))
        return canvas

    write_comparison([source, source], [f"{name}: SOURCE BOX", "PORTRAIT CROP"],
                     output, duration=1.5, fps=8, panel=(320, 360),
                     transforms=[marked, cropped])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for mode in ("subjects", "saliency", "center"):
        parser.add_argument(f"--{mode}", type=Path, required=True)
    parser.add_argument("--source-cooking", type=Path, required=True)
    parser.add_argument("--source-fountain", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    for mode in ("subjects", "saliency", "center"):
        source = (args.source_fountain if mode == "saliency"
                  else args.source_cooking)
        write_crop(getattr(args, mode), source, mode,
                   args.out / f"{mode}-crop.gif")


if __name__ == "__main__":
    main()
