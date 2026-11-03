#!/usr/bin/env python3
"""Local video upscaling via Real-ESRGAN ncnn/Vulkan or FFmpeg Lanczos.

Upscaling reconstructs resolution. It is not color correction and cannot
reliably recover motion blur or missed focus. The original is never modified.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".m4v", ".webm", ".avi"}


class UpscaleError(RuntimeError):
    pass


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise UpscaleError((result.stderr or result.stdout)[-3000:])
    return result


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def probe(path: Path) -> dict:
    data = json.loads(run(["ffprobe", "-v", "error", "-show_streams",
                           "-show_format", "-of", "json", str(path)]).stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise UpscaleError(f"no video stream: {path}")
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    rotation = 0
    for side in video.get("side_data_list", []):
        if "rotation" in side:
            rotation = int(side["rotation"])
    width, height = int(video["width"]), int(video["height"])
    if abs(rotation) % 180 == 90:
        width, height = height, width
    return {
        "duration": float(data.get("format", {}).get("duration") or 0),
        "width": width,
        "height": height,
        "fps": video.get("avg_frame_rate") or video.get("r_frame_rate") or "30/1",
        "has_audio": audio is not None,
    }


def preferred_backend(explicit: str | None, executable: str | None) -> tuple[str, Path | None]:
    if explicit == "lanczos":
        return "lanczos", None
    candidates = [executable, os.environ.get("REALESRGAN_NCNN"),
                  shutil.which("realesrgan-ncnn-vulkan"),
                  str(Path(__file__).resolve().parents[4] / "tmp" / "realesrgan" /
                      "realesrgan-ncnn-vulkan.exe")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return "realesrgan", Path(candidate)
    if explicit == "realesrgan":
        raise UpscaleError("realesrgan-ncnn-vulkan executable not found")
    return "lanczos", None


def frame_count(folder: Path) -> int:
    return len(list(folder.glob("*.png"))) + len(list(folder.glob("*.jpg")))


def extract_frames(source: Path, folder: Path, start: float, duration: float) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error"]
    if start > 0:
        cmd += ["-ss", f"{start:.3f}"]
    if duration > 0:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-i", str(source), "-fps_mode", "passthrough", "-map", "0:v:0",
            str(folder / "%06d.png")]
    run(cmd)


def run_lanczos(source: Path, output: Path, size: tuple[int, int],
                start: float, duration: float, has_audio: bool,
                fps: str) -> None:
    width, height = size
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error"]
    if start > 0:
        cmd += ["-ss", f"{start:.3f}"]
    if duration > 0:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-i", str(source), "-vf",
            f"scale={width}:{height}:flags=lanczos,unsharp=5:5:0.35:5:5:0.0",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", fps]
    if has_audio:
        cmd += ["-map", "0:v:0", "-map", "0:a:0", "-c:a", "copy"]
    else:
        cmd += ["-an"]
    cmd += ["-movflags", "+faststart", str(output)]
    run(cmd)


def run_realesrgan(executable: Path, frames: Path, upscaled: Path,
                   model: str, scale: int, tile: int) -> None:
    upscaled.mkdir(parents=True, exist_ok=True)
    run([str(executable), "-i", str(frames), "-o", str(upscaled),
         "-n", model, "-s", str(scale), "-t", str(tile)])


def reassemble(upscaled: Path, source: Path, output: Path,
               start: float, duration: float, fps: str, has_audio: bool) -> None:
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
           "-framerate", fps, "-i", str(upscaled / "%06d.png")]
    if start > 0:
        cmd += ["-ss", f"{start:.3f}"]
    if duration > 0:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-i", str(source)]
    if has_audio:
        cmd += ["-map", "0:v:0", "-map", "1:a:0", "-c:a", "copy"]
    else:
        cmd += ["-map", "0:v:0", "-an"]
    cmd += ["-c:v", "libx265", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-tag:v", "hvc1", "-shortest",
            "-movflags", "+faststart", str(output)]
    run(cmd)


def compare_frame(source: Path, output: Path, source_at: float, output_at: float,
                  target: Path) -> None:
    def grab(path: Path, at: float) -> np.ndarray:
        result = subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{at:.3f}",
             "-i", str(path), "-frames:v", "1", "-vf", "scale=960:540",
             "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if result.returncode or not result.stdout:
            raise UpscaleError(f"cannot sample {path}")
        return np.asarray(Image.open(__import__("io").BytesIO(result.stdout)).convert("RGB"))

    before = grab(source, source_at)
    after = grab(output, output_at)
    canvas = Image.new("RGB", (before.shape[1] * 2, before.shape[0]), "white")
    canvas.paste(Image.fromarray(before), (0, 0))
    canvas.paste(Image.fromarray(after), (before.shape[1], 0))
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, quality=90)


def upscale(args) -> dict:
    source = Path(args.input).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in VIDEO_EXTENSIONS:
        raise UpscaleError(f"input must be a supported video: {source}")
    info = probe(source)
    if info["duration"] <= 0:
        raise UpscaleError("input has no duration")
    start = float(args.start or 0)
    duration = float(args.duration or max(0.0, info["duration"] - start))
    if start < 0 or duration <= 0 or start + duration > info["duration"] + 0.1:
        raise UpscaleError("start/duration outside the source")
    scale = max(1, int(args.scale))
    width = int(info["width"]) * scale
    height = int(info["height"]) * scale
    if width % 2:
        width += 1
    if height % 2:
        height += 1
    output = Path(args.output).expanduser().resolve()
    if output.resolve() == source.resolve():
        raise UpscaleError("output must differ from the source")
    output.parent.mkdir(parents=True, exist_ok=True)
    work = Path(args.work).expanduser().resolve() if args.work else (
        output.parent / ".content-studio" / "upscale" / source.stem)
    frames = work / "frames"
    upscaled = work / "upscaled"
    if args.force:
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    backend, executable = preferred_backend(args.backend, args.realesrgan)
    started = time.perf_counter()
    if backend == "realesrgan":
        extract_frames(source, frames, start, duration)
        before = frame_count(frames)
        if not before:
            raise UpscaleError("no frames extracted")
        run_realesrgan(executable, frames, upscaled, args.model, scale, args.tile)
        after = frame_count(upscaled)
        if after != before:
            raise UpscaleError(f"upscaler produced {after} frames; expected {before}")
        reassemble(upscaled, source, output, start, duration, info["fps"],
                   info["has_audio"])
    else:
        run_lanczos(source, output, (width, height), start, duration,
                    info["has_audio"], info["fps"])
    elapsed = time.perf_counter() - started
    produced = probe(output)
    manifest = {
        "schema_version": 1,
        "generated_at": now(),
        "source": str(source),
        "output": str(output),
        "backend": backend,
        "model": args.model if backend == "realesrgan" else None,
        "scale": scale,
        "tile": args.tile if backend == "realesrgan" else None,
        "source_size": [info["width"], info["height"]],
        "output_size": [produced["width"], produced["height"]],
        "start_seconds": round(start, 3),
        "duration_seconds": round(duration, 3),
        "runtime_seconds": round(elapsed, 2),
        "source_bytes": source.stat().st_size,
        "output_bytes": output.stat().st_size,
        "note": "upscaling does not correct color, exposure, or motion blur",
    }
    manifest_path = work / "upscale.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    try:
        offset = min(2.0, duration / 2)
        compare_frame(source, output, start + offset, offset,
                      work / "before-after.jpg")
    except UpscaleError:
        pass
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scale", type=int, choices=[2, 3, 4], default=2,
                        help="upscale factor; 2 turns 1080p into 4K")
    parser.add_argument("--backend", choices=["realesrgan", "lanczos"],
                        help="default: realesrgan when installed, otherwise lanczos")
    parser.add_argument("--realesrgan", help="path to realesrgan-ncnn-vulkan executable")
    parser.add_argument("--model", default="realesr-animevideov3",
                        help="realesrgan model name")
    parser.add_argument("--tile", type=int, default=256,
                        help="realesrgan tile size; lower for limited VRAM")
    parser.add_argument("--start", type=float, help="start second for a test excerpt")
    parser.add_argument("--duration", type=float, help="duration for a test excerpt")
    parser.add_argument("--work", type=Path, help="intermediate frame folder")
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = upscale(args)
        print(json.dumps(manifest, indent=2))
        return 0
    except (UpscaleError, OSError, ValueError) as exc:
        print(f"upscale: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
