"""Prepend a channel intro clip to a draft video with ffmpeg."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from common import Log, now, read_json, write_json


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams",
         "-show_format", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise SystemExit(f"ffprobe failed for {path}: {result.stderr.strip()[:200]}")
    data = json.loads(result.stdout)
    video = next((s for s in data["streams"] if s.get("codec_type") == "video"), None)
    audio = next((s for s in data["streams"] if s.get("codec_type") == "audio"), None)
    if not video:
        raise SystemExit(f"{path} has no video stream")
    num, _, den = (video.get("avg_frame_rate") or "25/1").partition("/")
    fps = (float(num) / float(den or 1)) if float(den or 1) else 25.0
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "fps": round(fps, 3) or 25.0,
        "duration": float(data.get("format", {}).get("duration") or 0.0),
        "has_audio": audio is not None,
    }


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]


def apply(video: Path, intro_path: Path, folder: Path, force: bool, log: Log) -> int:
    marker = folder / ".intro.json"
    state = read_json(marker)
    original = folder / "original-videos" / "video-before-intro.mp4"
    source = video

    if state and not force:
        log(f"{folder.name}: intro already applied ({state.get('applied')}); use --force")
        return 0
    if force and original.exists():
        source = original
    elif not original.exists():
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(video, original)
        log(f"kept the un-introed cut at {original.relative_to(folder)}")

    target = probe(source)
    lead = probe(intro_path)
    log(f"{folder.name}: {target['width']}x{target['height']}@{target['fps']}fps "
        f"+ intro {lead['duration']:.1f}s")

    width, height, fps = target["width"], target["height"], target["fps"]
    filters = []
    for index, info in enumerate((lead, target)):
        filters.append(
            f"[{index}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1,fps={fps}[v{index}]")
        if info["has_audio"]:
            filters.append(
                f"[{index}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a{index}]")
        else:
            filters.append(
                f"anullsrc=channel_layout=stereo:sample_rate=48000,"
                f"atrim=0:{info['duration']:.3f}[a{index}]")
    filters.append("[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]")

    temp = folder / "video.intro-tmp.mp4"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(intro_path), "-i", str(source),
           "-filter_complex", ";".join(filters),
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(temp)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                            errors="replace")
    if result.returncode != 0 or not temp.exists():
        temp.unlink(missing_ok=True)
        log(f"ffmpeg failed: {(result.stderr or '').strip()[:400]}")
        return 1
    temp.replace(video)
    out = probe(video)
    write_json(marker, {"applied": now(), "intro": str(intro_path),
                        "intro_hash": digest(intro_path),
                        "source_hash": digest(source),
                        "duration": round(out["duration"], 2)})
    log(f"{folder.name}: wrote {video.name} ({out['duration']:.1f}s, "
        f"{human(out['duration'])})")
    return 0


def human(seconds: float) -> str:
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes}m{sec:02d}s"
