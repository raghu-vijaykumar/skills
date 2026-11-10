#!/usr/bin/env python3
"""Make moving, time-aligned comparisons from bounded upscale outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if parent.name == "content-studio-video")
sys.path.insert(0, str(ROOT / "shared"))
from preview_gif import write_comparison  # noqa: E402


def source_view(frame: Image.Image) -> Image.Image:
    # Expose source pixels at 2x nearest-neighbour scale, then show the same
    # central 320x180 output-pixel region as the upscaled candidates.
    if frame.size != (320, 180):
        raise ValueError("gallery source must be 320x180")
    return frame.resize((640, 360), Image.Resampling.NEAREST).crop(
        (160, 90, 480, 270))


def output_view(frame: Image.Image) -> Image.Image:
    if frame.size != (640, 360):
        raise ValueError("gallery output must be 640x360")
    return frame.crop((160, 90, 480, 270))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--lanczos", type=Path, required=True)
    parser.add_argument("--ncnn", type=Path, required=True)
    parser.add_argument("--pytorch", type=Path, required=True)
    parser.add_argument("--compare-lanczos", type=Path, required=True)
    parser.add_argument("--compare-ai", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, video in (("lanczos", args.lanczos), ("real-esrgan", args.ncnn),
                        ("pytorch", args.pytorch)):
        write_comparison([args.source, video], ["INPUT: 2x nearest", name],
                         args.out / f"{name}-before-after.gif", duration=1.2,
                         fps=10, transforms=[source_view, output_view])
    write_comparison([args.source, args.compare_lanczos, args.compare_ai],
                     ["INPUT: 2x nearest", "COMPARE: Lanczos", "COMPARE: AI"],
                     args.out / "compare-three-panel.gif", duration=1.2,
                     fps=10, transforms=[source_view, output_view, output_view])


if __name__ == "__main__":
    main()
