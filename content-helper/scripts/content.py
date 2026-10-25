#!/usr/bin/env python3
"""content-helper: back up channels, manage drafts, prune locals, add intros, read analytics."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import drive
import intro as intro_mod
import studio
import ytdlp
from common import (DEFAULT_CONFIG, Log, archive_ids, channel_root, channel_settings,
                    human_size, load_config, now, resolve_path, select_channels,
                    which_tool, write_json)

LAYOUT = ("long", "shorts", "drafts", "assets")


def prepare(cfg: dict, slug: str) -> Path:
    root = channel_root(cfg, slug)
    for name in LAYOUT:
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def needs_upload(cfg: dict, args) -> bool:
    return not args.no_upload


def backup(cfg: dict, args, log: Log) -> int:
    if not args.no_upload and not drive.available():
        log("MISSING rclone: winget install Rclone.Rclone")
        return 1
    rc = 0
    for slug, raw in select_channels(cfg, args.channel):
        settings = channel_settings(cfg, slug, raw)
        root = prepare(cfg, slug)
        staging = root / ".staging"
        archive = root / "archive.txt"
        ytdlp.resolve_channel_id(settings, log)
        base = f"https://www.youtube.com/channel/{settings['channel_id']}"
        log(f"backup {slug} ({settings['name']})")

        before = len(archive_ids(archive))
        rc |= ytdlp.download([f"{base}/videos", f"{base}/shorts"],
                             staging / "public", archive, settings["quality"], log)
        fetched = max(0, len(archive_ids(archive)) - before)
        filed = ytdlp.promote(staging / "public", root, log)

        if settings["include_private"] and not args.no_scheduled:
            priv_rc, priv_fetched, priv_filed = private_pass(settings, cfg, args, root,
                                                            staging, archive, log)
            rc |= priv_rc
            fetched += priv_fetched
            filed += priv_filed

        if not args.no_upload:
            rc |= drive.copy(root / "long", drive.join(settings["drive_folder"], "long"),
                             log, cfg["transfers"], immutable=True)
            rc |= drive.copy(root / "shorts", drive.join(settings["drive_folder"], "shorts"),
                             log, cfg["transfers"], immutable=True)

        report = {"channel": slug, "name": settings["name"],
                  "channelId": settings["channel_id"],
                  "driveFolder": settings["drive_folder"], "started": now(),
                  "downloads": fetched, "filed": filed, "rc": rc,
                  "long": len([p for p in (root / "long").iterdir() if p.is_dir()]),
                  "shorts": len([p for p in (root / "shorts").iterdir() if p.is_dir()])}
        report["finished"] = now()
        write_json(root / "backup-report.json", report)
        log(f"backup {slug}: +{fetched} downloaded, {report['long']} long, "
            f"{report['shorts']} shorts, rc={rc}")
    return rc


def private_pass(settings: dict, cfg: dict, args, root: Path, staging: Path,
                 archive: Path, log: Log) -> tuple[int, int, int]:
    port = int(cfg["browserDebugPort"])
    browser = settings["browser"]
    launched = False
    cookies = Path(args.cookies).expanduser() if getattr(args, "cookies", None) else None
    temp_dir = None
    if not cookies:
        launched = studio.launch(browser, port, log)
        if not launched:
            log("could not open a debuggable browser; private pass skipped")
            return 0, 0, 0
        cookies, temp_dir = studio.cookies_to_temp(port)
        if not cookies:
            log("cookie export failed; private pass skipped")
            if launched:
                studio.stop(browser, log)
            return 0, 0, 0

    rows = studio.rows(settings["channel_id"], port, log) if launched else []
    have = archive_ids(archive)
    pending = [r for r in rows if r.get("id") and r["id"] not in have
               and r.get("visibility") in ("Scheduled", "Private", "Unlisted")]
    for row in pending:
        log(f"{row['visibility']}: {row['id']} {str(row.get('title', ''))[:60]}")

    fetched = filed = rc = 0
    if pending:
        before = len(archive_ids(archive))
        rc = ytdlp.download([f"https://www.youtube.com/watch?v={r['id']}" for r in pending],
                            staging / "scheduled", archive, settings["quality"], log, cookies)
        fetched = max(0, len(archive_ids(archive)) - before)
        filed = ytdlp.promote(staging / "scheduled", root, log)

    if launched:
        studio.stop(browser, log)
    if temp_dir:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return rc, fetched, filed


def sync(cfg: dict, args, log: Log) -> int:
    if not drive.available():
        log("MISSING rclone: winget install Rclone.Rclone")
        return 1
    rc = 0
    for slug, raw in select_channels(cfg, args.channel):
        settings = channel_settings(cfg, slug, raw)
        root = prepare(cfg, slug)
        remote = settings["drive_folder"]
        if not remote:
            log(f"{slug}: no driveFolder configured")
            continue
        log(f"sync {slug} <-> {remote}")
        if args.pull:
            rc |= drive.pull(drive.join(remote, "drafts"), root / "drafts", log, cfg["transfers"])
            rc |= drive.pull(drive.join(remote, "assets"), root / "assets", log, cfg["transfers"])
            continue
        rc |= drive.copy(root / "long", drive.join(remote, "long"), log,
                         cfg["transfers"], immutable=True)
        rc |= drive.copy(root / "shorts", drive.join(remote, "shorts"), log,
                         cfg["transfers"], immutable=True)
        rc |= drive.copy(root / "drafts", drive.join(remote, "drafts"), log,
                         cfg["transfers"], immutable=False)
        rc |= drive.copy(root / "assets", drive.join(remote, "assets"), log,
                         cfg["transfers"], immutable=False)
        archive = root / "archive.txt"
        if archive.exists():
            rc |= drive.copy_file(archive, drive.join(remote, "archive.txt"), log)
        log(f"sync {slug} done rc={rc}; Drive holds "
            f"{drive.total_size(drive.join(remote, 'long'))} long + "
            f"{drive.total_size(drive.join(remote, 'shorts'))} shorts")
    return rc


def draft(cfg: dict, args, log: Log) -> int:
    slug, raw = select_channels(cfg, args.channel)[0]
    settings = channel_settings(cfg, slug, raw)
    root = prepare(cfg, slug)
    drafts = root / "drafts"
    if args.action == "list":
        for path in sorted(drafts.iterdir()) if drafts.exists() else []:
            if not path.is_dir():
                continue
            video = path / "video.mp4"
            size = human_size(video.stat().st_size) if video.exists() else "no video yet"
            log(f"{path.name:40} {size}")
        return 0

    name = (args.name or "").strip()
    if not name:
        raise SystemExit("--name is required for 'draft new'")
    folder = drafts / name
    if folder.exists() and not args.force:
        raise SystemExit(f"draft already exists: {folder}")
    (folder / "original-videos").mkdir(parents=True, exist_ok=True)
    (folder / "title.txt").write_text(name + "\n", encoding="utf-8")
    if not (folder / "description.txt").exists():
        (folder / "description.txt").write_text(
            f"# {settings['name']}\n\nWrite the description here.\n\n#tags\n", encoding="utf-8")
    write_json(folder / "draft.json", {"name": name, "channel": slug, "created": now(),
                                       "status": "draft"})
    log(f"created {folder}")
    return 0


def intro(cfg: dict, args, log: Log) -> int:
    rc = 0
    for slug, raw in select_channels(cfg, args.channel):
        settings = channel_settings(cfg, slug, raw)
        root = prepare(cfg, slug)
        intro_path = resolve_path(root, args.intro) if args.intro else resolve_path(root, settings["intro"])
        if not intro_path.exists():
            log(f"intro clip not found: {intro_path}")
            return 1
        targets = []
        if args.draft:
            targets = [root / "drafts" / args.draft]
        elif args.all:
            targets = sorted(p for p in (root / "drafts").iterdir() if p.is_dir())
        else:
            raise SystemExit("pass --draft NAME or --all")
        for folder in targets:
            video = folder / "video.mp4"
            if not video.exists():
                log(f"skip {folder.name}: no video.mp4")
                continue
            rc |= intro_mod.apply(video, intro_path, folder, args.force, log)
    return rc


def prune(cfg: dict, args, log: Log) -> int:
    if not drive.available() and not args.dry_run:
        log("MISSING rclone: needed to verify the Drive copy before deleting")
        return 1
    slug, raw = select_channels(cfg, args.channel)[0]
    settings = channel_settings(cfg, slug, raw)
    root = prepare(cfg, slug)
    remote = settings["drive_folder"]
    candidates: list[tuple[str, Path]] = []
    kinds = ["long", "shorts"] if args.include_shorts else ["long"]
    for kind in kinds:
        for folder in (root / kind).iterdir():
            if folder.is_dir():
                candidates.append((kind, folder))
    candidates.sort(key=lambda item: item[1].name, reverse=args.newest)
    if args.keep:
        candidates = [c for c in candidates if c[1].name >= args.keep]
    chosen = candidates[:args.count]
    if not chosen:
        log("nothing to prune")
        return 0
    freed = 0
    removed = 0
    for kind, folder in chosen:
        target = drive.join(remote, kind, folder.name)
        if args.dry_run:
            log(f"would delete {kind}/{folder.name} (after checking {target})")
            continue
        if not drive.folder_present(target, folder, log):
            log(f"kept {kind}/{folder.name}: Drive copy not verified")
            continue
        size = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
        shutil.rmtree(folder)
        freed += size
        removed += 1
        log(f"deleted local {kind}/{folder.name}")
    verb = "would prune" if args.dry_run else "pruned"
    log(f"{verb} {len(chosen) if args.dry_run else removed} item(s), "
        f"freed {human_size(freed)}; Drive untouched at {remote}; "
        f"archive.txt entries kept so backup will not re-download them")
    return 0


def listing(cfg: dict, log: Log) -> int:
    for slug, raw in cfg.get("channels", {}).items():
        settings = channel_settings(cfg, slug, raw)
        root = channel_root(cfg, slug)
        drafts = len([p for p in (root / "drafts").iterdir() if p.is_dir()]) if (root / "drafts").exists() else 0
        print(f"{slug:20} {settings['name']:24} {settings['drive_folder'] or '-':48} "
              f"local={root} drafts={drafts}")
    return 0


def doctor(cfg: dict, log: Log) -> int:
    import importlib.util

    checks = [("python yt-dlp", bool(importlib.util.find_spec("yt_dlp"))),
              ("python websocket-client", bool(importlib.util.find_spec("websocket"))),
              ("ffmpeg", which_tool("ffmpeg")), ("ffprobe", which_tool("ffprobe")),
              ("node", which_tool("node")), ("rclone", drive.available())]
    bad = 0
    for name, ok in checks:
        log(f"{'ok  ' if ok else 'MISS'} {name}")
        bad += 0 if ok else 1
    if drive.available():
        result = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True)
        log(f"rclone remotes: {' '.join(result.stdout.split()) or 'none'}")
    log(f"workspace: {cfg['workspace']}")
    return 1 if bad else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--channel")
    sub = parser.add_subparsers(dest="command", required=True)
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--config", default=argparse.SUPPRESS)
    shared.add_argument("--channel", default=argparse.SUPPRESS)

    sub.add_parser("list", parents=[shared], help="show channels and local roots")
    sub.add_parser("doctor", parents=[shared], help="check tools and remotes")

    p = sub.add_parser("backup", parents=[shared],
                       help="download public/private/scheduled videos to Drive")
    p.add_argument("--no-upload", action="store_true")
    p.add_argument("--no-scheduled", action="store_true")
    p.add_argument("--cookies")

    p = sub.add_parser("sync", parents=[shared],
                       help="push drafts/assets and archive to Drive, or pull drafts")
    p.add_argument("--pull", action="store_true", help="copy Drive drafts/assets down")

    p = sub.add_parser("draft", parents=[shared], help="scaffold or list drafts")
    p.add_argument("action", choices=["new", "list"])
    p.add_argument("--name")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("intro", parents=[shared],
                       help="prepend the channel intro to a draft video")
    p.add_argument("--draft")
    p.add_argument("--all", action="store_true")
    p.add_argument("--intro", help="override the intro clip path")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("prune", parents=[shared],
                       help="delete old published videos locally (Drive untouched)")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--newest", action="store_true")
    p.add_argument("--keep", help="only consider folders whose name sorts at/after this date")
    p.add_argument("--include-shorts", action="store_true")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("analytics", parents=[shared], help="retention and performance report")
    p.add_argument("--provider", choices=["api", "studio"], default=None)
    p.add_argument("--last", type=int, default=5)
    p.add_argument("--video")
    p.add_argument("--out")

    args = parser.parse_args()
    cfg = load_config(Path(args.config))
    log = Log(Path(cfg["workspace"]).expanduser() / "content-helper.log")

    if args.command == "list":
        return listing(cfg, log)
    if args.command == "doctor":
        return doctor(cfg, log)
    if args.command == "backup":
        return backup(cfg, args, log)
    if args.command == "sync":
        return sync(cfg, args, log)
    if args.command == "draft":
        return draft(cfg, args, log)
    if args.command == "intro":
        return intro(cfg, args, log)
    if args.command == "prune":
        return prune(cfg, args, log)
    if args.command == "analytics":
        import analytics

        return analytics.run(cfg, args, log)
    return 1


if __name__ == "__main__":
    sys.exit(main())
