#!/usr/bin/env python3
"""Match shot-to-shot mean color balance across a folder of vlog clips.

This is a conservative gray-balance match, not creative grading. It should run
after upscaling and before per-clip technical/creative correction.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

import enhance

EXTS = {".mp4", ".mov", ".mkv", ".m4v", ".webm", ".avi"}


class MatchError(RuntimeError):
    pass


def run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise MatchError((result.stderr or result.stdout)[-3000:])


def mean_color(path: Path, duration: float) -> dict:
    values = []
    for fraction in (0.2, 0.5, 0.8):
        rgb = enhance.extract_frame(path, max(0.0, duration * fraction))
        values.append(rgb.reshape(-1, 3).mean(axis=0))
    return {"r": float(np.mean([v[0] for v in values])),
            "g": float(np.mean([v[1] for v in values])),
            "b": float(np.mean([v[2] for v in values]))}


def gains_for(current: dict, target: dict) -> dict:
    return {key: round(max(0.88, min(1.12,
                                     target[key] / max(current[key], 1e-4))), 4)
            for key in ("r", "g", "b")}


def match_folder(args) -> dict:
    folder = Path(args.folder).expanduser().resolve()
    sources = sorted(p for p in folder.iterdir()
                     if p.is_file() and p.suffix.lower() in EXTS)
    if not sources:
        raise MatchError(f"no videos in {folder}")
    output = Path(args.output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    stats = []
    for source in sources:
        info = enhance.probe_video(source)
        stats.append({"source": source, "info": info,
                      "color": mean_color(source, info["duration_seconds"])})
    if args.reference:
        reference = Path(args.reference).expanduser().resolve()
        if not reference.is_file():
            raise MatchError(f"reference missing: {reference}")
        ref_info = enhance.probe_video(reference)
        target = mean_color(reference, ref_info["duration_seconds"])
        target_source = str(reference)
    else:
        target = {key: float(np.median([item["color"][key] for item in stats]))
                  for key in ("r", "g", "b")}
        target_source = "median of folder"
    results = []
    for item in stats:
        gains = gains_for(item["color"], target)
        target_path = output / (item["source"].stem + "-matched.mp4")
        run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(item["source"]), "-vf",
             f"colorchannelmixer=rr={gains['r']}:gg={gains['g']}:bb={gains['b']}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart",
             str(target_path)])
        results.append({"source": str(item["source"]), "output": str(target_path),
                        "before": item["color"], "gains": gains})
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "folder": str(folder),
        "reference": target_source,
        "target": target,
        "results": results,
    }
    (output / "color-match.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                             encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reference", type=Path,
                        help="match every clip to this reference clip; default median of folder")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(json.dumps(match_folder(args), indent=2))
        return 0
    except (MatchError, OSError, ValueError) as exc:
        print(f"match: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
