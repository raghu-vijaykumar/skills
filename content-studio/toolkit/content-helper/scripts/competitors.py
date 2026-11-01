"""Collect observable public video facts for topic comparisons, not private analytics."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from common import Log, channel_path, channel_root, select_channels, write_json


def video_id(value: str) -> str:
    """Accept a YouTube ID or canonical video URL supplied by research."""
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    parsed = urlparse(value)
    host = parsed.hostname or ""
    if host in ("youtu.be", "www.youtu.be"):
        candidate = parsed.path.strip("/").split("/")[0]
    elif host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        candidate = parse_qs(parsed.query).get("v", [""])[0]
        if not candidate and parsed.path.startswith("/shorts/"):
            candidate = parsed.path.split("/")[2]
    else:
        candidate = ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        raise ValueError(f"not a YouTube video ID or URL: {value}")
    return candidate


def public_row(info: dict, collected: str) -> dict:
    """Do not manufacture impressions, CTR, VTR, or retention for public videos."""
    vid = video_id(str(info.get("id") or info.get("webpage_url") or ""))
    return {"videoId": vid, "url": f"https://www.youtube.com/watch?v={vid}",
            "channelId": info.get("channel_id"), "channel": info.get("channel"),
            "title": info.get("title"), "description": info.get("description"),
            "publishedAt": info.get("upload_date"), "durationSeconds": info.get("duration"),
            "views": info.get("view_count"), "likes": info.get("like_count"),
            "comments": info.get("comment_count"), "collectedAt": collected,
            "metricSource": "public YouTube video page via yt-dlp",
            "ctr": None, "vtr": None, "retention": None}


def collect(topic: str, urls: list[str], limit: int, extractor) -> tuple[list[dict], list[dict]]:
    """Search a topic, then resolve each candidate to one source-linked video."""
    candidates = list(urls)
    failures: list[dict] = []
    if topic:
        try:
            found = extractor(f"ytsearch{limit}:{topic}", flat=True)
            candidates.extend((entry.get("url") or entry.get("id") or "")
                              for entry in found.get("entries") or [] if entry)
        except Exception as exc:
            failures.append({"source": "YouTube topic search", "error": str(exc)})
    rows: list[dict] = []
    seen = set()
    collected = datetime.now(timezone.utc).isoformat()
    for candidate in candidates:
        try:
            vid = video_id(candidate)
            if vid in seen:
                continue
            seen.add(vid)
            info = extractor(f"https://www.youtube.com/watch?v={vid}", flat=False)
            rows.append(public_row(info, collected))
        except Exception as exc:
            failures.append({"source": str(candidate), "error": str(exc)})
        if len(rows) >= limit:
            break
    return rows, failures


def run(cfg: dict, args, log: Log) -> int:
    slug, _ = select_channels(cfg, args.channel)[0]
    root = channel_root(cfg, slug)
    if not args.topic and not args.video:
        raise SystemExit("competitors needs --topic or --video")
    if not 1 <= args.limit <= 50:
        raise SystemExit("--limit must be 1..50")
    import yt_dlp
    def extract(url: str, *, flat: bool) -> dict:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True,
                               "skip_download": True, "extract_flat": flat}) as downloader:
            return downloader.extract_info(url, download=False)
    rows, failures = collect(args.topic or "", args.video or [], args.limit, extract)
    label = re.sub(r"[^a-z0-9-]+", "-", (args.topic or "selected").lower()).strip("-")[:55] or "selected"
    out = Path(args.out).expanduser() if args.out else channel_path(root, "analytics") / "competitors" / f"{label}.json"
    if not out.resolve().is_relative_to(root.resolve()):
        raise SystemExit("competitor output must stay inside the channel workspace")
    write_json(out, {"channel": slug, "topic": args.topic, "collectedAt": datetime.now(timezone.utc).isoformat(),
                     "kind": "public-comparison", "videos": rows, "failures": failures})
    log(f"public comparisons: {len(rows)} videos, {len(failures)} failures -> {out}")
    return 0 if rows else 1
