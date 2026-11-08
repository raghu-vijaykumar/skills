#!/usr/bin/env python3
"""Apply creator-neutral color looks to selected video ranges with FFmpeg.

Filter *choice* belongs to ``content-studio-styles``: profiles pick a look and
look ranges pick a preset or LUT. This module owns the preset catalog and filter
*application*: graph construction, HDR safety, and the FFmpeg render.
"""

from __future__ import annotations

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


def validate_ranges(ranges, presets=None):
    """Validate simple preset ranges; the caller keeps them in source time."""
    catalog = PRESETS if presets is None else presets
    if not isinstance(ranges, list) or not ranges:
        raise ValueError("ranges must be a nonempty list")
    ordered = sorted(ranges, key=lambda r: float(r["start"]))
    previous = 0
    for item in ordered:
        start, end = float(item["start"]), float(item["end"])
        if not all(math.isfinite(v) for v in (start, end)) or not 0 <= start < end or start < previous:
            raise ValueError("Ranges must be positive, non-overlapping and increasing")
        if item.get("preset") not in catalog:
            raise ValueError(f"Unknown preset: {item.get('preset')}")
        previous = end
    return ordered


def filter_chain(ranges, presets=None):
    """Build an ``eq`` chain whose ``enable`` expressions keep other footage untouched."""
    catalog = PRESETS if presets is None else presets
    parts = []
    for item in validate_ranges(ranges, catalog):
        preset = catalog[item["preset"]]
        start, end = float(item["start"]), float(item["end"])
        enable = f"between(t\\,{start:.6f}\\,{end:.6f})"
        parts.append("eq=" + ":".join([
            f"contrast={preset['contrast']}", f"brightness={preset['brightness']}",
            f"saturation={preset['saturation']}", f"gamma={preset['gamma']}",
            f"enable='{enable}'"
        ]))
    return ",".join(parts)


def ensure_sdr(source):
    """Refuse PQ/HLG or BT.2020 input instead of silently treating HDR as SDR."""
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe is required for HDR safety check")
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                             "-show_entries", "stream=color_transfer,color_primaries",
                             "-of", "json", str(source)], capture_output=True, text=True, check=True)
    streams = json.loads(result.stdout).get("streams", [])
    if not streams:
        raise ValueError("No video stream found")
    stream = streams[0]
    if stream.get("color_transfer") in ("smpte2084", "arib-std-b67") or stream.get("color_primaries") == "bt2020":
        raise ValueError("HDR/HLG source unsupported: tone-map to SDR first")


def validate_looks(looks, presets=None, root=None):
    """Validate editable look ranges and resolve LUT paths against ``root``."""
    catalog = PRESETS if presets is None else presets
    ordered = sorted(looks, key=lambda x: float(x["start"]))
    last = 0.0
    for look in ordered:
        start, end = float(look["start"]), float(look["end"])
        fade = float(look.get("fade", 0.35))
        if not all(math.isfinite(v) for v in (start, end, fade)) or start < last or end <= start or fade < 0 or fade * 2 > end - start:
            raise ValueError("Invalid, overlapping, or too-short look range")
        if bool(look.get("preset")) == bool(look.get("lut")):
            raise ValueError("Exactly one of preset or lut required")
        if look.get("preset") and look["preset"] not in catalog:
            raise ValueError("Unknown preset")
        if look.get("lut"):
            path = Path(look["lut"])
            if root and not path.is_absolute():
                path = Path(root) / path
            path = path.resolve()
            if path.suffix.lower() != ".cube" or not path.is_file():
                raise ValueError("LUT must reference an existing .cube file")
            look["_lut_path"] = str(path)
        last = end
    return ordered


def look_graph(looks, presets=None, root=None):
    """Build a split/blend graph so each look fades in and out without touching other frames."""
    catalog = PRESETS if presets is None else presets
    ordered = validate_looks([dict(x) for x in looks], catalog, root)
    parts = ["[0:v:0]format=yuv444p[v0]"]
    current = "v0"
    for index, look in enumerate(ordered):
        source, graded, output = f"base{index}", f"grade{index}", f"v{index+1}"
        parts.append(f"[{current}]split=2[{source}][input{index}]")
        if "preset" in look:
            preset = catalog[look["preset"]]
            grade = "eq=" + ":".join(f"{key}={preset[key]}" for key in ("contrast", "brightness", "saturation", "gamma"))
        else:
            path = look["_lut_path"].replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
            grade = f"lut3d=file='{path}'"
        parts.append(f"[input{index}]{grade}[{graded}]")
        start, end, fade = float(look["start"]), float(look["end"]), float(look.get("fade", 0.35))
        if fade == 0:
            alpha = f"between(T,{start},{end})"
        else:
            # FFmpeg expressions only accept two-argument min(); nest instead of min(1,a,b).
            alpha = f"max(0,min(min(1,(T-{start})/{fade}),({end}-T)/{fade}))"
        # blend expression uses T (frame timestamp) and pixel A/B.
        parts.append(f"[{source}][{graded}]blend=all_expr='A*(1-({alpha}))+B*({alpha})'[{output}]")
        current = output
    parts.append(f"[{current}]format=yuv420p[vout]")
    return ";".join(parts)


