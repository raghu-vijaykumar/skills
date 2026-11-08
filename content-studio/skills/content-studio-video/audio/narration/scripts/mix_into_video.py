#!/usr/bin/env python3
"""Mux approved narration into a separate edited-video master without changing its picture."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            result.update(chunk)
    return result.hexdigest()


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def mix(video: Path, narration: Path, output: Path, *, original_gain: float = 0.35,
        voice_gain: float = 1.0, replace_original: bool = False) -> dict:
    video, narration, output = video.resolve(), narration.resolve(), output.resolve()
    if not video.is_file() or not narration.is_file():
        raise ValueError("video and narration must be existing files")
    if output in (video, narration) or output.exists():
        raise ValueError("output must be a new file separate from both inputs")
    if min(original_gain, voice_gain) < 0 or max(original_gain, voice_gain) > 2:
        raise ValueError("audio gains must be between 0 and 2")
    source = probe(video)
    voice = probe(narration)
    picture = next((item for item in source.get("streams", []) if item.get("codec_type") == "video"), None)
    source_audio = next((item for item in source.get("streams", []) if item.get("codec_type") == "audio"), None)
    voice_audio = next((item for item in voice.get("streams", []) if item.get("codec_type") == "audio"), None)
    duration = float(source.get("format", {}).get("duration") or 0)
    if not picture or not voice_audio or duration <= 0:
        raise ValueError("video picture, narration audio, and positive video duration are required")
    if float(voice.get("format", {}).get("duration") or 0) > duration + 0.1:
        raise ValueError("narration extends beyond the edited video; revise timing first")
    limit = f"{duration:.6f}"
    if source_audio and not replace_original:
        graph = (f"[0:a:0]volume={original_gain},apad,atrim=0:{limit}[base];"
                 f"[1:a:0]volume={voice_gain},apad,atrim=0:{limit}[narr];"
                 "[base][narr]amix=inputs=2:duration=longest:normalize=0,"
                 "alimiter=limit=0.95[aout]")
    else:
        graph = (f"[1:a:0]volume={voice_gain},apad,atrim=0:{limit},"
                 "alimiter=limit=0.95[aout]")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="voice-mix-", dir=output.parent) as scratch:
        temporary = Path(scratch) / output.name
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                   "-i", str(video), "-i", str(narration), "-filter_complex", graph,
                   "-map", "0:v:0", "-map", "[aout]", "-map_metadata", "0",
                   "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", limit,
                   "-movflags", "+faststart", str(temporary)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout)[-1800:])
        delivered = probe(temporary)
        new_picture = next((item for item in delivered.get("streams", [])
                            if item.get("codec_type") == "video"), None)
        new_audio = next((item for item in delivered.get("streams", [])
                          if item.get("codec_type") == "audio"), None)
        if not new_picture or not new_audio or any(
                new_picture.get(key) != picture.get(key)
                for key in ("codec_name", "width", "height", "color_transfer")):
            raise RuntimeError("mixed video failed picture/audio stream validation")
        if abs(float(delivered["format"]["duration"]) - duration) > 0.2:
            raise RuntimeError("mixed video duration differs from the manual edit")
        os.replace(temporary, output)
    report = {"input_video": str(video), "input_sha256": digest(video),
              "narration": str(narration), "narration_sha256": digest(narration),
              "output": str(output), "output_sha256": digest(output),
              "duration_seconds": round(duration, 3), "picture_stream_copied": True,
              "original_gain": original_gain if source_audio and not replace_original else 0,
              "voice_gain": voice_gain, "replace_original": replace_original,
              "review_required": True}
    output.with_suffix(output.suffix + ".mix.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--narration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--original-gain", type=float, default=0.35)
    parser.add_argument("--voice-gain", type=float, default=1.0)
    parser.add_argument("--replace-original", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(mix(args.video, args.narration, args.output,
                             original_gain=args.original_gain,
                             voice_gain=args.voice_gain,
                             replace_original=args.replace_original), indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
