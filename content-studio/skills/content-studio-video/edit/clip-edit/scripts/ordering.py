"""Keep a draft's mixed-device camera clips in capture-time order."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from common import channel_root, select_channels
import draftlayout


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv"}
FIELDS = ("order", "new_name", "original_name", "start_local", "end_local",
          "duration_seconds", "device", "time_estimated")
PREFIX = re.compile(r"^\d{3,} - (.+)$")
ANDROID = re.compile(r"^VID(\d{14})", re.IGNORECASE)
IPHONE = re.compile(r"^IMG_(\d+)", re.IGNORECASE)


class OrderError(RuntimeError):
    pass


def original_name(name: str) -> str:
    match = PREFIX.match(name)
    return match.group(1) if match else name


def analysis_folder(root: Path, name: str) -> Path:
    """Carry an older numbered analysis folder forward after camera renames."""
    stable = root / original_name(name)
    if stable.exists() or not root.is_dir():
        return stable
    matches = [p for p in root.iterdir() if p.is_dir()
               and original_name(p.name).casefold() == stable.name.casefold()]
    if len(matches) > 1:
        raise OrderError(f"multiple analysis folders for {stable.name}")
    if matches:
        os.replace(matches[0], stable)
    return stable


def camera_files(draft: Path) -> list[Path]:
    root = draftlayout.camera_root(draft)
    return sorted((p for p in root.iterdir() if p.is_file()
                   and p.suffix.lower() in VIDEO_EXTENSIONS
                   and p.name.lower() != "video.mp4"), key=lambda p: p.name.casefold())


def read_timeline(draft: Path) -> list[dict]:
    path = draftlayout.timeline_path(draft)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise OrderError(f"timeline has missing columns: {path}")
        rows = list(reader)
    if len({r["new_name"].casefold() for r in rows}) != len(rows):
        raise OrderError("timeline contains duplicate names")
    return rows


def timeline_current(files: list[Path], rows: list[dict]) -> bool:
    if not rows or len(files) != len(rows) or {
            p.name.casefold() for p in files} != {r["new_name"].casefold() for r in rows}:
        return False
    # A hand-edited timeline with stale numbering must also be rebuilt.
    try:
        ordered = sorted(rows, key=lambda row: int(row["order"]))
    except ValueError:
        return False
    return all(int(row["order"]) == index and
               row["new_name"] == f"{index:0{max(3, len(str(len(rows))))}d} - {row['original_name']}"
               for index, row in enumerate(ordered, 1))


def probe(path: Path) -> tuple[float, datetime | None]:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration:format_tags=creation_time:stream_tags=creation_time",
                             "-of", "json", str(path)], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise OrderError(f"ffprobe failed for {path.name}: {result.stderr.strip()[-300:]}")
    data = json.loads(result.stdout)
    created = data.get("format", {}).get("tags", {}).get("creation_time")
    if not created:
        created = next((s.get("tags", {}).get("creation_time")
                        for s in data.get("streams", []) if s.get("tags", {}).get("creation_time")), None)
    timestamp = None
    if created:
        timestamp = datetime.fromisoformat(created.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
    return float(data.get("format", {}).get("duration") or 0), timestamp


def parse_offset(text: str) -> timedelta:
    match = re.fullmatch(r"([+-])(\d{2}):(\d{2})", text)
    if not match or int(match.group(2)) > 14 or int(match.group(3)) >= 60 or \
            (int(match.group(2)) == 14 and int(match.group(3)) > 0):
        raise OrderError("--utc-offset must look like +04:00 or -05:30")
    minutes = int(match.group(2)) * 60 + int(match.group(3))
    return timedelta(minutes=minutes if match.group(1) == "+" else -minutes)


def snap_offset(delta: timedelta) -> timedelta:
    """Camera metadata can differ by seconds; timezones move in 15-minute steps."""
    minutes = round(delta.total_seconds() / 900) * 15
    if abs(minutes) > 14 * 60:
        raise OrderError("could not infer a plausible camera timezone offset")
    return timedelta(minutes=minutes)


def infer_offset(files: list[Path], prior: list[dict], override: str | None) -> timedelta:
    if override:
        return parse_offset(override)
    by_name = {p.name.casefold(): p for p in files}
    for row in prior:
        if row["device"].startswith("iPhone") and row["time_estimated"].lower() == "no":
            path = by_name.get(row["new_name"].casefold())
            if path:
                _, created = probe(path)
                if created:
                    local = datetime.fromisoformat(row["start_local"])
                    return snap_offset(local - created.replace(tzinfo=None))
    for path in files:
        match = ANDROID.match(original_name(path.name))
        if match:
            _, created = probe(path)
            if created:
                local = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
                return snap_offset(local - created.replace(tzinfo=None))
    raise OrderError("cannot infer camera timezone; pass --utc-offset (for example +04:00)")


def estimated_from_sequence(name: str, rows: list[dict]) -> datetime | None:
    match = IPHONE.match(name)
    if not match:
        return None
    number = int(match.group(1))
    neighbors = []
    for row in rows:
        other = IPHONE.match(row["original_name"])
        if other:
            neighbors.append((int(other.group(1)), datetime.fromisoformat(row["start_local"])))
    if not neighbors:
        return None
    before = max((x for x in neighbors if x[0] < number), default=None, key=lambda x: x[0])
    after = min((x for x in neighbors if x[0] > number), default=None, key=lambda x: x[0])
    if before and after:
        share = (number - before[0]) / (after[0] - before[0])
        return before[1] + (after[1] - before[1]) * share
    neighbor = before or after
    return neighbor[1] + timedelta(minutes=number - neighbor[0])


def new_row(path: Path, offset: timedelta, prior: list[dict]) -> dict:
    name = original_name(path.name)
    duration, created = probe(path)
    android = ANDROID.match(name)
    if android:
        start = datetime.strptime(android.group(1), "%Y%m%d%H%M%S")
        device, estimated = "Android", "no"
    elif created:
        start = (created.astimezone(timezone.utc) + offset).replace(tzinfo=None)
        device, estimated = ("iPhone" if IPHONE.match(name) else "Camera"), "no"
    else:
        start = estimated_from_sequence(name, prior)
        if start is None:
            start = (datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
                     + offset).replace(tzinfo=None)
        device, estimated = ("iPhone" if IPHONE.match(name) else "Camera"), "yes"
    end = start + timedelta(seconds=duration)
    return {"order": "", "new_name": path.name, "original_name": name,
            "start_local": start.strftime("%Y-%m-%d %H:%M:%S"),
            "end_local": end.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": f"{duration:.3f}".rstrip("0").rstrip("."),
            "device": device, "time_estimated": estimated}


def planned_rows(files: list[Path], prior: list[dict], offset: timedelta,
                 refresh: bool = False) -> tuple[list[dict], list[tuple[Path, Path]], int]:
    old = {r["new_name"].casefold(): r for r in prior}
    old_by_original = {r["original_name"].casefold(): r for r in prior}
    entries = []
    additions = 0
    for path in files:
        row = None if refresh else old.get(path.name.casefold())
        if row is None and not refresh:
            row = old_by_original.get(original_name(path.name).casefold())
        if row is None:
            row = new_row(path, offset, prior)
            additions += 1
        entries.append((path, dict(row)))
    if len({original_name(p.name).casefold() for p, _ in entries}) != len(entries):
        raise OrderError("duplicate camera basenames cannot be numbered safely")
    entries.sort(key=lambda item: (item[1]["start_local"],
                                   int(item[1]["order"] or 0), item[1]["original_name"].casefold()))
    width = max(3, len(str(len(entries))))
    renames = []
    rows = []
    for index, (path, row) in enumerate(entries, 1):
        target = path.with_name(f"{index:0{width}d} - {row['original_name']}")
        row["order"] = str(index)
        row["new_name"] = target.name
        rows.append(row)
        if path.name != target.name:
            renames.append((path, target))
    return rows, renames, additions


def apply_order(draft: Path, rows: list[dict], renames: list[tuple[Path, Path]]) -> None:
    """Stage all names before assigning numbers, so insertion cannot collide."""
    root = draftlayout.camera_root(draft).resolve()
    draftlayout.internal_dir(draft).mkdir(parents=True, exist_ok=True)
    moving = {source.resolve() for source, _ in renames}
    for source, target in renames:
        if source.resolve().parent != root or target.resolve().parent != root:
            raise OrderError("rename target escaped the draft folder")
        if target.exists() and target.resolve() not in moving:
            raise OrderError(f"rename would overwrite a file: {target.name}")
    token = uuid.uuid4().hex
    staged = [(source, target, root / f".order-{token}-{index}.tmp")
              for index, (source, target) in enumerate(renames)]
    current = {}
    try:
        for source, _, temporary in staged:
            os.replace(source, temporary)
            current[source] = temporary
        for source, target, temporary in staged:
            os.replace(temporary, target)
            current[source] = target
        temp_csv = draftlayout.internal_dir(draft) / f".order-{token}.csv"
        with temp_csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_csv, draftlayout.timeline_path(draft))
    except Exception:
        # Restore original names through a second temporary phase so target
        # filenames cannot block rollback after partial assignment.
        recovery = []
        for index, (source, _, _) in enumerate(staged):
            location = current.get(source)
            if location and location.exists():
                temporary = root / f".recover-{token}-{index}.tmp"
                os.replace(location, temporary)
                recovery.append((temporary, source))
        for temporary, source in recovery:
            os.replace(temporary, source)
        (draftlayout.internal_dir(draft) / f".order-{token}.csv").unlink(missing_ok=True)
        raise


def ensure_current(draft: Path, log, *, utc_offset: str | None = None,
                   refresh: bool = False, dry_run: bool = False) -> list[dict]:
    files = camera_files(draft)
    if not files:
        raise OrderError(f"no camera videos in {draft}")
    prior = read_timeline(draft)
    if timeline_current(files, prior) and not refresh:
        return sorted(prior, key=lambda row: int(row["order"]))
    offset = infer_offset(files, prior, utc_offset)
    rows, renames, additions = planned_rows(files, prior, offset, refresh)
    log(f"{draft.name}: {len(rows)} clips; {additions} new; {len(renames)} renamed; "
        f"UTC offset {offset.total_seconds() / 3600:+g}h")
    if dry_run:
        for source, target in renames[:12]:
            log(f"  {source.name} -> {target.name}")
        if len(renames) > 12:
            log(f"  ... {len(renames) - 12} more")
        return rows
    apply_order(draft, rows, renames)
    return rows


def run(cfg: dict, args, log) -> int:
    try:
        slug, _ = select_channels(cfg, args.channel)[0]
        if not args.draft or Path(args.draft).name != args.draft:
            raise OrderError("pass a draft folder name with --draft")
        draft = channel_root(cfg, slug) / "drafts" / args.draft
        if not draft.is_dir():
            raise OrderError(f"draft not found: {draft}")
        rows = ensure_current(draft, log, utc_offset=args.utc_offset,
                              refresh=args.refresh, dry_run=args.dry_run)
        log(f"{draft.name}: order {'previewed' if args.dry_run else 'current'} ({len(rows)} clips)")
        return 0
    except (OrderError, OSError, ValueError) as exc:
        log(f"order: {exc}")
        return 1
