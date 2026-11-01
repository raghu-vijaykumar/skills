"""Extract audio, frames and clips from a published video or a draft."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from common import Log, channel_root, human_size


def parse_time(value: str) -> float:
    value = value.strip()
    if not value:
        return 0.0
    if re.fullmatch(r"\d+(\.\d+)?", value):
        return float(value)
    parts = value.split(":")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def fmt_time(seconds: float) -> str:
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}m{sec:02d}s" if hours else f"{minutes}m{sec:02d}s"


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
         str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise SystemExit(f"ffprobe failed: {result.stderr.strip()[:200]}")
    data = json.loads(result.stdout)
    video = next((s for s in data["streams"] if s.get("codec_type") == "video"), None)
    return {"duration": float(data.get("format", {}).get("duration") or 0),
            "width": int(video["width"]) if video else None,
            "height": int(video["height"]) if video else None}


def resolve_target(channel_root_path: Path, args) -> tuple[Path, str]:
    if getattr(args, "path", None):
        path = Path(args.path).expanduser()
        return path, path.stem
    if getattr(args, "video", None):
        matches = sorted({p for p in channel_root_path.glob("**/video.mp4")
                          if args.video in p.parent.name})
        if not matches:
            raise SystemExit(f"no local video folder for id {args.video}")
        return matches[0], args.video
    if getattr(args, "draft", None):
        path = channel_root_path / "drafts" / args.draft / "video.mp4"
        if not path.exists():
            raise SystemExit(f"draft has no video.mp4: {path}")
        return path, args.draft
    raise SystemExit("pass --video ID, --draft NAME or --path FILE")


def out_dir(base: Path, out: str | None, target: str) -> Path:
    path = Path(out).expanduser() if out else base / "analysis" / re.sub(r"[^A-Za-z0-9._-]+", "-", target)
    path.mkdir(parents=True, exist_ok=True)
    return path


def audio(source: Path, start: float, end: float | None, dest: Path, log: Log) -> Path:
    target = dest / (f"audio-{int(start)}-{int(end)}.wav" if end else "audio-full.wav")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{start}"]
    if end:
        cmd += ["-to", f"{end}"]
    cmd += ["-i", str(source), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(target)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        log(f"audio failed: {result.stderr.strip()[:200]}")
        return target
    log(f"audio {target.name} ({human_size(target.stat().st_size)})")
    return target


def frames(source: Path, stamps: list[float], dest: Path, log: Log) -> list[Path]:
    written = []
    for index, stamp in enumerate(stamps, start=1):
        target = dest / f"frame-{index:03d}-{stamp:.2f}s.png"
        result = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{stamp}",
             "-i", str(source), "-frames:v", "1", "-q:v", "2", str(target)],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode == 0 and target.exists():
            written.append(target)
        else:
            log(f"frame at {stamp}s failed: {result.stderr.strip()[:120]}")
    log(f"{len(written)} frame(s)")
    return written


def clip(source: Path, start: float, end: float, dest: Path, copy: bool, log: Log) -> Path:
    target = dest / f"clip-{int(start)}-{int(end)}.mp4"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{start}",
           "-to", f"{end}", "-i", str(source)]
    if copy:
        cmd += ["-c", "copy", "-avoid_negative_ts", "make_zero"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart"]
    cmd.append(str(target))
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        log(f"clip failed: {result.stderr.strip()[:200]}")
        return target
    log(f"clip {target.name} ({human_size(target.stat().st_size)})")
    return target


def run(cfg: dict, args, log: Log) -> int:
    from common import channel_settings, select_channels

    slug, raw = select_channels(cfg, args.channel)[0]
    settings = channel_settings(cfg, slug, raw)
    root = channel_root(cfg, slug)
    source, label = resolve_target(root, args)
    info = probe(source)
    log(f"{label}: {fmt_time(info['duration'])}, {info['width']}x{info['height']}")
    dest = out_dir(root, args.out, label)

    start = parse_time(args.start) if getattr(args, "start", None) else 0.0
    end = parse_time(args.end) if getattr(args, "end", None) else None
    if end is not None and end <= start:
        raise SystemExit("--end must be greater than --start")
    if end is None and info["duration"]:
        end = info["duration"]

    if args.action in ("audio", "segment"):
        audio(source, start, end if end != info["duration"] else None, dest, log)

    if args.action in ("frames", "segment"):
        stamps = []
        if getattr(args, "at", None):
            stamps = [parse_time(value) for value in args.at.split(",") if value.strip()]
        else:
            count = args.count
            span = (end - start) if end else info["duration"]
            stamps = [start + span * (i + 0.5) / count for i in range(count)]
        frames(source, stamps, dest, log)

    if args.action in ("clip", "segment"):
        clip(source, start, end or info["duration"], dest, args.copy, log)

    log(f"output in {dest}")
    return 0
