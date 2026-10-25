"""yt-dlp downloading and per-video filing."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from common import Log, archive_ids, read_json, run_stream

SUFFIX_KIND = {
    "jpg": "thumbnail", "jpeg": "thumbnail", "png": "thumbnail", "webp": "thumbnail",
    "info.json": "metadata",
    "mp4": "video", "mkv": "video", "webm": "video",
}


def format_selector(quality) -> str:
    quality = str(quality)
    return (f"bv*[height<={quality}]+ba/b[height<={quality}]" if quality.isdigit() else "bv*+ba/b")


def resolve_channel_id(settings: dict, log: Log) -> str:
    if settings.get("channel_id"):
        return settings["channel_id"]
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--flat-playlist", "--playlist-items", "1",
         "--print", "playlist:channel_id", settings["source"]],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("UC") and len(line) == 24:
            settings["channel_id"] = line
            log(f"resolved {settings['source']} -> {line}")
            return line
    raise SystemExit(f"could not resolve a channel id for {settings['source']}")


def download(targets: list[str], staging: Path, archive: Path, quality, log: Log,
             cookies: Path | None = None) -> int:
    staging.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "yt_dlp",
           "-f", format_selector(quality),
           "--merge-output-format", "mp4",
           "--no-overwrites", "--no-mtime", "--newline",
           "--retries", "10", "--fragment-retries", "10", "--concurrent-fragments", "4",
           "--embed-metadata", "--embed-thumbnail",
           "--write-info-json", "--write-thumbnail", "--convert-thumbnails", "jpg",
           "--download-archive", str(archive),
           "--js-runtimes", "node",
           "-o", str(staging / "%(upload_date>%Y-%m-%d)s__%(id)s.%(ext)s"),
           "--no-warnings"]
    if cookies:
        cmd += ["--cookies", str(cookies)]
    rc = 0
    for target in targets:
        log(f"yt-dlp {target}")
        rc |= run_stream(cmd + [target], log)
    return rc


def description_text(info: dict) -> str:
    tags = ", ".join(info.get("tags") or [])
    return "\n".join([
        "Title: " + str(info.get("title") or ""),
        "Channel: " + str(info.get("channel") or info.get("uploader") or ""),
        "Upload date: " + str(info.get("upload_date") or ""),
        "Publish date: " + str(info.get("release_date") or info.get("upload_date") or ""),
        "Duration: " + str(info.get("duration_string") or ""),
        "Views: " + str(info.get("view_count") or ""),
        "Video ID: " + str(info.get("id") or ""),
        "URL: " + str(info.get("webpage_url") or ""),
        "Thumbnail: thumbnail.jpg",
        "",
        "Tags: " + tags,
        "",
        "Description:",
        "-" * 60,
        str(info.get("description") or "(no description)").strip(),
        "",
    ])


def promote(staging: Path, target: Path, log: Log) -> int:
    if not staging.exists():
        return 0
    groups: dict[str, dict[str, Path]] = {}
    for path in sorted(staging.iterdir()):
        if not path.is_file():
            continue
        match = re.match(r"^(\d{4}-\d{2}-\d{2})__([A-Za-z0-9_-]{11})\.(.+)$", path.name)
        if not match:
            continue
        _, vid, suffix = match.groups()
        kind = SUFFIX_KIND.get(suffix)
        if kind:
            groups.setdefault(vid, {})[kind] = path

    filed = 0
    for vid, files in groups.items():
        info = read_json(files["metadata"]) if "metadata" in files else {}
        upload = str(info.get("upload_date") or "")
        date = f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}" if len(upload) == 8 else "unknown-date"
        from common import sanitize

        folder = target / sanitize(f"{date} - {info.get('title') or vid} [{vid}]")
        folder.mkdir(parents=True, exist_ok=True)
        names = {"video": "video" + files["video"].suffix.lower(),
                 "thumbnail": "thumbnail.jpg", "metadata": "metadata.json"}
        for kind, src in files.items():
            shutil.move(str(src), str(folder / names[kind]))
        if "metadata" in files:
            (folder / "description.txt").write_text(description_text(info), encoding="utf-8")
        filed += 1
        log(f"filed {folder.name}")
    return filed


def archive_count(archive: Path) -> int:
    return len(archive_ids(archive))
