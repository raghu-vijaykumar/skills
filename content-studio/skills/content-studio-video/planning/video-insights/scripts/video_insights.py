#!/usr/bin/env python3
"""Prepare published-video insight notes from the existing channel archive and reports."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HELPER = Path(__file__).resolve().parents[3] / "edit" / "clip-edit" / "scripts"
sys.path.insert(0, str(HELPER))

from common import DEFAULT_CONFIG, channel_path, channel_root, load_config, read_json, write_json  # noqa: E402

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
BEGIN = "<!-- VIDEO INSIGHTS: AUTO EVIDENCE BEGIN -->"
END = "<!-- VIDEO INSIGHTS: AUTO EVIDENCE END -->"
COMMENTS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
COMMENT_CACHE_SECONDS = 30 * 24 * 60 * 60


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def analytics_root(root: Path) -> Path:
    """Use the helper's existing store without creating analysis/ in legacy channels."""
    return channel_path(root, "analytics")


def archived_videos(root: Path) -> dict[str, dict]:
    rows = {}
    for kind in ("long", "shorts"):
        for path in sorted((root / kind).glob("*/metadata.json")):
            info = read_json(path)
            video_id = str(info.get("id") or "")
            if not VIDEO_ID.fullmatch(video_id):
                continue
            # The backup archive can contain private or scheduled downloads.
            if info.get("availability") != "public":
                continue
            upload = str(info.get("upload_date") or "")
            date = f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}" if re.fullmatch(r"\d{8}", upload) else None
            rows[video_id] = {
                "id": video_id, "kind": kind, "title": str(info.get("title") or video_id),
                "published_at": date, "duration_seconds": info.get("duration"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "archive_metadata": str(path.relative_to(root)).replace("\\", "/"),
                "verification": "public_archive_metadata",
            }
    return rows


def published_index(root: Path) -> dict[str, dict]:
    """Retain previously verified videos when their local media is pruned."""
    path = analytics_root(root) / "published-index.json"
    previous = read_json(path).get("videos") or {}
    rows = {key: {**value, "id": key} for key, value in previous.items()
            if VIDEO_ID.fullmatch(key) and isinstance(value, dict)
            and value.get("verification") == "public_archive_metadata"}
    rows.update(archived_videos(root))
    return dict(sorted(rows.items()))


def save_index(root: Path, rows: dict[str, dict]) -> Path:
    path = analytics_root(root) / "published-index.json"
    old = read_json(path) if path.exists() else {}
    if old.get("schema_version") != 1 or old.get("videos") != rows:
        write_json(path, {"schema_version": 1, "generated_at": utc_now(), "videos": rows})
    return path


def replace_evidence(path: Path, title: str, evidence: str, authored_template: str) -> None:
    block = f"{BEGIN}\n{evidence.rstrip()}\n{END}"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {title}\n\n{block}\n\n{authored_template}", encoding="utf-8")
        return
    current = path.read_text(encoding="utf-8")
    if current.count(BEGIN) != 1 or current.count(END) != 1:
        raise ValueError(f"refusing to change note without one intact evidence block: {path}")
    start = current.index(BEGIN)
    finish = current.index(END) + len(END)
    if start >= current.index(END):
        raise ValueError(f"refusing malformed evidence markers: {path}")
    revised = current[:start] + block + current[finish:]
    if revised != current:
        path.write_text(revised, encoding="utf-8")


def age_label(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")


def value(data: dict, key: str) -> str:
    result = data.get(key)
    return "unavailable" if result is None else str(result)


def video_evidence(root: Path, row: dict, dataset: dict[str, dict]) -> str:
    video_id = row["id"]
    folder = analytics_root(root) / video_id
    metric_path = folder / "metrics.json"
    metric_record = read_json(metric_path) if metric_path.exists() else {}
    metrics = metric_record.get("metrics") or {}
    item = dataset.get(video_id) or {}
    dataset_path = analytics_root(root) / "insights.json"
    dataset_generated = read_json(dataset_path).get("generated") if dataset_path.exists() else None
    lines = [
        "## Measured evidence",
        f"- Published video: [{row['title']}]({row['url']}) (`{video_id}`; {row['kind']}).",
        f"- Published date: {row.get('published_at') or 'unavailable'}; duration: {row.get('duration_seconds') or 'unavailable'} seconds.",
        f"- Last verified archive metadata (may be pruned locally): `{row.get('archive_metadata') or 'previous verified index'}`.",
        f"- Owned metrics: `{metric_path.relative_to(root).as_posix()}` ({age_label(metric_path) if metric_path.exists() else 'unavailable'}; source {metric_record.get('source') or 'unavailable'}).",
        f"- Views: {value(metrics, 'views')}; average view duration: {value(metrics, 'averageViewDuration')} seconds; average viewed: {value(metrics, 'averageViewPercentage')}%.",
        f"- Likes: {value(metrics, 'likes')}; comments: {value(metrics, 'comments')}; shares: {value(metrics, 'shares')}; subscribers gained: {value(metrics, 'subscribersGained')}.",
        f"- Owned CTR: {value(item, 'ctr')}; Shorts VTR: {value(item, 'vtr')} (dataset generated {dataset_generated or 'unavailable'}). Missing values are unavailable, never zero.",
    ]
    retention = folder / "retention.csv"
    lines.append(f"- Retention curve: `{retention.relative_to(root).as_posix()}` ({age_label(retention)})" if retention.exists()
                 else "- Retention curve: unavailable.")
    comments = folder / "comments.json"
    if comments.exists() and time.time() - comments.stat().st_mtime > COMMENT_CACHE_SECONDS:
        # Comment text is short-lived API data. Expire only files made by this collector.
        if read_json(comments).get("source") == "owned YouTube Data API commentThreads":
            comments.unlink()
    if comments.exists():
        record = read_json(comments)
        lines.append(f"- Viewer feedback: {len(record.get('comments') or [])} sampled top-level comments in `{comments.relative_to(root).as_posix()}` (collected {record.get('collected_at') or 'unknown'}).")
    else:
        lines.append("- Viewer feedback: unavailable; no comments report collected.")
    return "\n".join(lines)


def channel_evidence(root: Path, rows: dict[str, dict]) -> str:
    store = analytics_root(root)
    dataset_path = store / "insights.json"
    dataset = read_json(dataset_path) if dataset_path.exists() else {}
    long_count = sum(row["kind"] == "long" for row in rows.values())
    short_count = sum(row["kind"] == "shorts" for row in rows.values())
    status_path = store / "video-insights-source-status.json"
    status = read_json(status_path) if status_path.exists() else {}
    states = ", ".join(f"{name}: {item.get('status', 'unknown')}" for name, item in (status.get("sources") or {}).items())
    recent = sorted(rows.values(), key=lambda row: row.get("published_at") or "", reverse=True)[:12]
    lines = [
        "## Measured evidence",
        f"- Verified published index: {len(rows)} videos ({long_count} long, {short_count} Shorts) in `{(store / 'published-index.json').relative_to(root).as_posix()}`.",
        f"- Owned channel dataset: `{dataset_path.relative_to(root).as_posix()}` ({dataset.get('generated') or 'unavailable'}); {len(dataset.get('videos') or [])} rows.",
        f"- Last report refresh: {status.get('collected_at') or 'unavailable'}; {states or 'no source status recorded'}.",
        "- Compare only similar formats, ages, topics, and languages. A cohort average alone does not establish why a video performed differently.",
        "- Recent published-video notes (all verified IDs are in the index):",
    ]
    lines.extend(f"  - [{row['id']}]({row['id']}/video-insights.md) — {row['title']} ({row.get('published_at') or 'date unavailable'})."
                 for row in recent)
    return "\n".join(lines)


def dataset_rows(root: Path) -> dict[str, dict]:
    path = analytics_root(root) / "insights.json"
    data = read_json(path) if path.exists() else {}
    return {row["id"]: row for row in data.get("videos") or []
            if isinstance(row, dict) and VIDEO_ID.fullmatch(str(row.get("id") or ""))}


def prepare(root: Path, channel_name: str) -> dict:
    rows = published_index(root)
    if not rows:
        raise ValueError(f"no verified published archive metadata or prior index under {root}")
    index_path = save_index(root, rows)
    store = analytics_root(root)
    dataset = dataset_rows(root)
    channel_note = store / "video-insights.md"
    replace_evidence(channel_note, f"Video Insights — {channel_name}", channel_evidence(root, rows),
                     "## Observed channel patterns\n\nRecord repeated observations with published video IDs, dates, and timecodes.\n\n"
                     "## Interpretation and limits\n\nSeparate hypotheses from measured facts; include counterexamples.\n\n"
                     "## Suggestions for future edits\n\nCite supporting video notes and name a bounded comparison to review.\n")
    for row in rows.values():
        note = store / row["id"] / "video-insights.md"
        # Keep the heading stable if the creator later changes the public title.
        replace_evidence(note, f"Video Insights — {row['id']}",
                         video_evidence(root, row, dataset),
                         "## Observations\n\nRecord exact moments, metrics, and audience feedback with source links.\n\n"
                         "## Interpretation and limits\n\nState plausible explanations and what the evidence cannot establish.\n\n"
                         "## Suggestions for future edits\n\nName a specific edit to compare and its review criterion.\n")
    return {"published_videos": len(rows), "channel_note": str(channel_note),
            "per_video_notes": len(rows), "index": str(index_path)}


def parse_comment_threads(payload: dict, video_id: str) -> list[dict]:
    comments = []
    for item in payload.get("items") or []:
        top = (item.get("snippet") or {}).get("topLevelComment") or {}
        snippet = top.get("snippet") or {}
        comment_id = str(top.get("id") or "")
        text = snippet.get("textOriginal") or snippet.get("textDisplay")
        if not comment_id or not text:
            continue
        comments.append({"id": comment_id, "text": text, "published_at": snippet.get("publishedAt"),
                         "likes": snippet.get("likeCount"),
                         "url": f"https://www.youtube.com/watch?v={video_id}&lc={urllib.parse.quote(comment_id)}"})
    return comments


def collect_comments(root: Path, videos: list[dict], limit: int, settings: dict) -> dict:
    if limit <= 0 or not videos:
        return {"status": "skipped", "videos": 0}
    import analytics  # noqa: E402
    from common import Log  # noqa: E402

    client = analytics.ApiClient(settings, Log())
    completed = 0
    for row in videos:
        video_id = row["id"]
        collected = []
        token = None
        while len(collected) < limit:
            params = {"part": "snippet", "videoId": video_id, "order": "time",
                      "maxResults": min(100, limit - len(collected)), "textFormat": "plainText"}
            if token:
                params["pageToken"] = token
            request = urllib.request.Request(COMMENTS_URL + "?" + urllib.parse.urlencode(params),
                                             headers={"Authorization": f"Bearer {client.token['access_token']}"})
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            collected.extend(parse_comment_threads(payload, video_id))
            token = payload.get("nextPageToken")
            if not token or not payload.get("items"):
                break
        write_json(analytics_root(root) / video_id / "comments.json",
                   {"video_id": video_id, "collected_at": utc_now(),
                    "source": "owned YouTube Data API commentThreads", "sample_limit": limit,
                    "comments": collected[:limit]})
        completed += 1
    return {"status": "ok", "videos": completed, "sample_limit": limit}


def run_collector(command: list[str]) -> dict:
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "failed", "detail": str(exc)}
    output = (result.stderr or result.stdout).strip().splitlines()
    return {"status": "ok" if result.returncode == 0 else "failed",
            "detail": output[-1] if output else "no output"}


def refresh(root: Path, channel: str, config: Path, last: int, vtr_count: int,
            comments_limit: int, settings: dict, reauthorize: bool = False) -> dict:
    helper = HELPER / "content.py"
    base = [sys.executable, str(helper)]
    select = ["--channel", channel, "--config", str(config)]
    analytics_command = base + ["analytics", *select, "--last", str(last)]
    if reauthorize:
        analytics_command.append("--reauthorize")
    status = {"analytics": run_collector(analytics_command)}
    if reauthorize and status["analytics"]["status"] != "ok":
        # One consent attempt is enough; avoid launching a second browser flow.
        status["dataset"] = {"status": "skipped", "detail": "reauthorization did not complete"}
        status["comments"] = {"status": "skipped", "detail": "reauthorization did not complete"}
        write_json(analytics_root(root) / "video-insights-source-status.json",
                   {"collected_at": utc_now(), "sources": status})
        return status
    status["dataset"] = run_collector(base + ["insights", *select, "--vtr-count", str(vtr_count)])
    rows = published_index(root)
    videos = sorted(rows.values(), key=lambda row: row.get("published_at") or "", reverse=True)[:last]
    try:
        status["comments"] = collect_comments(root, videos, comments_limit, settings)
    except (SystemExit, urllib.error.URLError, ValueError, OSError) as exc:
        status["comments"] = {"status": "unavailable", "detail": str(exc)}
    write_json(analytics_root(root) / "video-insights-source-status.json",
               {"collected_at": utc_now(), "sources": status})
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "refresh", "paths"))
    parser.add_argument("--channel", required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--video", help="published video ID for paths")
    parser.add_argument("--last", type=int, default=10, help="recent videos to refresh")
    parser.add_argument("--vtr-count", type=int, default=0, help="owned Studio Shorts reach reads")
    parser.add_argument("--comments-limit", type=int, default=100, help="top-level comments per video; 0 skips")
    parser.add_argument("--reauthorize", action="store_true", help="renew owned-channel Google read-only consent once before refreshing reports")
    args = parser.parse_args(argv)
    if args.last < 1 or not 0 <= args.comments_limit <= 500 or args.vtr_count < 0:
        parser.error("--last must be positive, --comments-limit 0..500, and --vtr-count nonnegative")
    if args.video and not VIDEO_ID.fullmatch(args.video):
        parser.error("--video must be an eleven-character YouTube ID")
    if args.video and args.action != "paths":
        parser.error("--video applies only to paths")
    if args.reauthorize and args.action != "refresh":
        parser.error("--reauthorize applies only to refresh")
    config = args.config.expanduser().resolve()
    cfg = load_config(config)
    raw = (cfg.get("channels") or {}).get(args.channel)
    if raw is None:
        parser.error(f"unknown channel: {args.channel}")
    root = channel_root(cfg, args.channel)
    if not root.is_dir():
        parser.error(f"channel workspace does not exist: {root}")
    if args.action == "paths":
        rows = published_index(root)
        if args.video and args.video not in rows:
            parser.error(f"video is not verified in the published archive: {args.video}")
        selected = [rows[args.video]] if args.video else rows.values()
        print(json.dumps({"channel": str(analytics_root(root) / "video-insights.md"),
                          "videos": {row["id"]: str(analytics_root(root) / row["id"] / "video-insights.md")
                                     for row in selected}}, indent=2))
        return 0
    status = None
    if args.action == "refresh":
        from common import channel_settings  # noqa: E402
        status = refresh(root, args.channel, config, args.last, args.vtr_count,
                         args.comments_limit, channel_settings(cfg, args.channel, raw), args.reauthorize)
    result = prepare(root, str(raw.get("name") or args.channel))
    if status is not None:
        result["sources"] = status
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if status is None or all(item["status"] in ("ok", "skipped") for item in status.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
