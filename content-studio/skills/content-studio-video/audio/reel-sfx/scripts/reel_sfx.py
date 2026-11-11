#!/usr/bin/env python3
"""Download a public Instagram Reel and export reviewable sound-effect ranges."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit


REEL_PATH = re.compile(r"^/reel/([A-Za-z0-9_-]+)/?$", re.ASCII)
REPO_ROOT = Path(__file__).resolve().parents[6]


def private_path(path: Path) -> Path:
    path = path.expanduser().resolve()
    # Public skill source must never receive third-party media or private metadata.
    if path == REPO_ROOT or REPO_ROOT in path.parents:
        raise ValueError("Output must be outside the source repository")
    return path


def canonical_url(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {
        "instagram.com", "www.instagram.com"
    } or parsed.username or parsed.password or parsed.port:
        raise ValueError("Expected a public https://www.instagram.com/reel/<id>/ URL")
    match = REEL_PATH.fullmatch(parsed.path)
    if not match:
        raise ValueError("Expected a public Instagram Reel URL")
    reel_id = match.group(1)
    return f"https://www.instagram.com/reel/{reel_id}/", reel_id


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe(source: Path) -> dict:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,sample_rate,channels", "-of", "json", str(source)],
            capture_output=True, text=True, check=True, timeout=30)
        data = json.loads(result.stdout)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired,
            json.JSONDecodeError) as error:
        raise ValueError("Source media could not be probed") from error
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    duration = float(data.get("format", {}).get("duration", 0))
    if not audio or duration <= 0:
        raise ValueError("Source has no usable audio")
    return {"duration_seconds": duration, "sample_rate": int(audio["sample_rate"]),
            "channels": int(audio["channels"])}


def download(url: str, output_dir: Path) -> dict:
    canonical, reel_id = canonical_url(url)
    output_dir = private_path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    media = output_dir / f"reel-{reel_id}.mp4"
    record_file = output_dir / f"reel-{reel_id}.source.json"
    if media.exists() or record_file.exists():
        if media.is_file() and record_file.is_file():
            record = json.loads(record_file.read_text(encoding="utf-8"))
            if record.get("url") == canonical and record.get("sha256") == sha256(media):
                return record
        raise ValueError("Existing download is incomplete or differs from its source record")
    template = output_dir / f"reel-{reel_id}.%(ext)s"
    command = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-progress",
               "--no-warnings", "--quiet", "--write-info-json", "--merge-output-format",
               "mp4", "-o", str(template), canonical]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("Reel download failed or timed out") from error
    if result.returncode:
        raise ValueError("Reel download failed: " + (result.stderr.strip()[-400:] or "unknown error"))
    info_file = output_dir / f"reel-{reel_id}.info.json"
    if not media.is_file() or not info_file.is_file():
        raise ValueError("Reel download did not produce MP4 media and metadata")
    info = json.loads(info_file.read_text(encoding="utf-8"))
    record = {"id": reel_id, "url": canonical, "creator": info.get("uploader"),
              "creator_id": info.get("uploader_id"), "title": info.get("title"),
              "upload_date": info.get("upload_date"), "license": info.get("license"),
              "media": str(media), "sha256": sha256(media), "probe": probe(media)}
    record_file.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # yt-dlp's full info file can contain expiring stream URLs; retain only needed provenance.
    info_file.unlink()
    return record


def extract(source: Path, output: Path, start: float, end: float,
            name: str, category: str, source_record: Path | None = None) -> dict:
    source = source.expanduser().resolve()
    output = private_path(output)
    if not source.is_file() or not name.strip() or not category.strip():
        raise ValueError("Existing source, name, and category are required")
    if output.suffix.lower() != ".wav" or output.exists() or output.with_suffix(".json").exists():
        raise ValueError("Output must be a new .wav path with no existing sidecar")
    media = probe(source)
    if start < 0 or end <= start or end > media["duration_seconds"] + 0.001:
        raise ValueError("Effect range must be positive and inside the source")
    provenance = {}
    if source_record:
        provenance = json.loads(source_record.read_text(encoding="utf-8"))
        if provenance.get("sha256") != sha256(source):
            raise ValueError("Source hash does not match its download record")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i",
               str(source), "-ss", f"{start:.6f}", "-t", f"{end-start:.6f}",
               "-map", "0:a:0", "-vn", "-c:a", "pcm_s24le", str(output)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode or not output.is_file():
            raise ValueError("Effect export failed: " + result.stderr.strip()[-400:])
        exported = probe(output)
        if abs(exported["duration_seconds"] - (end - start)) > 0.03:
            raise ValueError("Effect export duration differs from the selected range")
        record = {"name": name.strip(), "category": category.strip(),
                  "source": str(source), "source_sha256": sha256(source),
                  "source_url": provenance.get("url"), "creator": provenance.get("creator"),
                  "start_seconds": start, "end_seconds": end, "output": str(output),
                  "sha256": sha256(output), "media": exported,
                  "effect_review": "pending", "rights": "unknown", "reuse_status": "reference-only"}
        output.with_suffix(".json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return record
    except (OSError, subprocess.TimeoutExpired, ValueError):
        output.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    get = actions.add_parser("download")
    get.add_argument("--url", required=True)
    get.add_argument("--output-dir", required=True, type=Path)
    cut = actions.add_parser("extract")
    cut.add_argument("--source", required=True, type=Path)
    cut.add_argument("--source-record", type=Path)
    cut.add_argument("--output", required=True, type=Path)
    cut.add_argument("--start", required=True, type=float)
    cut.add_argument("--end", required=True, type=float)
    cut.add_argument("--name", required=True)
    cut.add_argument("--category", required=True)
    args = parser.parse_args()
    record = (download(args.url, args.output_dir) if args.action == "download" else
              extract(args.source, args.output, args.start, args.end,
                      args.name, args.category, args.source_record))
    print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"reel-sfx: {error}") from error
