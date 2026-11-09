"""Bind final-render permission to exact human-reviewed timeline and assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from model import asset_path, sha256_file, validate


def capability_sha256() -> str:
    """Bind approval to the actual renderer and its advertised methods."""
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "methods.json",
        root / "scripts" / "model.py",
        root / "scripts" / "compiler.py",
        root / "scripts" / "timeline.py",
        # Custom transitions are shared with the specialist renderer. Any
        # recipe or catalog change must invalidate prior render approval.
        root.parent / "shared" / "xfade_effects.py",
        root.parent / "edit" / "transitions" / "presets" / "transitions.json",
    ]
    digest = hashlib.sha256()
    for path in files:
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def fingerprint(timeline_path: Path, timeline: dict) -> str:
    """A file-byte and asset digest makes edits and replacements stale."""
    result = validate(timeline)
    plan = Path(timeline["plan_file"])
    # Checklist evidence is intentionally mutable as approved steps finish.
    # validate() checks its plan binding and step IDs without making later
    # evidence updates invalidate a human-approved timeline and final render.
    parts = [timeline_path.read_bytes(), plan.read_bytes(),
             plan.with_name("approval.json").read_bytes(),
             bytes.fromhex(capability_sha256())]
    for clip in result["clips"]:
        parts.append(clip["path"].as_posix().encode())
        parts.append(bytes.fromhex(sha256_file(clip["path"])))
    for cue in result["audio"]:
        path = asset_path(result["root"], cue["source"])
        parts.append(path.as_posix().encode())
        parts.append(bytes.fromhex(sha256_file(path)))
    for item in result["operations"]:
        if item["method"] == "title":
            font = asset_path(result["root"], item["font_source"])
            parts.append(font.as_posix().encode())
            parts.append(bytes.fromhex(sha256_file(font)))
        if item["method"] == "motion-graphics-ass":
            sidecar = asset_path(result["root"], item["source"])
            parts.append(sidecar.as_posix().encode())
            parts.append(bytes.fromhex(sha256_file(sidecar)))
    digest = hashlib.sha256()
    for part in parts:
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    return digest.hexdigest()


def require_human_approval(timeline_path: Path, timeline: dict,
                           approval_path: Path) -> dict:
    if not approval_path.is_file():
        raise ValueError("Human timeline approval is missing")
    record = json.loads(approval_path.read_text(encoding="utf-8-sig"))
    if (not record.get("reviewer") or not record.get("review_note")
            or record.get("actor") != "human"
            or not record.get("approved_at")
            or record.get("fingerprint") != fingerprint(timeline_path, timeline)):
        raise ValueError("Timeline approval is missing or stale")
    return record
