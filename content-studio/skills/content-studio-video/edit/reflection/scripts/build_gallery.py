"""Animate actual bounded reflection candidates beside their source window."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = next(parent for parent in Path(__file__).resolve().parents
            if parent.name == "content-studio-video")
sys.path.insert(0, str(ROOT / "shared"))
from preview_gif import write_comparison  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--ai", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=SKILL / "previews")
    args = parser.parse_args()
    # Both results are review candidates; neither is approved reflection
    # removal or a final deliverable.
    for name, candidate in (("bounded-preview", args.preview),
                            ("ai-review", args.ai)):
        write_comparison([args.source, candidate],
                         ["SOURCE", "REVIEW CANDIDATE"],
                         args.out / f"{name}.gif", duration=1, fps=8)


if __name__ == "__main__":
    main()
