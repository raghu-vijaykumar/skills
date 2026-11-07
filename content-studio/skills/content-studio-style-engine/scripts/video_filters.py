#!/usr/bin/env python3
"""Apply creator-neutral color-look presets to selected video time ranges using FFmpeg."""
import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

PRESETS = {
    "warm-golden": {"contrast": 1.06, "brightness": 0.015, "saturation": 1.16, "gamma": 1.04},
    "cool-cinematic": {"contrast": 1.13, "brightness": -0.015, "saturation": 0.82, "gamma": 0.97},
    "vintage-fade": {"contrast": 0.88, "brightness": 0.035, "saturation": 0.72, "gamma": 1.08},
    "vibrant-travel": {"contrast": 1.08, "brightness": 0.01, "saturation": 1.3, "gamma": 1.02},
    "soft-portrait": {"contrast": 0.95, "brightness": 0.02, "saturation": 0.94, "gamma": 1.05},
    "mono-noir": {"contrast": 1.22, "brightness": -0.025, "saturation": 0, "gamma": 0.94},
    "clean-natural": {"contrast": 1.02, "brightness": 0, "saturation": 1.04, "gamma": 1},
}

def validate_ranges(ranges):
    if not isinstance(ranges, list) or not ranges:
        raise ValueError("ranges must be a nonempty list")
    ordered = sorted(ranges, key=lambda r: float(r["start"]))
    previous = 0
    for item in ordered:
        start, end = float(item["start"]), float(item["end"])
        if not all(math.isfinite(v) for v in (start, end)) or not 0 <= start < end or start < previous:
            raise ValueError("Ranges must be positive, non-overlapping and increasing")
        if item.get("preset") not in PRESETS:
            raise ValueError(f"Unknown preset: {item.get('preset')}")
        previous = end
    return ordered

def filters(ranges):
    # enable evaluates source timeline seconds. Non-selected portions remain unchanged.
    parts = []
    for item in validate_ranges(ranges):
        p = PRESETS[item["preset"]]
        start, end = float(item["start"]), float(item["end"])
        enable = f"between(t\\,{start:.6f}\\,{end:.6f})"
        parts.append("eq=" + ":".join([
            f"contrast={p['contrast']}", f"brightness={p['brightness']}",
            f"saturation={p['saturation']}", f"gamma={p['gamma']}",
            f"enable='{enable}'"
        ]))
    return ",".join(parts)

def render(input_path, output_path, ranges, ffmpeg="ffmpeg", crf=18, preset="medium", preview=None):
    source, target = Path(input_path).resolve(), Path(output_path).resolve()
    if not source.is_file() or source == target:
        raise ValueError("Input must exist and output must be a different file")
    if not shutil.which(ffmpeg):
        raise RuntimeError("FFmpeg not found")
    if not 0 <= crf <= 51:
        raise ValueError("CRF must be 0..51")
    if preview is not None and (preview[0] < 0 or not 0 < preview[1] <= 30):
        raise ValueError('Preview must be at most 30 seconds')
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-hide_banner", "-nostdin", "-n", "-i", str(source),
               "-map", "0:v:0", "-map", "0:a?", "-vf", filters(ranges),
               "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
               "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(target)]
    if preview is not None:
        command[command.index("-map"):command.index("-map")] = ["-ss", str(preview[0]), "-t", str(preview[1])]
    subprocess.run(command, check=True)
    return target

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    p = sub.add_parser("render")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--ranges", required=True, help="JSON file containing ranges array")
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--ffmpeg", default="ffmpeg")
    p.add_argument("--preview-start", type=float)
    p.add_argument("--preview-duration", type=float, default=5)
    args = parser.parse_args()
    if args.command == "list":
        print(json.dumps(PRESETS, indent=2))
    else:
        data = json.loads(Path(args.ranges).read_text(encoding="utf-8"))
        preview = (args.preview_start, args.preview_duration) if args.preview_start is not None else None
        render(args.input, args.output, data["ranges"], args.ffmpeg, args.crf, preview=preview)

if __name__ == "__main__":
    main()