def _check_render_paths(source, target, ffmpeg):
    if not source.is_file() or source == target:
        raise ValueError("Input must exist and output must be a different file")
    if not shutil.which(ffmpeg):
        raise RuntimeError("FFmpeg not found")


def render_ranges(input_path, output_path, ranges, presets=None, ffmpeg="ffmpeg",
                  crf=18, preset="medium", preview=None):
    """Render selected preset ranges; audio is stream-copied when MP4-compatible."""
    source, target = Path(input_path).resolve(), Path(output_path).resolve()
    _check_render_paths(source, target, ffmpeg)
    ensure_sdr(source)
    if not 0 <= crf <= 51:
        raise ValueError("CRF must be 0..51")
    if preview is not None and (preview[0] < 0 or not 0 < preview[1] <= 30):
        raise ValueError("Preview must be at most 30 seconds")
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-hide_banner", "-nostdin", "-n", "-i", str(source),
               "-map", "0:v:0", "-map", "0:a?", "-vf", filter_chain(ranges, presets),
               "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
               "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(target)]
    if preview is not None:
        command[command.index("-map"):command.index("-map")] = ["-ss", str(preview[0]), "-t", str(preview[1])]
    subprocess.run(command, check=True)
    return target


def render_looks(input_path, output_path, looks, presets=None, root=None, ffmpeg="ffmpeg",
                 crf=18, preset="medium"):
    """Render feathered preset or LUT looks to a new SDR master."""
    source, target = Path(input_path).resolve(), Path(output_path).resolve()
    _check_render_paths(source, target, ffmpeg)
    ensure_sdr(source)
    if not 0 <= crf <= 51:
        raise ValueError("CRF must be 0..51")
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-hide_banner", "-nostdin", "-n", "-i", str(source),
               "-filter_complex", look_graph(looks, presets, root),
               "-map", "[vout]", "-map", "0:a?", "-c:a", "copy",
               "-c:v", "libx264", "-crf", str(crf), "-preset", preset,
               "-pix_fmt", "yuv420p", str(target)]
    subprocess.run(command, check=True)
    return target


def compare_looks(input_path, output_path, looks, presets=None, root=None, start=0,
                  duration=5, ffmpeg="ffmpeg"):
    """Render a short side-by-side original-versus-graded review clip."""
    source, target = Path(input_path).resolve(), Path(output_path).resolve()
    _check_render_paths(source, target, ffmpeg)
    if not (0 <= start and 0 < duration <= 30):
        raise ValueError("Comparison preview must be within 30 seconds")
    ensure_sdr(source)
    graph = look_graph(looks, presets, root)
    graph += (";[0:v:0]format=yuv420p,setsar=1,scale=640:-2[before];"
              "[vout]setsar=1,scale=640:-2[after];[before][after]hstack=inputs=2[comparison]")
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-hide_banner", "-nostdin", "-n", "-i", str(source),
               "-filter_complex", graph, "-map", "[comparison]", "-an",
               "-ss", str(start), "-t", str(duration),
               "-c:v", "libx264", "-crf", "18", "-preset", "medium",
               "-pix_fmt", "yuv420p", str(target)]
    subprocess.run(command, check=True)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="show the built-in look presets")
    p = sub.add_parser("render", help="apply preset ranges to an SDR video")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--ranges", required=True, help="JSON file containing a ranges array")
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--ffmpeg", default="ffmpeg")
    p.add_argument("--preview-start", type=float)
    p.add_argument("--preview-duration", type=float, default=5)
    p = sub.add_parser("looks", help="apply feathered preset or LUT looks")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--looks", required=True, help="JSON file containing a ranges array")
    p.add_argument("--crf", type=int, default=18)
    p = sub.add_parser("compare", help="render a side-by-side review clip")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--looks", required=True)
    p.add_argument("--start", type=float, default=0)
    p.add_argument("--duration", type=float, default=5)
    args = parser.parse_args(argv)
    if args.command == "list":
        print(json.dumps(PRESETS, indent=2))
        return 0
    if args.command == "render":
        data = json.loads(Path(args.ranges).read_text(encoding="utf-8-sig"))
        preview = (args.preview_start, args.preview_duration) if args.preview_start is not None else None
        render_ranges(args.input, args.output, data["ranges"], ffmpeg=args.ffmpeg,
                      crf=args.crf, preview=preview)
        return 0
    data = json.loads(Path(args.looks).read_text(encoding="utf-8-sig"))
    looks = data["ranges"] if isinstance(data, dict) else data
    root = Path(args.looks).resolve().parent
    if args.command == "looks":
        render_looks(args.input, args.output, looks, root=root, crf=args.crf)
    else:
        compare_looks(args.input, args.output, looks, root=root, start=args.start,
                      duration=args.duration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
