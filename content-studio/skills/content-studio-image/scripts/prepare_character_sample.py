#!/usr/bin/env python3
"""Copy a generated original character portrait into a compact catalog sample."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def prepare(source: Path, output: Path, size=512) -> Path:
    if output.exists():
        raise FileExistsError(f"Sample already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image = image.convert("RGB")
        edge = min(image.size)
        left = (image.width - edge) // 2
        top = (image.height - edge) // 2
        image = image.crop((left, top, left + edge, top + edge))
        image = image.resize((size, size), Image.Resampling.LANCZOS)
        # A bounded palette keeps the visual catalog small while preserving a legible preview.
        image.quantize(colors=192, method=Image.Quantize.MEDIANCUT).save(output, optimize=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.source, args.output))


if __name__ == "__main__":
    main()
