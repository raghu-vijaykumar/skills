#!/usr/bin/env python3
"""Build a reproducible image-generation brief for one character style."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "catalog" / "character-styles.json"


def prompt_for(style_id: str, brief: str) -> str:
    if not brief.strip():
        raise ValueError("Character brief is required")
    styles = json.loads(CATALOG.read_text(encoding="utf-8"))["styles"]
    style = next((item for item in styles if item["id"] == style_id), None)
    if not style:
        raise ValueError(f"Unknown character style: {style_id}")
    # Identity and framing precede rendering style so a comparison changes only the treatment.
    return (f"Create one original character image. Character and composition: {brief.strip()}\n"
            f"Visual style: {style['prompt']}\n"
            "Preserve the stated identity, clothing, pose and framing. Do not depict an existing "
            "franchise character or copy a living artist's signature style. No text, logo or watermark.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style", required=True)
    parser.add_argument("--brief", type=Path, required=True)
    args = parser.parse_args()
    print(prompt_for(args.style, args.brief.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
