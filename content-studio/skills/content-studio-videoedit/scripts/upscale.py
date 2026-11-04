#!/usr/bin/env python3
"""Diagnosis-first video upscaling via Real-ESRGAN or FFmpeg Lanczos.

Upscaling reconstructs resolution. It is not color correction and cannot
reliably recover motion blur or missed focus. The original is never modified.

The draft batch treats AI upscaling as a proposed enhancement: a clip is
analyzed, an 8-second candidate is rendered with both Lanczos and the selected
model, and only a measurable, temporally stable improvement replaces the clip.
The single-clip command keeps its explicit contract and renders what it is told.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".m4v", ".webm", ".avi"}
SCHEMA_VERSION = 2
ANALYSIS_VERSION = "1"
DEFAULT_MODEL = {"realesrgan": "realesrgan-x4plus",
                 "pytorch": "realesr-general-x4v3"}
MODEL_NOTES = {
    "realesr-animevideov3": "animation-only model; never auto-selected for live "
                            "footage, keep it behind an explicit --model",
    "realesrgan-x4plus": "general photo model; measured 22-27 s/frame at 1080p on "
                         "ncnn/Vulkan because it computes 4x internally",
    "realesr-general-x4v3": "lightweight general model with denoise strength; "
                            "requires the PyTorch backend and verified weights",
    "RealESRGAN_x2plus": "native 2x RRDB model; sharper and heavier than the "
                         "compact general model",
    "RealESRGAN_x4plus": "native 4x RRDB model; the heaviest benchmark option",
    "RealESRNet_x4plus": "MSE-trained RRDB baseline; smoother, fewer invented edges",
}
NCNN_MODELS = {"realesrgan-x4plus", "realesrgan-x4plus-anime",
               "realesr-animevideov3", "realesrnet-x4plus"}
PYTORCH_MODELS = {"realesr-general-x4v3", "RealESRGAN_x2plus",
                  "RealESRGAN_x4plus", "RealESRNet_x4plus"}
HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}
TILE_MIN = 32
WEIGHTS_DIR = Path(__file__).resolve().parents[4] / "tmp" / "realesrgan" / "weights"
WEIGHT_FILES = {
    "realesr-general-x4v3": "realesr-general-x4v3.pth",
    "realesr-general-wdn-x4v3": "realesr-general-wdn-x4v3.pth",
    "RealESRGAN_x2plus": "RealESRGAN_x2plus.pth",
    "RealESRGAN_x4plus": "RealESRGAN_x4plus.pth",
    "RealESRNet_x4plus": "RealESRNet_x4plus.pth",
}


def bundled_weights(model: str | None) -> Path | None:
    """A verified checkpoint under the local (gitignored) weights directory."""
    name = WEIGHT_FILES.get(model or "")
    if not name:
        return None
    path = WEIGHTS_DIR / name
    return path if path.is_file() else None


def cuda_available() -> bool:
    try:
        import torch
    except ImportError:
        return False
    return bool(torch.cuda.is_available())


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


def fps_value(fps: str | None) -> float:
    try:
        if fps and "/" in fps:
            numerator, denominator = fps.split("/", 1)
            value = float(numerator) / float(denominator or 1)
        else:
            value = float(fps or 30)
    except (TypeError, ValueError, ZeroDivisionError):
        return 30.0
    return value if 1.0 <= value <= 240.0 else 30.0


def probe(path: Path) -> dict:
    data = json.loads(run(["ffprobe", "-v", "error", "-show_streams",
                           "-show_format", "-of", "json", str(path)]).stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise UpscaleError(f"no video stream: {path}")
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    rotation = 0
    sides = video.get("side_data_list") or []
    for side in sides:
        if "rotation" in side:
            rotation = int(side["rotation"])
    width, height = int(video["width"]), int(video["height"])
    if abs(rotation) % 180 == 90:
        width, height = height, width
    return {
        "duration": float(data.get("format", {}).get("duration") or 0),
        "width": width,
        "height": height,
        "rotation": rotation,
        "fps": video.get("avg_frame_rate") or video.get("r_frame_rate") or "30/1",
        "r_fps": video.get("r_frame_rate") or "30/1",
        "pix_fmt": video.get("pix_fmt") or "yuv420p",
        "color_primaries": video.get("color_primaries"),
        "color_transfer": video.get("color_transfer"),
        "color_space": video.get("color_space"),
        "color_range": video.get("color_range"),
        "dolby_vision": any("DOVI" in str(side.get("side_data_type", ""))
                            for side in sides),
        "has_audio": audio is not None,
    }


def is_hdr(info: dict) -> bool:
    return bool(info.get("dolby_vision")) or info.get("color_transfer") in HDR_TRANSFERS


def pytorch_available() -> bool:
    return importlib.util.find_spec("torch") is not None


def preferred_backend(explicit: str | None, executable: str | None) -> tuple[str, Path | None]:
    if explicit == "lanczos":
        return "lanczos", None
    if explicit == "pytorch":
        if not pytorch_available():
            raise UpscaleError(
                "PyTorch Real-ESRGAN is not installed; install torch, realesrgan, "
                "and basicsr, or use --backend realesrgan for the ncnn/Vulkan build")
        return "pytorch", None
    if explicit is None and pytorch_available() and cuda_available() \
            and bundled_weights("realesr-general-x4v3"):
        # The measured best default on a CUDA machine with verified weights:
        # +25.7% detail vs +14.1% for the ncnn video model on the sample clip.
        return "pytorch", None
    candidates = [executable, os.environ.get("REALESRGAN_NCNN"),
                  shutil.which("realesrgan-ncnn-vulkan"),
                  str(Path(__file__).resolve().parents[4] / "tmp" / "realesrgan" /
                      "realesrgan-ncnn-vulkan.exe")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return "realesrgan", Path(candidate)
    if explicit == "realesrgan":
        raise UpscaleError("realesrgan-ncnn-vulkan executable not found")
    if pytorch_available():
        return "pytorch", None
    return "lanczos", None


def resolve_model(backend: str, model: str | None, executable: Path | None) -> str | None:
    if backend == "lanczos":
        return None
    if backend == "pytorch":
        name = model or DEFAULT_MODEL["pytorch"]
        if name not in PYTORCH_MODELS:
            raise UpscaleError(f"pytorch model must be one of {sorted(PYTORCH_MODELS)}")
        return name
    name = model or DEFAULT_MODEL["realesrgan"]
    if name not in NCNN_MODELS:
        raise UpscaleError(f"ncnn model must be one of {sorted(NCNN_MODELS)}; "
                           "realesr-general-x4v3 needs --backend pytorch")
    if executable:
        models = executable.parent / "models"
        if models.is_dir():
            candidates = [models / f"{name}.param"] + [
                models / f"{name}-x{scale}.param" for scale in (2, 3, 4)]
            if not any(candidate.is_file() for candidate in candidates):
                raise UpscaleError(f"model {name} is not in {models}")
    return name


def frame_count(folder: Path) -> int:
    return len(list(folder.glob("*.png"))) + len(list(folder.glob("*.jpg")))


def frame_timestamps(source: Path, start: float, duration: float) -> list[float]:
    """Timestamps of the frames inside the requested range, in source seconds."""
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "frame=best_effort_timestamp_time", "-of", "csv=p=0"]
    if duration > 0:
        cmd += ["-read_intervals", f"{max(0.0, start):.6f}%+{duration:.6f}"]
    cmd.append(str(source))
    output = run(cmd).stdout
    stamps = []
    for line in output.splitlines():
        value = line.strip().split(",")[0]
        if not value or value == "N/A":
            continue
        try:
            stamp = float(value)
        except ValueError:
            continue
        if stamp + 0.001 >= start and (duration <= 0 or stamp <= start + duration + 0.001):
            stamps.append(round(stamp, 6))
    return stamps


def frame_deltas(timestamps: list[float], fps: float,
                 tail: float | None = None) -> list[float]:
    fallback = 1.0 / max(fps, 1.0)
    deltas = [round(timestamps[index + 1] - timestamps[index], 6)
              for index in range(len(timestamps) - 1)]
    deltas = [value if value > 0.001 else fallback for value in deltas]
    if tail is not None:
        deltas.append(max(0.001, tail))
    else:
        deltas.append(deltas[-1] if deltas else fallback)
    return deltas


def write_concat(frames: list[Path], deltas: list[float], target: Path) -> None:
    lines = []
    for frame, delta in zip(frames, deltas):
        escaped = str(frame).replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
        lines.append(f"duration {delta:.6f}")
    if frames:
        escaped = str(frames[-1]).replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract_frames(source: Path, folder: Path, start: float, duration: float) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(source)]
    if start > 0:
        cmd += ["-ss", f"{start:.6f}"]
    if duration > 0:
        cmd += ["-t", f"{duration:.6f}"]
    cmd += ["-fps_mode", "passthrough", "-map", "0:v:0", str(folder / "%06d.png")]
    run(cmd)


def color_args(info: dict) -> list[str]:
    args = []
    for flag, key in (("-color_primaries", "color_primaries"),
                      ("-color_trc", "color_transfer"),
                      ("-colorspace", "color_space"),
                      ("-color_range", "color_range")):
        value = info.get(key)
        if value and value not in {"unknown", "unspecified", "reserved"}:
            args += [flag, value]
    return args


def encode_args(info: dict, preset: str = "medium",
                encoder: str = "auto") -> list[str]:
    ten_bit = "10" in str(info.get("pix_fmt") or "")
    pixel_format = "yuv420p10le" if ten_bit else "yuv420p"
    choice = encoder or "auto"
    if choice == "auto":
        choice = "nvenc" if encoder_available("hevc_nvenc") else "libx265"
    if choice == "nvenc":
        nvenc_format = "p010le" if ten_bit else "yuv420p"
        return (["-c:v", "hevc_nvenc", "-preset", "p5", "-rc", "vbr",
                 "-cq", "19", "-pix_fmt", nvenc_format, "-tag:v", "hvc1"]
                + color_args(info))
    return (["-c:v", "libx265", "-preset", preset, "-crf", "18",
             "-pix_fmt", pixel_format, "-tag:v", "hvc1"] + color_args(info))


_ENCODER_CACHE: dict[str, bool] = {}


def encoder_available(name: str) -> bool:
    if name not in _ENCODER_CACHE:
        try:
            output = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                                    capture_output=True, text=True,
                                    encoding="utf-8", errors="replace").stdout
        except OSError:
            output = ""
        _ENCODER_CACHE[name] = name in output
    return _ENCODER_CACHE[name]


def run_lanczos(source: Path, output: Path, size: tuple[int, int],
                start: float, duration: float, has_audio: bool,
                fps: str, info: dict | None = None, preset: str = "medium",
                encoder: str = "auto") -> None:
    width, height = size
    info = info or probe(source)
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error"]
    if start > 0:
        cmd += ["-ss", f"{start:.3f}"]
    if duration > 0:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-i", str(source), "-vf",
            f"scale={width}:{height}:flags=lanczos,unsharp=5:5:0.35:5:5:0.0",
            "-fps_mode", "vfr"] + encode_args(info, preset, encoder)
    if has_audio:
        cmd += ["-map", "0:v:0", "-map", "0:a:0", "-c:a", "copy"]
    else:
        cmd += ["-an"]
    cmd += ["-movflags", "+faststart", str(output)]
    run(cmd)


def run_realesrgan(executable: Path, frames: Path, upscaled: Path,
                   model: str, scale: int, tile: int,
                   staging: str = "jpeg") -> None:
    upscaled.mkdir(parents=True, exist_ok=True)
    fmt = "jpg" if staging == "jpeg" else "png"
    cmd = [str(executable), "-i", str(frames), "-o", str(upscaled),
           "-n", model, "-s", str(scale), "-t", str(max(TILE_MIN, tile)),
           "-f", fmt]
    models = executable.parent / "models"
    if models.is_dir():
        cmd += ["-m", str(models)]
    run(cmd)


def run_realesrgan_pytorch(frames: Path, upscaled: Path, model: str, scale: int,
                           tile: int, denoise_strength: float | None,
                           weights: str | None, weights2: str | None = None,
                           staging: str = "jpeg") -> dict:
    """Opt-in PyTorch adapter; weights are explicit, never downloaded silently."""
    if not weights:
        raise UpscaleError("the PyTorch backend needs --weights to a verified "
                           "checkpoint; automatic downloads are intentionally disabled")
    try:
        import torch
        import realesrgan_torch
    except ImportError as exc:  # pragma: no cover - depends on optional torch
        raise UpscaleError("PyTorch backend requires torch; install a CUDA build "
                           "from https://pytorch.org") from exc
    net, device = realesrgan_torch.load_model(model, weights, weights2,
                                              denoise_strength)
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    upscaled.mkdir(parents=True, exist_ok=True)
    peak = 0.0
    for path in sorted(frames.glob("*.png")):
        image = Image.open(path).convert("RGB")
        tensor = (torch.from_numpy(np.asarray(image, dtype=np.float32) / 255.0)
                  .permute(2, 0, 1).unsqueeze(0))
        output, used = realesrgan_torch.enhance(net, device, tensor, outscale=scale,
                                                tile=tile, tile_pad=10)
        peak = max(peak, used)
        array = output.squeeze(0).permute(1, 2, 0).float().cpu().numpy() * 255.0
        image = Image.fromarray(np.clip(array, 0, 255).round().astype(np.uint8))
        if staging == "jpeg":
            image.save(upscaled / f"{path.stem}.jpg", format="JPEG",
                       quality=95, subsampling=0)
        else:
            image.save(upscaled / f"{path.stem}.png", format="PNG",
                       compress_level=1)
    if device == "cuda":
        peak = max(peak, torch.cuda.max_memory_allocated() / (1024 ** 2))
    return {"device": device, "peak_vram_mb": round(peak, 1) if peak else None}


def encode_chunk(upscaled: Path, concat: Path, output: Path,
                 size: tuple[int, int] | None, info: dict,
                 preset: str = "medium", encoder: str = "auto") -> None:
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", str(concat)]
    if size:
        cmd += ["-vf", f"scale={size[0]}:{size[1]}:flags=lanczos"]
    cmd += ["-an"] + encode_args(info, preset, encoder) + [str(output)]
    run(cmd)


def concat_videos(chunks: list[Path], output: Path, work: Path) -> None:
    listing = work / "chunks.txt"
    listing.write_text("\n".join(
        f"file '{str(chunk).replace(chr(39), chr(92) + chr(39))}'" for chunk in chunks
    ) + "\n", encoding="utf-8")
    run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(output)])


def mux_audio(video: Path, source: Path, output: Path, start: float,
              duration: float, info: dict) -> None:
    full = start <= 0.001 and duration >= info["duration"] - 0.05
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(video)]
    if not full:
        # Trim only the audio input; the video track is already exact.
        cmd += ["-ss", f"{start:.6f}", "-t", f"{duration:.6f}"]
    cmd += ["-i", str(source), "-map", "0:v:0", "-map", "1:a:0?"]
    if full:
        cmd += ["-c", "copy"]
    else:
        cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "256k"]
    cmd += ["-shortest", "-movflags", "+faststart", str(output)]
    run(cmd)


def plan_chunks(total: int, chunk: int) -> list[tuple[int, int]]:
    if total <= 0:
        return [(0, 0)]
    if chunk <= 0 or chunk >= total:
        return [(0, total)]
    return [(start, min(start + chunk, total)) for start in range(0, total, chunk)]


def render_ai(source: Path, video: Path, work: Path, backend: str,
              executable: Path | None, model: str, scale: int, tile: int,
              start: float, duration: float, info: dict, chunk: int = 0,
              denoise_strength: float | None = None,
              weights: str | None = None, weights2: str | None = None,
              preset: str = "medium", staging: str = "jpeg",
              encoder: str = "auto") -> dict:
    """Render an upscaled video track with source timestamps preserved."""
    fps = fps_value(info.get("fps"))
    timestamps = frame_timestamps(source, start, duration)
    if len(timestamps) < 2:
        timestamps = []
    total = len(timestamps) if timestamps else max(1, round(duration * fps))
    chunks = plan_chunks(total, chunk)
    work.mkdir(parents=True, exist_ok=True)
    videos: list[Path] = []
    rendered = 0
    timing_fallback = False
    device = None
    peak_vram = None
    for index, (first, last) in enumerate(chunks):
        if timestamps:
            segment_start = start if first == 0 else timestamps[first]
            segment_end = (timestamps[last] if last < len(timestamps)
                           else min(start + duration, info["duration"]))
        else:
            segment_start = start + first / max(fps, 1.0)
            segment_end = min(start + duration,
                              start + last / max(fps, 1.0))
        window = max(0.02, segment_end - segment_start)
        frames = work / f"frames-{index:03d}"
        upscaled = work / f"upscaled-{index:03d}"
        shutil.rmtree(frames, ignore_errors=True)
        shutil.rmtree(upscaled, ignore_errors=True)
        extract_frames(source, frames, segment_start, window)
        count = frame_count(frames)
        if not count:
            raise UpscaleError("no frames extracted")
        if backend == "realesrgan":
            run_realesrgan(executable, frames, upscaled, model, scale, tile,
                           staging)
        else:
            stats = run_realesrgan_pytorch(frames, upscaled, model, scale, tile,
                                           denoise_strength, weights, weights2,
                                           staging)
            device = stats["device"]
            if stats.get("peak_vram_mb"):
                peak_vram = max(peak_vram or 0.0, stats["peak_vram_mb"])
        produced = frame_count(upscaled)
        if produced != count:
            raise UpscaleError(f"upscaler produced {produced} frames; expected {count}")
        if timestamps and len(chunks) > 1 and count != last - first:
            raise UpscaleError("chunk frame boundaries drifted; rerun without --chunk")
        deltas = None
        if timestamps and count == last - first:
            tail = max(0.001, min(1.0, segment_end - timestamps[first + count - 1]))
            deltas = frame_deltas(timestamps[first:first + count], fps, tail=tail)
            if abs(sum(deltas) - window) > 0.08:
                deltas = None
        if deltas is None:
            # Duration/count keeps audio sync even when the probe and decoder
            # disagree about a variable-frame-rate segment.
            deltas = [window / count] * count
            timing_fallback = True
        listing = work / f"chunk-{index:03d}.txt"
        write_concat(sorted(path for path in upscaled.iterdir() if path.is_file()),
                    deltas, listing)
        chunk_video = work / f"chunk-{index:03d}.mp4"
        encode_chunk(upscaled, listing, chunk_video, None, info, preset, encoder)
        rendered += count
        videos.append(chunk_video)
        print(f"upscale: {source.name} chunk {index + 1}/{len(chunks)} "
              f"({rendered}/{total} frames)", file=sys.stderr, flush=True)
        shutil.rmtree(frames, ignore_errors=True)
        shutil.rmtree(upscaled, ignore_errors=True)
    if len(videos) == 1:
        os.replace(videos[0], video)
    else:
        concat_videos(videos, video, work)
    return {"frames": rendered, "chunks": len(videos),
            "timing": "uniform_fallback" if timing_fallback
                      else ("vfr" if timestamps else "uniform"),
            "device": device, "peak_vram_mb": peak_vram}


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


def parse_target(value: str | None) -> tuple[int, int] | None:
    if not value:
        return None
    text = str(value).strip().lower()
    presets = {"4k": (3840, 2160), "2160p": (3840, 2160),
               "1080p": (1920, 1080), "1440p": (2560, 1440),
               "720p": (1280, 720)}
    if text in presets:
        return presets[text]
    match = re.fullmatch(r"(\d+)x(\d+)", text)
    if not match:
        raise UpscaleError("target must be 4k, 2160p, 1080p, or WxH")
    width, height = int(match.group(1)), int(match.group(2))
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise UpscaleError("target must be positive even dimensions")
    return width, height


def source_hash(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checkpoint_info(weights: str | None, partner: str | None = None) -> dict | None:
    """Record the checkpoint files and hashes used by the PyTorch backend."""
    if not weights:
        return None
    path = Path(weights)
    info = {"path": path.name, "sha256": source_hash(path) if path.is_file() else None}
    if partner:
        other = Path(partner)
        info["denoise_path"] = other.name
        info["denoise_sha256"] = source_hash(other) if other.is_file() else None
    return info


def cache_params(source: Path, backend: str, model: str | None, scale: int,
                 tile: int, target: tuple[int, int], start: float, duration: float,
                 denoise_strength: float | None) -> dict:
    return {
        "analysis_version": ANALYSIS_VERSION,
        "source_hash": source_hash(source),
        "backend": backend,
        "model": model,
        "scale": scale,
        "tile": tile if backend != "lanczos" else None,
        "target": list(target),
        "start_seconds": round(start, 3),
        "duration_seconds": round(duration, 3),
        "denoise_strength": denoise_strength,
    }


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
    target = parse_target(getattr(args, "target", None))
    if target:
        width, height = target
    else:
        width = int(info["width"]) * scale
        height = int(info["height"]) * scale
        if width % 2:
            width += 1
        if height % 2:
            height += 1
        target = (width, height)
    output = Path(args.output).expanduser().resolve()
    if output.resolve() == source.resolve():
        raise UpscaleError("output must differ from the source")
    output.parent.mkdir(parents=True, exist_ok=True)
    backend, executable = preferred_backend(args.backend, args.realesrgan)
    model = resolve_model(backend, args.model, executable)
    weights = getattr(args, "weights", None)
    weights2 = getattr(args, "weights2", None)
    denoise_strength = getattr(args, "denoise_strength", None)
    if backend == "pytorch":
        weights = weights or bundled_weights(model)
        if not weights:
            raise UpscaleError(
                "the PyTorch backend needs --weights to a verified checkpoint; "
                "automatic downloads are intentionally disabled")
        if model == "realesr-general-x4v3":
            weights2 = weights2 or bundled_weights("realesr-general-wdn-x4v3")
            if denoise_strength is None:
                denoise_strength = 0.5
    if is_hdr(info) and not getattr(args, "allow_hdr", False):
        raise UpscaleError("HDR/Dolby Vision source: pass --allow-hdr after deciding "
                           "how to tone-map, otherwise the frame pipeline would "
                           "silently change the color space")
    work = Path(args.work).expanduser().resolve() if args.work else (
        output.parent / ".content-studio" / "upscale" / source.stem)
    staging = getattr(args, "staging", "jpeg")
    encoder = getattr(args, "encoder", "auto")
    if args.force:
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    params = cache_params(source, backend, model, scale, args.tile, target,
                          start, duration, denoise_strength)
    params["staging"] = staging
    params["encoder"] = encoder
    manifest_path = work / "upscale.json"
    if not getattr(args, "force", False) and output.is_file() and manifest_path.is_file():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if previous.get("params") == params:
            previous["cached"] = True
            return previous
    started = time.perf_counter()
    timing = {"mode": "cfr", "frames": 0, "chunks": 0}
    if backend == "lanczos":
        run_lanczos(source, output, target, start, duration,
                    info["has_audio"], info["fps"], info, encoder=encoder)
    else:
        video_only = work / "upscaled-video.mp4"
        timing = render_ai(source, video_only, work, backend, executable, model,
                           scale, max(TILE_MIN, args.tile), start, duration, info,
                           chunk=max(0, int(getattr(args, "chunk", 0) or 0)),
                           denoise_strength=denoise_strength,
                           weights=weights, weights2=weights2,
                           staging=staging, encoder=encoder)
        if not info["has_audio"]:
            os.replace(video_only, output)
        else:
            mux_audio(video_only, source, output, start, duration, info)
    verification = {"status": "not_applicable", "reason": "lanczos_baseline"}
    if backend != "lanczos":
        try:
            import restoration
            verification = restoration.verify_delivery(
                source, output, target, start, duration, backend, executable,
                model, scale, max(TILE_MIN, args.tile), denoise_strength,
                weights, weights2, work, staging=staging, encoder=encoder)
            if (verification["status"] == "verified"
                    and not getattr(args, "preflight_verified", False)):
                verification["status"] = "review"
                verification["reason"] = "no diagnosed preview was approved"
        except (UpscaleError, OSError, ValueError) as exc:
            verification = {"status": "review", "error": str(exc),
                            "verified_at": now()}
    elapsed = time.perf_counter() - started
    produced = probe(output)
    if [produced["width"], produced["height"]] != list(target):
        verification = {"status": "review", "reason": "output dimensions differ",
                        "expected": list(target),
                        "actual": [produced["width"], produced["height"]]}
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": now(),
        "source": str(source),
        "output": str(output),
        "source_hash": params["source_hash"],
        "params": params,
        "backend": backend,
        "model": model,
        "model_note": MODEL_NOTES.get(model or ""),
        "scale": scale,
        "tile": args.tile if backend != "lanczos" else None,
        "denoise_strength": denoise_strength,
        "staging": staging,
        "encoder": (encoder if encoder != "auto" else
                    ("nvenc" if encoder_available("hevc_nvenc") else "libx265")),
        "checkpoint": checkpoint_info(weights, weights2),
        "verification": verification,
        "source_size": [info["width"], info["height"]],
        "output_size": [produced["width"], produced["height"]],
        "source_pixel_format": info["pix_fmt"],
        "output_pixel_format": produced["pix_fmt"],
        "color": {key: info.get(key) for key in
                  ("color_primaries", "color_transfer", "color_space", "color_range")},
        "start_seconds": round(start, 3),
        "duration_seconds": round(duration, 3),
        "runtime_seconds": round(elapsed, 2),
        "timing": timing,
        "source_bytes": source.stat().st_size,
        "output_bytes": output.stat().st_size,
        "note": "upscaling does not correct color, exposure, or motion blur",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    try:
        offset = min(2.0, duration / 2)
        compare_frame(source, output, start + offset, offset,
                      work / "before-after.jpg")
    except UpscaleError:
        pass
    return manifest


def upscale_ranges(args, draft: Path, target: tuple[int, int],
                   restoration) -> dict:
    """Render only the timeline-used ranges, one asset per range."""
    processed = draft / ".content-studio" / "processed-clips"
    files = sorted(processed.glob("*/final.mp4"))
    entries = restoration.timeline_ranges(Path(args.timeline), files)
    target_width, target_height = target
    results: list[dict] = []
    assets: list[dict] = []
    for entry in entries:
        source = entry["source"]
        info = probe(source)
        factor = min(4, max(2, int(math.ceil(max(target_width / info["width"],
                                                target_height / info["height"])))))
        decision = {"decision": "FIX", "reasons": ["mode_always"]}
        preview = None
        if getattr(args, "mode", "auto") == "auto" and args.backend != "lanczos":
            analysis = restoration.analyze_clip(source, target)
            if analysis["decision"] in {"SKIP", "UNSUPPORTED"}:
                decision = analysis
            else:
                preview = restoration.preview_clip(
                    source, target,
                    preview_seconds=getattr(args, "preview_seconds", 5.0),
                    backend=args.backend, executable=args.realesrgan,
                    model=args.model, tile=args.tile,
                    denoise_strength=getattr(args, "denoise_strength", None),
                    weights=getattr(args, "weights", None),
                    weights2=getattr(args, "weights2", None),
                    staging=getattr(args, "staging", "jpeg"),
                    encoder=getattr(args, "encoder", "auto"),
                    work=source.parent / "upscale-work")
                decision = preview["decision"]
            if getattr(args, "review", False):
                decision["preview"] = str(preview["report_path"]) if preview else None
        ranges = entry["ranges"]
        if getattr(args, "analyze_only", False) or getattr(args, "preview", False):
            for start, end in ranges:
                results.append({"source": str(source), "status": "analyzed",
                                "decision": decision["decision"],
                                "reasons": decision.get("reasons", []),
                                "range": [start, end],
                                "preview": (str(preview["report_path"])
                                            if preview else None)})
            continue
        if decision["decision"] == "UNSUPPORTED":
            for start, end in ranges:
                results.append({"source": str(source), "status": "unsupported",
                                "decision": "UNSUPPORTED",
                                "reasons": decision.get("reasons", []),
                                "range": [start, end]})
            continue
        if decision["decision"] == "REVIEW" and not getattr(args, "approve", False):
            for start, end in ranges:
                results.append({"source": str(source), "status": "review_pending",
                                "decision": "REVIEW",
                                "reasons": decision.get("reasons", []),
                                "range": [start, end],
                                "preview": (str(preview["report_path"])
                                            if preview else None)})
            continue
        backend, model = args.backend, args.model
        if decision["decision"] == "SKIP":
            backend, model = "lanczos", None
        for index, (start, end) in enumerate(ranges):
            output = source.parent / "upscaled" / (
                f"{source.stem}-r{index:02d}-{int(start * 1000):09d}-"
                f"{int(end * 1000):09d}.mp4")
            manifest = upscale(argparse.Namespace(
                input=source, output=output, scale=factor, backend=backend,
                realesrgan=args.realesrgan, model=model, tile=args.tile,
                start=start, duration=end - start, target=args.target,
                chunk=getattr(args, "chunk", 0),
                denoise_strength=getattr(args, "denoise_strength", None),
                weights=getattr(args, "weights", None),
                weights2=getattr(args, "weights2", None),
                staging=getattr(args, "staging", "jpeg"),
                encoder=getattr(args, "encoder", "auto"),
                allow_hdr=getattr(args, "allow_hdr", False), force=args.force,
                preflight_verified=preview is not None,
                work=source.parent / "upscale-work" / "ranges" / output.stem))
            verification = manifest.get("verification") or {}
            review_status = "approved"
            if verification.get("status") == "review":
                if not getattr(args, "approve", False) \
                        and getattr(args, "mode", "auto") != "always":
                    results.append({"source": str(source),
                                    "status": "verification_review",
                                    "decision": decision["decision"],
                                    "reasons": decision.get("reasons", []),
                                    "range": [start, end],
                                    "asset": str(output),
                                    "verification": verification})
                    continue
                manifest["verification"]["status"] = "unverified_override"
                review_status = "unverified_override"
            assets.append({
                "source": str(source), "start": start, "end": end,
                "asset": str(output), "backend": manifest["backend"],
                "model": manifest["model"],
                "denoise_strength": manifest["denoise_strength"],
                "review_status": review_status,
                "verification": verification,
            })
            results.append({"source": str(source), "status": "upscaled",
                            "decision": decision["decision"],
                            "reasons": decision.get("reasons", []),
                            "range": [start, end],
                            "asset": str(output), "output": manifest})
    summary = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": now(),
        "draft": str(draft),
        "target": list(target),
        "mode": "timeline-ranges",
        "timeline": str(Path(args.timeline).resolve()),
        "clips": results,
        "upscaled": sum(1 for item in results if item["status"] == "upscaled"),
        "review_pending": sum(1 for item in results
                              if item["status"] == "review_pending"),
        "unsupported": sum(1 for item in results if item["status"] == "unsupported"),
        "verification_review": sum(1 for item in results
                                   if item["status"] == "verification_review"),
        "timeline_updated": 0,
    }
    manifest_dir = draft / ".content-studio" / "upscale"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "timeline-map.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "ranges": assets}, indent=2)
        + "\n", encoding="utf-8")
    if getattr(args, "write_timeline", None) and assets:
        summary["timeline_updated"] = restoration.write_timeline_map(
            Path(args.timeline), assets, Path(args.write_timeline))
    (manifest_dir / "upscale-batch.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    restoration.write_batch_report(summary, manifest_dir / "upscale-review.html")
    return summary


def upscale_draft(args) -> dict:
    import restoration

    draft = Path(args.draft).expanduser().resolve()
    target = parse_target(args.target or "4k")
    if target is None:
        raise UpscaleError("target is required")
    if getattr(args, "timeline_ranges", False):
        if not getattr(args, "timeline", None):
            raise UpscaleError("--timeline-ranges needs --timeline")
        return upscale_ranges(args, draft, target, restoration)
    processed = draft / ".content-studio" / "processed-clips"
    if not processed.is_dir():
        raise UpscaleError(f"processed clips not found: {processed}")
    files = sorted(processed.glob("*/final.mp4"))
    if getattr(args, "timeline", None):
        files = restoration.timeline_sources(Path(args.timeline), files)
    if args.limit:
        files = files[:max(1, int(args.limit))]
    target_width, target_height = target
    results = []
    for source in files:
        info = probe(source)
        source_orientation = "portrait" if info["height"] > info["width"] else "landscape"
        target_orientation = "portrait" if target_height > target_width else "landscape"
        if source_orientation != target_orientation:
            results.append({"source": str(source), "status": "orientation_mismatch",
                            "size": [info["width"], info["height"]],
                            "target": list(target)})
            continue
        if info["width"] >= target_width and info["height"] >= target_height:
            results.append({"source": str(source), "status": "already_at_target",
                            "size": [info["width"], info["height"]]})
            continue
        factor = min(4, max(2, int(math.ceil(max(target_width / info["width"],
                                                target_height / info["height"])))))
        output = source.with_name("final-4k.mp4")
        if args.dry_run:
            results.append({"source": str(source), "status": "would_upscale",
                            "factor": factor, "size": [info["width"], info["height"]],
                            "target": list(target)})
            continue
        decision = {"decision": "FIX", "reasons": ["mode_always"],
                    "detail": "AI upscaling requested without analysis"}
        preview = None
        if getattr(args, "analyze_only", False):
            analysis = restoration.analyze_clip(source, target)
            results.append({"source": str(source), "status": "analyzed",
                            "decision": analysis["decision"],
                            "reasons": analysis.get("reasons", []),
                            "preview": None})
            continue
        if getattr(args, "mode", "auto") == "auto" and args.backend != "lanczos":
            analysis = restoration.analyze_clip(source, target)
            if analysis["decision"] in {"SKIP", "UNSUPPORTED"}:
                decision = analysis
            else:
                preview = restoration.preview_clip(
                    source, target, preview_seconds=getattr(args, "preview_seconds", 5.0),
                    backend=args.backend, executable=args.realesrgan,
                    model=args.model, tile=args.tile,
                    denoise_strength=getattr(args, "denoise_strength", None),
                    weights=getattr(args, "weights", None),
                    weights2=getattr(args, "weights2", None),
                    staging=getattr(args, "staging", "jpeg"),
                    encoder=getattr(args, "encoder", "auto"),
                    work=source.parent / "upscale-work")
                decision = preview["decision"]
            if getattr(args, "review", False):
                decision["preview"] = str(preview["report_path"]) if preview else None
        if getattr(args, "analyze_only", False) or getattr(args, "preview", False):
            results.append({"source": str(source), "status": "analyzed",
                            "decision": decision["decision"],
                            "reasons": decision.get("reasons", []),
                            "preview": (str(preview["report_path"])
                                        if preview else None)})
            continue
        if decision["decision"] == "REVIEW" and not getattr(args, "approve", False):
            results.append({"source": str(source), "status": "review_pending",
                            "decision": "REVIEW",
                            "reasons": decision.get("reasons", []),
                            "preview": (str(preview["report_path"])
                                        if preview else None)})
            continue
        if decision["decision"] == "UNSUPPORTED":
            results.append({"source": str(source), "status": "unsupported",
                            "decision": "UNSUPPORTED",
                            "reasons": decision.get("reasons", [])})
            continue
        backend = args.backend
        model = args.model
        if decision["decision"] == "SKIP":
            backend, model = "lanczos", None
        manifest = upscale(argparse.Namespace(
            input=source, output=output, scale=factor, backend=backend,
            realesrgan=args.realesrgan, model=model, tile=args.tile,
            start=None, duration=None, target=args.target, chunk=getattr(args, "chunk", 0),
            denoise_strength=getattr(args, "denoise_strength", None),
            weights=getattr(args, "weights", None),
            weights2=getattr(args, "weights2", None),
            staging=getattr(args, "staging", "jpeg"),
            encoder=getattr(args, "encoder", "auto"),
            allow_hdr=getattr(args, "allow_hdr", False), force=args.force,
            preflight_verified=preview is not None,
            work=source.parent / "upscale-work"))
        verification = manifest.get("verification") or {}
        if verification.get("status") == "review" \
                and not getattr(args, "approve", False) \
                and getattr(args, "mode", "auto") != "always":
            results.append({"source": str(source), "status": "verification_review",
                            "decision": decision["decision"],
                            "reasons": decision.get("reasons", []),
                            "asset": str(output),
                            "verification": verification})
            continue
        if verification.get("status") == "review":
            manifest["verification"]["status"] = "unverified_override"
        backup = source.with_name("final-pre-upscale.mp4")
        if not backup.exists():
            shutil.copy2(source, backup)
        os.replace(output, source)
        report_path = source.parent / "report.json"
        if report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["upscale"] = manifest
            depth = "10-bit" if "10" in str(manifest["output_pixel_format"]) else "8-bit"
            report["final_format"] = (f"{manifest['output_size'][0]}x"
                                      f"{manifest['output_size'][1]} {depth} "
                                      f"{info['color_transfer'] or 'SDR'} "
                                      f"{fps_value(info['fps']):.3f} fps")
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        results.append({"source": str(source), "status": "upscaled",
                        "decision": decision["decision"], "factor": factor,
                        "reasons": decision.get("reasons", []), "output": manifest})
    summary = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": now(),
        "draft": str(draft),
        "target": list(target),
        "mode": getattr(args, "mode", "auto"),
        "clips": results,
        "upscaled": sum(1 for item in results if item["status"] == "upscaled"),
        "skipped": sum(1 for item in results
                       if item["status"] in {"already_at_target", "orientation_mismatch"}),
        "review_pending": sum(1 for item in results
                              if item["status"] == "review_pending"),
        "verification_review": sum(1 for item in results
                                   if item["status"] == "verification_review"),
        "unsupported": sum(1 for item in results if item["status"] == "unsupported"),
    }
    manifest_dir = draft / ".content-studio" / "upscale"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "upscale-batch.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    restoration.write_batch_report(summary, manifest_dir / "upscale-review.html")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--draft", type=Path,
                        help="batch-upscale a vlog draft's processed final.mp4 clips")
    parser.add_argument("--target", help="target: 4k, 2160p, 1080p, or WxH")
    parser.add_argument("--timeline", type=Path,
                        help="batch: only clips referenced by this editable timeline")
    parser.add_argument("--timeline-ranges", action="store_true",
                        help="batch: render only the timeline's used source ranges")
    parser.add_argument("--write-timeline", type=Path,
                        help="write a timeline copy that points at the upscaled range assets")
    parser.add_argument("--limit", type=int, help="batch: process only the first N clips")
    parser.add_argument("--dry-run", action="store_true",
                        help="batch: report what would be upscaled")
    parser.add_argument("--mode", choices=["auto", "always"], default="auto",
                        help="auto: analyze and only apply a passing preview")
    parser.add_argument("--analyze-only", action="store_true",
                        help="batch/single: diagnose without rendering")
    parser.add_argument("--preview", action="store_true",
                        help="batch/single: render comparison previews without replacing")
    parser.add_argument("--review", action="store_true",
                        help="write per-clip preview links into the batch report")
    parser.add_argument("--approve", action="store_true",
                        help="batch: apply REVIEW decisions whose preview looked acceptable")
    parser.add_argument("--preview-seconds", type=float, default=5.0,
                        help="candidate window length (default 5 s)")
    parser.add_argument("--scale", type=int, choices=[2, 3, 4], default=2,
                        help="upscale factor; 2 turns 1080p into 4K")
    parser.add_argument("--backend", choices=["realesrgan", "pytorch", "lanczos"],
                        help="default: realesrgan when installed, otherwise lanczos")
    parser.add_argument("--realesrgan", help="path to realesrgan-ncnn-vulkan executable")
    parser.add_argument("--model",
                        help="ncnn defaults to realesrgan-x4plus; pytorch defaults to "
                             "realesr-general-x4v3. realesr-animevideov3 is animation-only")
    parser.add_argument("--weights", help="pytorch checkpoint path (required for pytorch)")
    parser.add_argument("--weights2",
                        help="denoise partner checkpoint for realesr-general-x4v3")
    parser.add_argument("--denoise-strength", type=float,
                        help="realesr-general-x4v3 denoise strength (pytorch backend)")
    parser.add_argument("--tile", type=int, default=256,
                        help="realesrgan tile size; lower for limited VRAM")
    parser.add_argument("--chunk", type=int, default=0,
                        help="frames per inference chunk; 0 processes the clip in one pass")
    parser.add_argument("--staging", choices=["jpeg", "png"], default="jpeg",
                        help="intermediate frame format; jpeg is ~20x faster to write")
    parser.add_argument("--encoder", choices=["auto", "libx265", "nvenc"],
                        default="auto",
                        help="auto uses hevc_nvenc when ffmpeg supports it")
    parser.add_argument("--allow-hdr", action="store_true",
                        help="explicitly allow the frame pipeline on HDR/DV footage")
    parser.add_argument("--start", type=float, help="start second for a test excerpt")
    parser.add_argument("--duration", type=float, help="duration for a test excerpt")
    parser.add_argument("--work", type=Path, help="intermediate frame folder")
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.draft:
            manifest = upscale_draft(args)
        else:
            if not args.input or not args.output:
                if args.analyze_only or args.preview:
                    raise UpscaleError("use --analyze-only/--preview with --draft")
                raise UpscaleError("use --input and --output, or --draft")
            if args.analyze_only or args.preview:
                import restoration
                target = parse_target(args.target or "4k")
                analysis = restoration.analyze_clip(Path(args.input).resolve(), target)
                preview = None
                if args.preview:
                    preview = restoration.preview_clip(
                        Path(args.input).resolve(), target,
                        preview_seconds=args.preview_seconds, backend=args.backend,
                        executable=args.realesrgan, model=args.model, tile=args.tile,
                        denoise_strength=args.denoise_strength, weights=args.weights,
                        weights2=args.weights2, staging=args.staging,
                        encoder=args.encoder,
                        work=args.work or Path(args.output).parent / "upscale-work")
                manifest = {"analysis": analysis, "preview": preview}
            else:
                manifest = upscale(args)
        print(json.dumps(manifest, indent=2))
        return 0
    except (UpscaleError, OSError, ValueError) as exc:
        print(f"upscale: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
