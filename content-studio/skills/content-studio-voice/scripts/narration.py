#!/usr/bin/env python3
"""Pure narration planning helpers: validation, hashing, reuse, timeline fitting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_text(text: str) -> str:
    """Stable short hash used to detect script edits between renders."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    """Write JSON atomically so an interrupted render cannot corrupt the manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def validate_script(spec: dict) -> list[dict]:
    """Return normalized sections or raise ValueError with a precise reason."""
    raw = spec.get("segments")
    if not isinstance(raw, list) or not raw:
        raise ValueError("script must contain a non-empty segments list")
    seen: set[str] = set()
    segments: list[dict] = []
    previous_start = -1.0
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"segment {index} must be an object")
        segment_id = str(item.get("id", "")).strip()
        text = str(item.get("text", "")).strip()
        if not segment_id:
            raise ValueError(f"segment {index} has no id")
        if segment_id in seen:
            raise ValueError(f"duplicate segment id: {segment_id}")
        if not text:
            raise ValueError(f"segment {segment_id} has no text")
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"segment {segment_id} needs numeric start and end") from error
        if start < 0:
            raise ValueError(f"segment {segment_id} starts before zero")
        if end <= start:
            raise ValueError(f"segment {segment_id} ends before it starts")
        if start < previous_start:
            raise ValueError("segments must be ordered by start time")
        seen.add(segment_id)
        previous_start = start
        segments.append(
            {"id": segment_id, "start": start, "end": end, "text": text}
        )
    return segments


def is_reusable(
    entry: dict | None, text: str, params: dict, audio_path: Path
) -> bool:
    """A segment can be reused only when text, settings, and audio all match."""
    if not entry or not audio_path.is_file():
        return False
    return entry.get("text_hash") == sha256_text(text) and entry.get("params") == params


def fit_timeline(
    segments: list[dict],
    durations: dict[str, float],
    video_seconds: float,
    max_tempo: float = 1.12,
    gap: float = 0.3,
) -> list[dict]:
    """Place sections at their timestamps with bounded, reported tempo changes."""
    if max_tempo < 1.0:
        raise ValueError("max_tempo must be at least 1.0")
    if gap < 0:
        raise ValueError("gap must not be negative")
    placed: list[dict] = []
    cursor = 0.0
    for index, segment in enumerate(segments):
        natural = float(durations[segment["id"]])
        start = max(segment["start"], cursor)
        next_start = (
            segments[index + 1]["start"]
            if index + 1 < len(segments)
            else video_seconds
        )
        available = max(next_start - start - gap, 0.1)
        tempo = min(natural / available, max_tempo) if natural > available else 1.0
        duration = natural / tempo
        end = start + duration
        overrun = max(0.0, end - (next_start - gap))
        placed.append(
            {
                "id": segment["id"],
                "user_slot": [segment["start"], segment["end"]],
                "natural_seconds": round(natural, 3),
                "tempo": round(tempo, 4),
                "start": round(start, 3),
                "end": round(end, 3),
                "slot_seconds": round(segment["end"] - segment["start"], 3),
                "overrun_seconds": round(overrun, 3),
                "needs_review": bool(overrun > 0.05),
            }
        )
        cursor = end + gap
    return placed


def timeline_summary(placed: list[dict], video_seconds: float) -> dict:
    if not placed:
        raise ValueError("no placed segments")
    end = max(item["end"] for item in placed)
    return {
        "video_seconds": round(video_seconds, 3),
        "narration_seconds": round(end, 3),
        "mix_seconds": round(max(video_seconds, end + 0.4), 3),
        "overrun_total": round(sum(item["overrun_seconds"] for item in placed), 3),
        "review": [
            {
                "id": item["id"],
                "natural_seconds": item["natural_seconds"],
                "tempo": item["tempo"],
                "overrun_seconds": item["overrun_seconds"],
            }
            for item in placed
            if item["needs_review"]
        ],
    }
