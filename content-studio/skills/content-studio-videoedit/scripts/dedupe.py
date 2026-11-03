"""Quarantine identical camera clips and flag near-duplicate shots.

Exact copies are detected from file contents, not filenames, and moved to
``draft/analysis/duplicates``. Near-duplicates are only reported for review;
setting ``remove=yes`` in the review CSV quarantines them on the next scan.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import draftlayout
import ordering


CACHE_VERSION = 1
FRAME_WIDTH = 16
FRAME_HEIGHT = 16
FRAME_BYTES = FRAME_WIDTH * FRAME_HEIGHT
SAMPLE_POINTS = (0.1, 0.3, 0.5, 0.7, 0.9)
# Mean absolute grayscale difference across sampled 16x16 frames. Near
# duplicates are review-only, so a generous threshold is safer than missing
# a repeated take.
NEAR_DIFFERENCE = 0.10
DURATION_TOLERANCE = 0.02
DURATION_FLOOR = 0.5
ASPECT_TOLERANCE = 0.01
REVIEW_FIELDS = ("group", "keep", "duplicate", "duration_seconds", "width",
                 "height", "difference", "remove", "notes")
APPROVED = {"yes", "y", "true", "1"}


class DedupeError(RuntimeError):
    pass


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _signature(path: Path) -> dict:
    info = path.stat()
    return {"size": info.st_size, "mtime_ns": info.st_mtime_ns}


def _record(path: Path, records: dict, cache: dict) -> dict:
    if path.name in records:
        return records[path.name]
    signature = _signature(path)
    old = cache.get(path.name)
    if old and old.get("size") == signature["size"] and \
            old.get("mtime_ns") == signature["mtime_ns"]:
        entry = dict(old)
    else:
        entry = signature
    records[path.name] = entry
    return entry


def _sha256(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha_for(path: Path, records: dict, cache: dict) -> str:
    record = _record(path, records, cache)
    if not record.get("sha256"):
        record["sha256"] = _sha256(path)
    return record["sha256"]


def _probe_info(path: Path) -> dict | None:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
         str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        return None
    try:
        data = json.loads(result.stdout)
    except ValueError:
        return None
    video = next((stream for stream in data.get("streams", [])
                  if stream.get("codec_type") == "video"
                  and not stream.get("disposition", {}).get("attached_pic")), None)
    if not video:
        return None
    try:
        duration = float(data.get("format", {}).get("duration")
                         or video.get("duration") or 0)
        width = int(video.get("width") or 0)
        height = int(video.get("height") or 0)
    except (TypeError, ValueError):
        return None
    if duration <= 0 or width <= 0 or height <= 0:
        return None
    rotation = 0
    for item in video.get("side_data_list", []):
        if "rotation" in item:
            try:
                rotation = int(float(item["rotation"]))
            except (TypeError, ValueError):
                rotation = 0
            break
    if not rotation:
        try:
            rotation = int(float(video.get("tags", {}).get("rotate", 0)))
        except (TypeError, ValueError):
            rotation = 0
    if abs(rotation) % 180 == 90:
        width, height = height, width
    return {"duration": duration, "width": width, "height": height}


def _info_for(path: Path, records: dict, cache: dict) -> dict | None:
    record = _record(path, records, cache)
    if "info" in record:
        return record["info"]
    info = _probe_info(path)
    record["info"] = info
    return info


def _sample_frames(path: Path, duration: float) -> list[bytes] | None:
    if duration < 0.2:
        return None
    frames = []
    for point in SAMPLE_POINTS:
        stamp = max(0.0, min(duration - 0.01, duration * point))
        result = subprocess.run(
            ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-ss", f"{stamp:.3f}", "-i", str(path), "-map", "0:v:0",
             "-frames:v", "1", "-an", "-sn",
             "-vf", f"scale={FRAME_WIDTH}:{FRAME_HEIGHT}:flags=area,format=gray",
             "-f", "rawvideo", "-"],
            capture_output=True)
        if result.returncode or len(result.stdout) != FRAME_BYTES:
            return None
        frames.append(result.stdout)
    return frames


def _frames_for(path: Path, info: dict, records: dict, cache: dict) -> list[bytes] | None:
    record = _record(path, records, cache)
    if "frames" in record:
        cached = record["frames"]
        return [bytes.fromhex(value) for value in cached] if cached else None
    frames = _sample_frames(path, info["duration"])
    record["frames"] = [frame.hex() for frame in frames] if frames else None
    return frames


def _difference(first: list[bytes], second: list[bytes]) -> float:
    if len(first) != len(second) or not first:
        return 1.0
    total = 0.0
    for left, right in zip(first, second):
        total += sum(abs(a - b) for a, b in zip(left, right)) / (FRAME_BYTES * 255)
    return total / len(first)


def _aspect(info: dict) -> float:
    return info["width"] / info["height"]


def _comparable(first: dict, second: dict) -> bool:
    longer = max(first["duration"], second["duration"])
    if abs(first["duration"] - second["duration"]) > max(DURATION_FLOOR,
                                                          DURATION_TOLERANCE * longer):
        return False
    return abs(_aspect(first) - _aspect(second)) <= ASPECT_TOLERANCE * max(
        _aspect(first), _aspect(second))


def _timeline_ranks(draft: Path) -> dict[str, int]:
    try:
        rows = ordering.read_timeline(draft)
    except ordering.OrderError:
        return {}
    ranks = {}
    for row in rows:
        try:
            rank = int(row.get("order") or 0)
        except (TypeError, ValueError):
            rank = 0
        if not rank:
            rank = 10 ** 9
        for key in (row.get("original_name", ""), row.get("new_name", "")):
            if key:
                ranks[key.casefold()] = rank
    return ranks


def _keep_key(path: Path, ranks: dict[str, int]) -> tuple[int, str]:
    original = ordering.original_name(path.name)
    rank = ranks.get(original.casefold(), ranks.get(path.name.casefold()))
    if rank is None:
        match = re.match(r"^(\d+) - ", path.name)
        rank = int(match.group(1)) if match else 10 ** 9
    return rank, path.name.casefold()


def _destination(folder: Path, name: str) -> Path:
    target = folder / name
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    for index in range(2, 1000):
        candidate = folder / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
    raise DedupeError(f"cannot find a free quarantine name for {name}")


def _quarantine(path: Path, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    target = _destination(folder, path.name)
    os.replace(path, target)
    return target


def _read_review(path: Path) -> dict[tuple[str, str], dict]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = csv.DictReader(fh)
        if not set(REVIEW_FIELDS).issubset(rows.fieldnames or []):
            return {}
        review = {}
        for row in rows:
            keep = (row.get("keep") or "").strip()
            duplicate = (row.get("duplicate") or "").strip()
            if keep and duplicate:
                review[(keep.casefold(), duplicate.casefold())] = row
        return review


def _resolve(name: str, direct: dict[str, str]) -> str:
    seen = set()
    current = name
    while current.casefold() in direct:
        key = current.casefold()
        if key in seen:
            break
        seen.add(key)
        target = direct[key]
        if target.casefold() == key:
            break
        current = target
    return current


def _groups(paths: list[Path], pairs: list[tuple[Path, Path]]) -> list[list[Path]]:
    parent = {path: path for path in paths}

    def find(path: Path) -> Path:
        while parent[path] != path:
            parent[path] = parent[parent[path]]
            path = parent[path]
        return path

    for first, second in pairs:
        left, right = find(first), find(second)
        if left != right:
            parent[right] = left
    grouped: dict[Path, list[Path]] = {}
    for path in paths:
        grouped.setdefault(find(path), []).append(path)
    return [group for group in grouped.values() if len(group) > 1]


def scan(draft: Path, log) -> dict:
    """Move exact duplicates aside and report near-duplicate shots."""
    files = ordering.camera_files(draft)
    report = {"draft": str(draft), "scanned": len(files), "exact": [], "near": [],
              "quarantined": [], "aliases": {}, "review_csv": None, "cache": None}
    if not files:
        return report

    folder = draftlayout.duplicates_dir(draft)
    report_path = folder / "report.json"
    cache_path = folder / "cache.json"
    review_path = folder / "review.csv"
    prior_report = _read_json(report_path)
    prior_review = _read_review(review_path)
    cache = _read_json(cache_path)
    if cache.get("version") != CACHE_VERSION:
        cache = {}
    cache_files = cache.get("files", {}) if isinstance(cache.get("files"), dict) else {}
    records: dict[str, dict] = {}

    direct = {str(key).casefold(): str(value)
              for key, value in (prior_report.get("aliases") or {}).items()}
    ranks = _timeline_ranks(draft)
    quarantined = []

    by_size: dict[int, list[Path]] = {}
    for path in files:
        by_size.setdefault(path.stat().st_size, []).append(path)
    for size, same_size in by_size.items():
        if len(same_size) < 2:
            continue
        by_hash: dict[str, list[Path]] = {}
        for path in same_size:
            try:
                digest = _sha_for(path, records, cache_files)
            except OSError as exc:
                log(f"{draft.name}: cannot hash {path.name}: {exc}")
                continue
            by_hash.setdefault(digest, []).append(path)
        for digest, copies in by_hash.items():
            if len(copies) < 2:
                continue
            copies.sort(key=lambda path: _keep_key(path, ranks))
            keep = copies[0]
            keep_original = ordering.original_name(keep.name)
            removed = []
            for extra in copies[1:]:
                moved = _quarantine(extra, folder)
                extra_original = ordering.original_name(extra.name)
                direct[extra.name.casefold()] = keep_original
                direct[extra_original.casefold()] = keep_original
                relative = moved.relative_to(draft).as_posix()
                removed.append(extra.name)
                quarantined.append({
                    "original_name": extra_original, "filename": extra.name,
                    "kept": keep_original, "reason": "exact", "path": relative,
                    "difference": 0.0, "bytes": size})
                log(f"{draft.name}: duplicate {extra.name} -> {relative} "
                    f"(kept {keep.name})")
            report["exact"].append({
                "sha256": digest, "bytes": size, "kept": keep.name,
                "kept_original": keep_original, "removed": removed,
                "removed_original": [ordering.original_name(name) for name in removed]})

    remaining = ordering.camera_files(draft)
    infos: dict[Path, dict] = {}
    for path in remaining:
        info = _info_for(path, records, cache_files)
        if info:
            infos[path] = info

    frame_values: dict[Path, list[bytes] | None] = {}

    def frames(path: Path) -> list[bytes] | None:
        if path not in frame_values:
            frame_values[path] = _frames_for(path, infos[path], records, cache_files)
        return frame_values[path]

    paths = list(infos)
    candidates = []
    for index, first in enumerate(paths):
        for second in paths[index + 1:]:
            if _comparable(infos[first], infos[second]):
                candidates.append((first, second))

    matching = []
    for first, second in candidates:
        left, right = frames(first), frames(second)
        if left and right and _difference(left, right) <= NEAR_DIFFERENCE:
            matching.append((first, second))

    near_rows = []
    pending_rows = []
    for group_number, group in enumerate(
            sorted(_groups(paths, matching),
                   key=lambda items: min(_keep_key(path, ranks) for path in items)), 1):
        group.sort(key=lambda path: _keep_key(path, ranks))
        keep = group[0]
        keep_original = ordering.original_name(keep.name)
        for duplicate in group[1:]:
            duplicate_original = ordering.original_name(duplicate.name)
            difference = _difference(frames(keep) or [], frames(duplicate) or [])
            previous = prior_review.get((keep_original.casefold(),
                                         duplicate_original.casefold()), {})
            notes = (previous.get("notes") or "").strip()
            approved = (previous.get("remove") or "").strip().lower() in APPROVED
            entry = {"group": group_number, "keep": keep_original,
                     "duplicate": duplicate_original,
                     "difference": round(difference, 4)}
            if approved:
                moved = _quarantine(duplicate, folder)
                direct[duplicate.name.casefold()] = keep_original
                direct[duplicate_original.casefold()] = keep_original
                relative = moved.relative_to(draft).as_posix()
                entry.update({"action": "quarantined", "path": relative})
                quarantined.append({
                    "original_name": duplicate_original, "filename": duplicate.name,
                    "kept": keep_original, "reason": "near-duplicate",
                    "path": relative, "difference": round(difference, 4),
                    "bytes": moved.stat().st_size})
                log(f"{draft.name}: approved near-duplicate {duplicate.name} -> "
                    f"{relative} (kept {keep.name})")
            else:
                entry["action"] = "review"
                info = infos[duplicate]
                pending_rows.append({
                    "group": group_number, "keep": keep_original,
                    "duplicate": duplicate_original,
                    "duration_seconds": round(info["duration"], 3),
                    "width": info["width"], "height": info["height"],
                    "difference": round(difference, 4),
                    "remove": previous.get("remove", ""), "notes": notes})
            near_rows.append(entry)

    aliases = {key: _resolve(value, direct) for key, value in direct.items()}
    # Keep a cumulative audit trail of files still present in quarantine.
    previous_quarantine = prior_report.get("quarantined")
    if isinstance(previous_quarantine, list):
        new_paths = {item.get("path") for item in quarantined}
        historical = [item for item in previous_quarantine
                      if item.get("path") not in new_paths
                      and (draft / str(item.get("path", ""))).is_file()]
        quarantined = historical + quarantined
    report.update({
        "near": near_rows, "quarantined": quarantined, "aliases": aliases,
        "quarantine_folder": folder.relative_to(draft).as_posix(),
        "review_csv": review_path.relative_to(draft).as_posix(),
        "cache": cache_path.relative_to(draft).as_posix(),
        "thresholds": {"near_difference": NEAR_DIFFERENCE,
                       "duration_tolerance": DURATION_TOLERANCE,
                       "aspect_tolerance": ASPECT_TOLERANCE}})

    folder.mkdir(parents=True, exist_ok=True)
    with review_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(pending_rows)
    cache_out = {"version": CACHE_VERSION, "files": {}}
    for path in ordering.camera_files(draft):
        if path.name in records:
            cache_out["files"][path.name] = records[path.name]
    cache_path.write_text(json.dumps(cache_out, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if pending_rows:
        log(f"{draft.name}: {len(pending_rows)} near-duplicate(s) need review in "
            f"{report['review_csv']}")
    return report
