#!/usr/bin/env python3
"""CLI for timeline look editing, graded rendering and side-by-side review."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from look_timeline import load_looks, graph, annotate_timeline
from video_filters import PRESETS, ensure_sdr

def run(args):
    subprocess.run(args, check=True)

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
    if args.mode == "timeline":
        data = json.loads(args.input.read_text(encoding="utf-8"))
        result = annotate_timeline(data, looks, PRESETS, args.looks.resolve().parent)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required")
    ensure_sdr(args.input)
    if args.mode == "compare" and not (0 <= args.start and 0 < args.duration <= 30):
        raise ValueError("Comparison preview must be within 30 seconds")
    filtergraph = graph(looks, PRESETS, args.looks.resolve().parent)
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-n", "-i", str(args.input)]
    if args.mode == "compare":
        filtergraph += ";[0:v:0]format=yuv420p,setsar=1,scale=640:-2[before];[vout]setsar=1,scale=640:-2[after];[before][after]hstack=inputs=2[comparison]"
        video = "[comparison]"
    else:
        video = "[vout]"
    cmd += ["-filter_complex", filtergraph, "-map", video]
    if args.mode == "render":
        cmd += ["-map", "0:a?", "-c:a", "copy"]
    else:
        cmd += ["-an", "-ss", str(args.start), "-t", str(args.duration)]
    cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", str(args.output)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    run(cmd)

if __name__ == "__main__":
    main()
