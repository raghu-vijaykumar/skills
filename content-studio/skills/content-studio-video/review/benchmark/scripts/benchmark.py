#!/usr/bin/env python3
"""Build a synchronized native-resolution benchmark grid for enhancement review.

Panels are placed without cropping or downscaling. A 5-panel vlog benchmark uses
two 1080p panels in a top row and three full-width 4K panels below.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

FONT = Path("C:/Windows/Fonts/segoeui.ttf")


class BenchmarkError(RuntimeError):
    pass


def run(args: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise BenchmarkError((result.stderr or result.stdout)[-3000:])
    return result


def probe(path: Path) -> dict:
    data = json.loads(run(["ffprobe", "-v", "error", "-show_streams",
                           "-show_format", "-of", "json", str(path)]).stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise BenchmarkError(f"no video stream: {path}")
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    return {"duration": float(data.get("format", {}).get("duration") or 0),
            "width": int(video["width"]), "height": int(video["height"]),
            "has_audio": audio is not None}


def draw_label(label: str, size: int) -> str:
    escaped = label.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    font = str(FONT).replace("\\", "/").replace(":", "\\:")
    return (f"drawtext=fontfile='{font}':text='{escaped}':x=24:y=24:"
            f"fontsize={max(20, size // 36)}:fontcolor=white:"
            f"box=1:boxcolor=black@0.65:boxborderw=12")


def build(args) -> dict:
    panels = [("1  ORIGINAL", args.original),
              ("2  PREPROCESSED", args.preprocessed),
              ("3  UPSCALED 4K", args.upscaled),
              ("4  COLOR 4K", args.color)]
    if args.color_warm:
        panels.append(("5  COLOR WARM 4K", args.color_warm))
    sources = [Path(path).expanduser().resolve() for _, path in panels]
    missing = [str(path) for path in sources if not path.is_file()]
    if missing:
        raise BenchmarkError("missing panels: " + ", ".join(missing))
    infos = [probe(path) for path in sources]
    duration = min(info["duration"] for info in infos)
    if max(info["duration"] for info in infos) - duration > 0.15:
        raise BenchmarkError("panel durations differ; regenerate from the same base edit")
    width = int(args.width)
    if width % 2:
        width += 1
    half = width // 2
    top_height = half * 9 // 16
    full_height = width * 9 // 16
    if top_height % 2:
        top_height += 1
    if full_height % 2:
        full_height += 1
    audio = Path(args.audio).expanduser().resolve() if args.audio else sources[1]
    if not audio.is_file():
        raise BenchmarkError(f"audio track missing: {audio}")

    outputs = []
    for index, ((label, _), source, info) in enumerate(zip(panels, sources, infos)):
        target_size = (half, top_height) if index < 2 else (width, full_height)
        outputs.append((source, info, target_size, label))

    inputs = []
    for source, _, _, _ in outputs:
        inputs += ["-i", str(source)]
    inputs += ["-i", str(audio)]
    audio_index = len(outputs)
    graph = []
    labels = []
    for index, (_, _, size, label) in enumerate(outputs):
        out = f"p{index}"
        graph.append(f"[{index}:v]scale={size[0]}:{size[1]},setsar=1,"
                     f"{draw_label(label, size[0])}[{out}]")
        labels.append(f"[{out}]")
    top = "[top]"
    graph.append(f"{labels[0]}{labels[1]}hstack=inputs=2{top}")
    rows = [top] + labels[2:]
    graph.append("".join(rows) + f"vstack=inputs={len(rows)}[v]")
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
           *inputs, "-filter_complex", ";".join(graph), "-map", "[v]",
           "-map", f"{audio_index}:a:0", "-t", f"{duration:.3f}", "-r", "30",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", str(output)]
    run(cmd)
    produced = probe(output)
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "output": str(output),
        "duration_seconds": round(duration, 3),
        "output_size": [produced["width"], produced["height"]],
        "layout": "native-stacked",
        "panels": [{"label": label, "path": str(source), "size": list(size)}
                   for (source, _, size, label) in outputs],
        "audio": str(audio),
    }
    manifest_path = output.parent / "benchmark.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True)
    parser.add_argument("--preprocessed", required=True)
    parser.add_argument("--upscaled", required=True)
    parser.add_argument("--color", required=True)
    parser.add_argument("--color-warm")
    parser.add_argument("--audio", help="default: preprocessed panel audio")
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=3840)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = build(args)
        print(json.dumps(manifest, indent=2))
        return 0
    except (BenchmarkError, OSError, ValueError) as exc:
        print(f"benchmark: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
