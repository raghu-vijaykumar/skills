"""Render a bounded published shot through the actual warm-golden preset."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = next(parent for parent in Path(__file__).resolve().parents
            if parent.name == "content-studio-video")
REPO = next(parent for parent in Path(__file__).resolve().parents
            if (parent / ".git").exists())
sys.path.insert(0, str(ROOT / "shared"))
from preview_gif import write_comparison  # noqa: E402


def run(args: list[str]) -> None:
    # Published Windows paths may contain Unicode punctuation in FFmpeg logs.
    result = subprocess.run(args, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(result.stderr[-1200:])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-video", type=Path, required=True)
    parser.add_argument("--at", type=float, default=245)
    args = parser.parse_args()
    work = REPO / "tmp/capability-gallery/color-preset"
    work.mkdir(parents=True, exist_ok=True)
    source, grade = work / "source.mp4", work / "warm-golden.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss",
         str(args.at), "-i", str(args.source_video), "-f", "lavfi",
         "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
         "-t", "2", "-vf", "scale=640:360:flags=lanczos,fps=8",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a",
         "aac", str(source)])
    ranges = work / "ranges.json"
    ranges.write_text(json.dumps({"ranges": [
        {"start": 0, "end": 2, "preset": "warm-golden"}
    ]}), encoding="utf-8")
    if grade.exists():
        grade.unlink()
    run([sys.executable, str(SKILL / "scripts/preset.py"), "render",
         "--input", str(source), "--output", str(grade), "--ranges", str(ranges)])
    target = SKILL / "previews/before-after.gif"
    write_comparison([source, grade], ["BEFORE", "AFTER: warm-golden"],
                     target, duration=2, fps=8)
    print(target)


if __name__ == "__main__":
    main()
