#!/usr/bin/env python3
"""Animate matching input, reference, and output at the same source times."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if parent.name == "content-studio-video")
sys.path.insert(0, str(ROOT / "shared"))
from preview_gif import write_comparison  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "before", "after", "out"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--duration", type=float, default=1.5)
    args = parser.parse_args()
    write_comparison([args.reference, args.before, args.after],
                     ["REFERENCE", "WARM INPUT", "MATCHED OUTPUT"], args.out,
                     start=args.start, duration=args.duration, fps=8)


if __name__ == "__main__":
    main()
