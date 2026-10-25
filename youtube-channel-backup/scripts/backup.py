#!/usr/bin/env python3
"""Incremental YouTube channel backup: per-video folders, then Google Drive."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = SKILL_ROOT / "config.json"
LOCAL_OVERRIDE = SKILL_ROOT / "config.local.json"
ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
SUFFIX_KIND = {
    "jpg": "thumbnail",
    "jpeg": "thumbnail",
    "png": "thumbnail",
    "webp": "thumbnail",
    "info.json": "metadata",
    "mp4": "video",
    "mkv": "video",
    "webm": "video",
}


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


class Log:
    def __init__(self, path: Path | None = None):
        self.path = path
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg: str) -> None:
        line = f"[{now()}] {msg}"
        print(line, flush=True)
        if self.path:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")


def sanitize(text: str, max_len: int = 90) -> str:
    text = re.sub(r"\s+", " ", ILLEGAL.sub("", text)).strip().rstrip(".")
    if len(text) > max_len:
        cut = text[:max_len]
        space = cut.rfind(" ")
        text = (cut[:space] if space > max_len * 0.6 else cut).rstrip(" -|,")
    return text or "untitled"


def config_template() -> dict:
    return {
        "localRoot": str(Path.home() / "yt-backups"),
        "remoteRoot": "gdrive:YouTubeBackups",
        "browser": "brave",
        "browserDebugPort": 9223,
        "quality": "best",
        "transfers": 2,
        "includePrivate": True,
        "channels": {
            "example-channel": {
                "name": "My Channel",
                "url": "https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx",
                "driveFolder": "gdrive:YouTubeBackups/My Channel",
                "includePrivate": True,
            }
        },
    }


def merge_config(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if key == "channels" and isinstance(value, dict) and isinstance(base.get(key), dict):
            for slug, channel in value.items():
                if isinstance(channel, dict) and isinstance(base[key].get(slug), dict):
                    base[key][slug].update(channel)
                else:
                    base[key][slug] = channel
        else:
            base[key] = value
    return base


def load_config(path: Path) -> dict:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config_template(), indent=2) + "\n", encoding="utf-8")
        raise SystemExit(f"Created a config template at {path}\nEdit it, then run again.")
    with path.open(encoding="utf-8-sig") as fh:
        cfg = json.load(fh)
    if path.resolve() == DEFAULT_CONFIG.resolve() and LOCAL_OVERRIDE.exists():
        with LOCAL_OVERRIDE.open(encoding="utf-8-sig") as fh:
            cfg = merge_config(cfg, json.load(fh))
    defaults = {"localRoot": str(Path.home() / "yt-backups"), "quality": "best",
                "transfers": 2, "browser": "brave", "browserDebugPort": 9223,
                "remoteRoot": cfg.get("remote", "gdrive:YouTubeBackups"),
                "includePrivate": True, "channels": {}}
    for key, value in defaults.items():
        cfg.setdefault(key, value)
    return cfg


def channel_settings(cfg: dict, slug: str, channel: dict) -> dict:
    source = channel.get("url") or channel.get("channelId") or channel.get("handle")
    if not source:
        raise SystemExit(f"channel '{slug}' needs a url, handle or channelId")
    names = {"out-of-office": "Out of Office Mode"}
    remote_root = str(cfg.get("remoteRoot") or "").rstrip("/")
    return {
        "source": source,
        "channel_id": channel.get("channelId", ""),
        "name": channel.get("name") or names.get(slug) or slug,
        "quality": channel.get("quality", cfg.get("quality")),
        "include_private": bool(channel.get("includePrivate",
                                            channel.get("includeScheduled",
                                                        cfg.get("includePrivate", True)))),
        "drive_folder": (channel.get("driveFolder")
                         or (f"{remote_root}/{slug}" if remote_root else "")),
    }


def resolve_channel_id(settings: dict, log: Log) -> str:
    if settings["channel_id"]:
        return settings["channel_id"]
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


def format_selector(quality) -> str:
    quality = str(quality)
    return (f"bv*[height<={quality}]+ba/b[height<={quality}]" if quality.isdigit() else "bv*+ba/b")


def check_tools(log: Log, need_rclone: bool) -> None:
    problems = []
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        problems.append("yt-dlp missing: python -m pip install --user yt-dlp yt-dlp-ejs")
    if not shutil.which("ffmpeg"):
        problems.append("ffmpeg missing: winget install Gyan.FFmpeg")
    if not shutil.which("node") and not shutil.which("deno"):
        problems.append("node missing (solves YouTube JS challenges): winget install OpenJS.NodeJS")
    if need_rclone and not shutil.which("rclone"):
        problems.append("rclone missing: winget install Rclone.Rclone")
    for problem in problems:
        log("MISSING " + problem)
    if problems:
        raise SystemExit(1)


def run_stream(cmd: list[str], log: Log, echo: tuple[str, ...] = ()) -> int:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace", bufsize=1)
    last_bucket = -1
    assert proc.stdout is not None
    for raw in proc.stdout:
        line = raw.rstrip()
        if not line:
            continue
        match = re.search(r"\[download\]\s+(\d{1,3}(?:\.\d)?)%", line)
        if match:
            bucket = int(float(match.group(1))) // 10
            if bucket != last_bucket:
                log(line)
                last_bucket = bucket
            continue
        if "Destination" in line or "Transferred" in line or "ERROR" in line or "WARNING" in line:
            log(line)
        elif any(token in line for token in echo):
            log(line)
    code = proc.wait()
    return code if code >= 0 else 1


def yt_targets(targets: list[str], staging: Path, archive: Path, quality, log: Log,
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


def read_info(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8-sig") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


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
        info = read_info(files["metadata"]) if "metadata" in files else {}
        upload = str(info.get("upload_date") or "")
        date = f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}" if len(upload) == 8 else "unknown-date"
        folder = target / sanitize(f"{date} - {info.get('title') or vid} [{vid}]")
        folder.mkdir(parents=True, exist_ok=True)
        names = {"video": "video" + files["video"].suffix.lower(),
                 "thumbnail": "thumbnail.jpg",
                 "metadata": "metadata.json"} if "video" in files else {
                 "thumbnail": "thumbnail.jpg", "metadata": "metadata.json"}
        for kind, src in files.items():
            shutil.move(str(src), str(folder / names[kind]))
        if "metadata" in files:
            (folder / "description.txt").write_text(description_text(info), encoding="utf-8")
        filed += 1
        log(f"filed {folder.name}")
    return filed


def archive_ids(archive: Path) -> set[str]:
    if not archive.exists():
        return set()
    ids = set()
    for line in archive.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            ids.add(parts[1])
    return ids


def studio_helper() -> Path:
    return Path(__file__).with_name("studio_ids.py")


def studio_rows(channel_id: str, port: int, log: Log) -> list[dict]:
    out = Path(tempfile.gettempdir()) / f"studio-{channel_id}.json"
    rc = run_stream([sys.executable, str(studio_helper()), "--channel", channel_id,
                     "--port", str(port), "--out", str(out)], log)
    if rc != 0 or not out.exists():
        log("Studio listing failed; skipping scheduled/private videos")
        return []
    try:
        rows = json.loads(out.read_text(encoding="utf-8"))
    finally:
        out.unlink(missing_ok=True)
    return rows


def export_cookies(port: int, log: Log) -> Path | None:
    out = Path(tempfile.mkdtemp(prefix="ytcookies-")) / "cookies.txt"
    rc = run_stream([sys.executable, str(studio_helper()), "--port", str(port),
                     "--cookies-out", str(out)], log)
    if rc != 0 or not out.exists():
        log("Cookie export failed; scheduled videos cannot be fetched")
        return None
    return out


def browser_helper(browser: str, port: int | None, log: Log) -> bool:
    if os.name != "nt":
        log("scheduled pass needs Windows (browser session helper)")
        return False
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", str(Path(__file__).with_name("browser_debug.ps1")), "-Browser", browser]
    if port:
        cmd += ["-Port", str(port)]
        log(f"launching {browser} with a debug port")
    else:
        cmd += ["-Stop"]
    return run_stream(cmd, log) == 0


def sync_to_drive(local: Path, target: str, transfers: int, log: Log) -> int:
    if not target:
        log("no Drive folder configured; local only")
        return 0
    log(f"rclone copy {local} -> {target}")
    return run_stream(["rclone", "copy", str(local), target,
                       "--ignore-existing", "--transfers", str(transfers),
                       "--checkers", "8", "--drive-chunk-size", "64M",
                       "--stats", "30s", "--stats-one-line",
                       "--exclude", "*.log", "--exclude", ".staging/**"], log)


def scheduled_pass(settings: dict, cfg: dict, args, root: Path, staging: Path,
                   archive: Path, log: Log, summary: dict) -> None:
    channel_id = settings["channel_id"]
    if not channel_id:
        log("no channel id, so the Studio pass cannot run")
        return
    port = int(cfg.get("browserDebugPort", 9223))
    browser = settings.get("browser") or cfg.get("browser", "brave")
    launched = False
    cookies = Path(args.cookies).expanduser() if args.cookies else None

    if not cookies:
        launched = browser_helper(browser, port, log)
        if not launched:
            log("could not open a debuggable browser session; private pass skipped")
            return
        cookies = export_cookies(port, log)

    rows = studio_rows(channel_id, port, log) if launched else []
    if not rows and launched:
        log("no Studio rows read; nothing to compare")

    have = archive_ids(archive)
    pending = [row for row in rows
               if row.get("id") and row["id"] not in have
               and row.get("visibility") in ("Scheduled", "Private", "Unlisted")]
    for row in pending:
        log(f"{row['visibility']}: {row['id']} {str(row.get('title', ''))[:60]}")

    if pending and cookies:
        before = len(archive_ids(archive))
        rc = yt_targets([f"https://www.youtube.com/watch?v={row['id']}" for row in pending],
                        staging / "scheduled", archive, settings["quality"], log, cookies)
        summary["downloads"] += max(0, len(archive_ids(archive)) - before)
        summary["rc"] += rc
        summary["filed"] += promote(staging / "scheduled", root, log)

    if launched:
        browser_helper(browser, None, log)
    if cookies and not args.cookies and not args.keep_cookies:
        shutil.rmtree(cookies.parent, ignore_errors=True)


def backup_channel(slug: str, channel: dict, cfg: dict, args, log: Log) -> dict:
    settings = channel_settings(cfg, slug, channel)
    settings["browser"] = channel.get("browser") or cfg.get("browser", "brave")
    root = Path(cfg["localRoot"]).expanduser() / slug
    staging = root / ".staging"
    archive = root / "archive.txt"
    for kind in ("long", "shorts"):
        (root / kind).mkdir(parents=True, exist_ok=True)

    resolve_channel_id(settings, log)
    channel_id = settings["channel_id"]
    base = f"https://www.youtube.com/channel/{channel_id}"
    summary = {"channel": slug, "name": settings["name"], "channelId": channel_id,
               "driveFolder": settings["drive_folder"], "started": now(),
               "downloads": 0, "filed": 0, "rc": 0}
    log(f"backup {slug} ({settings['name']}) -> {settings['drive_folder'] or 'local only'}")

    before = len(archive_ids(archive))
    summary["rc"] += yt_targets([f"{base}/videos", f"{base}/shorts"],
                                staging / "public", archive, settings["quality"], log)
    summary["downloads"] += max(0, len(archive_ids(archive)) - before)
    summary["filed"] += promote(staging / "public", root, log)

    if settings["include_private"] and not args.no_scheduled:
        scheduled_pass(settings, cfg, args, root, staging, archive, log, summary)

    if args.no_upload:
        log("upload skipped (--no-upload)")
    else:
        summary["rc"] += sync_to_drive(root, settings["drive_folder"],
                                       int(cfg.get("transfers", 2)), log)

    for kind in ("long", "shorts"):
        summary[kind] = len([p for p in (root / kind).iterdir() if p.is_dir()])
    summary["finished"] = now()
    (root / "backup-report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    log(f"done {slug}: {summary['long']} long, {summary['shorts']} shorts, "
        f"{summary['downloads']} downloaded, rc={summary['rc']}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", help="channel slug from the config (default: every channel)")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--list", action="store_true", help="list configured channels")
    parser.add_argument("--resolve", action="store_true",
                        help="resolve and print channel ids for every configured channel")
    parser.add_argument("--no-upload", action="store_true", help="skip the rclone copy")
    parser.add_argument("--no-scheduled", action="store_true", help="skip the Studio/private pass")
    parser.add_argument("--cookies", help="cookies.txt to use instead of a browser session")
    parser.add_argument("--keep-cookies", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    cfg = load_config(config_path)

    if args.list:
        for slug, chan in cfg["channels"].items():
            settings = channel_settings(cfg, slug, chan)
            print(f"{slug:24} {settings['channel_id'] or '(resolves at run time)':26} "
                  f"{settings['name']:24} {settings['drive_folder'] or 'local only'}")
        return 0

    selected = cfg["channels"]
    if args.channel:
        if args.channel not in selected:
            raise SystemExit(f"unknown channel '{args.channel}'; use --list")
        selected = {args.channel: selected[args.channel]}
    if not selected:
        raise SystemExit("no channels configured")

    log = Log(Path(cfg["localRoot"]).expanduser() / "backup.log")

    if args.resolve:
        for slug, chan in selected.items():
            settings = channel_settings(cfg, slug, chan)
            print(f"{slug}: {resolve_channel_id(settings, log)}")
        return 0

    check_tools(log, need_rclone=not args.no_upload
                and any(channel_settings(cfg, s, c)["drive_folder"] for s, c in selected.items()))

    worst = 0
    for slug, channel in selected.items():
        worst = max(worst, int(backup_channel(slug, channel, cfg, args, log).get("rc") or 0))
    return worst


if __name__ == "__main__":
    sys.exit(main())



