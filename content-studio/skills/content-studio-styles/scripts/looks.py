#!/usr/bin/env python3
"""CLI for timeline look editing, graded rendering and side-by-side review."""
import argparse
import json
import sys
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BUNDLE_ROOT / "skills" / "content-studio-videoedit" / "scripts"))

from filters import PRESETS, compare_looks, render_looks  # noqa: E402
from look_timeline import load_looks, annotate_timeline  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input SDR MP4 or timeline JSON")
    parser.add_argument("--looks", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", choices=["timeline", "render", "compare"], required=True)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--duration", type=float, default=5)
    args = parser.parse_args()
    looks = load_looks(args.looks)
    root = args.looks.resolve().parent
    if args.mode == "timeline":
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = annotate_timeline(data, looks, PRESETS, root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return
    if args.mode == "render":
        render_looks(args.input, args.output, looks, PRESETS, root)
    else:
        compare_looks(args.input, args.output, looks, PRESETS, root,
                      args.start, args.duration)


if __name__ == "__main__":
    main()
