#!/usr/bin/env python3
"""Catalogue reviewed visual assets and sound-effect references in a private folder."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image


KINDS = {
    "cta": {".mov", ".webm", ".mp4"},
    "meme": {".mov", ".mp4", ".webm", ".gif", ".png", ".webp"},
    "gif": {".gif"},
    "sticker": {".png", ".webp", ".gif"},
    "stock-clip": {".mov", ".mp4", ".webm"},
    "sfx": {".wav", ".flac", ".mp3", ".m4a"},
}
RIGHTS = {"owned", "licensed", "permission", "unknown"}
EFFECT_REVIEWS = {"pending", "passed", "failed"}
AUDIO_CONTEXTS = {"quiet", "dialogue", "music", "natural"}
REPO_ROOT = Path(__file__).resolve().parents[5]


def validate_library(root: Path) -> Path:
    root = root.expanduser().resolve()
    # Generated/private media belongs outside the versioned skill source.
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("Library must be outside the Content Studio source repository")
    return root


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def probe_media(path: Path) -> dict:
    """Reject corrupt imports before they enter a catalogue reused across edits."""
    if path.suffix.lower() in KINDS["sfx"]:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "a:0",
                 "-show_entries", "stream=codec_name,sample_rate,channels:format=duration",
                 "-of", "json", str(path)], capture_output=True, text=True,
                check=True, timeout=20)
            data = json.loads(result.stdout)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired,
                json.JSONDecodeError) as error:
            raise ValueError("Media file cannot be decoded") from error
        if not data.get("streams") or float(data.get("format", {}).get("duration", 0)) <= 0:
            raise ValueError("Media file has no usable audio")
        stream = data["streams"][0]
        return {"duration_seconds": float(data["format"]["duration"]),
                "sample_rate": int(stream["sample_rate"]), "channels": int(stream["channels"]),
                "codec": stream.get("codec_name", "unknown")}
    if path.suffix.lower() in {".mov", ".mp4", ".webm"}:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                 "stream=width,height,pix_fmt,codec_name:format=duration", "-of", "json", str(path)],
                capture_output=True, text=True, check=True, timeout=20)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            raise ValueError("Media file cannot be decoded") from error
        data = json.loads(result.stdout)
        if not data.get("streams"):
            raise ValueError("Media file has no video stream")
        stream = data["streams"][0]
        if not stream.get("width") or not stream.get("height"):
            raise ValueError("Media file has invalid dimensions")
        return {"width": stream["width"], "height": stream["height"],
                "duration_seconds": float(data.get("format", {}).get("duration", 0)),
                "pixel_format": stream.get("pix_fmt", "unknown")}
    try:
        with Image.open(path) as opened:
            opened.verify()
        with Image.open(path) as opened:
            return {"width": opened.width, "height": opened.height,
                    "frames": getattr(opened, "n_frames", 1), "mode": opened.mode}
    except (OSError, ValueError) as error:
        raise ValueError("Media file cannot be decoded") from error


def read_catalogue(root: Path) -> list[dict]:
    path = root / "catalogue.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("assets"), list):
        raise ValueError("Unsupported stock catalogue schema")
    return data["assets"]


def _markdown(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def write_catalogue(root: Path, assets: list[dict]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    catalog = root / "catalogue.json"
    readme = root / "README.md"
    lines = ["# My Content Studio stock assets", "",
             "Private catalogue of imported reusable media and reference-only effects.", "",
             "| ID | Name | Type | Size / length | Rights | Creator | Review | Sound / shot tags | Tags | Source | File |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for item in sorted(assets, key=lambda row: row["name"].casefold()):
        cells = [_markdown(str(item[key])) for key in
                 ("id", "name", "kind")]
        media = item["media"]
        cells.append(f"{media['duration_seconds']:.3f} s" if item["kind"] == "sfx"
                     else f"{media['width']}×{media['height']}")
        cells += [_markdown(str(item[key])) for key in ("rights", "creator")]
        cells.append(_markdown(item.get("reuse_status", "reusable")))
        profile = item.get("sfx_profile", {})
        cells.append(_markdown(profile.get("label", "—") +
                               (" · " + ", ".join(profile["shot_tags"])
                                if profile.get("shot_tags") else "") +
                               (" · identity " + profile["identification_review"]
                                if profile.get("identification_review") else "")))
        cells.append(_markdown(", ".join(item["tags"])))
        source = item.get("source_url") or "—"
        cells.append(f"[source]({source})" if source.startswith("https://") else "—")
        cells.append(f"[media]({item['relative_path']})")
        lines.append("| " + " | ".join(cells) + " |")
    if not assets:
        lines.append("| — | No assets imported yet | — | — | — | — | — | — | — | — | — | — |")
    # Replace small metadata files atomically; imported source media is never rewritten.
    for target, payload in ((catalog, json.dumps({"schema_version": 1, "assets": assets},
                                                indent=2, ensure_ascii=False) + "\n"),
                            (readme, "\n".join(lines) + "\n")):
        temp = target.with_name(target.name + ".partial")
        temp.write_text(payload, encoding="utf-8")
        os.replace(temp, target)


def add(root: Path, source: Path, name: str, kind: str, rights: str,
        creator: str, tags: list[str], *, source_url: str = "",
        source_start: float | None = None, source_end: float | None = None,
        source_sha256: str = "", effect_review: str = "pending") -> dict:
    root = validate_library(root)
    source = source.expanduser().resolve()
    if not source.is_file():
        raise ValueError("Source file does not exist")
    if kind not in KINDS or source.suffix.lower() not in KINDS[kind]:
        raise ValueError("File extension is unsupported for this asset type")
    if rights not in RIGHTS or not name.strip() or not creator.strip():
        raise ValueError("Name, creator, and a valid rights state are required")
    if rights == "unknown" and kind != "sfx":
        raise ValueError("Unknown rights are accepted only for reference-only SFX")
    if kind == "sfx" and effect_review not in EFFECT_REVIEWS:
        raise ValueError("SFX effect review must be pending, passed, or failed")
    if (source_start is None) != (source_end is None) or (source_start is not None and
            (source_start < 0 or source_end <= source_start)):
        raise ValueError("Source range must have valid start and end times")
    if source_url and not source_url.startswith("https://"):
        raise ValueError("Source URL must use HTTPS")
    media = probe_media(source)
    assets = read_catalogue(root)
    sha = digest_file(source)
    duplicate = next((item for item in assets if item["sha256"] == sha), None)
    if duplicate:
        return duplicate
    ident = "stock-" + sha[:16]
    internal = root in source.parents
    relative = source.relative_to(root) if internal else Path("media") / kind / (ident + source.suffix.lower())
    target = root / relative
    if not internal:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    reuse_status = ("reusable" if rights != "unknown" and
                    (kind != "sfx" or effect_review == "passed") else "reference-only")
    item = {"id": ident, "name": name.strip(), "kind": kind, "rights": rights,
            "creator": creator.strip(), "tags": sorted(set(t.strip() for t in tags if t.strip())),
            "sha256": sha, "relative_path": relative.as_posix(), "media": media,
            "reuse_status": reuse_status}
    if kind == "sfx":
        item.update({"effect_review": effect_review, "source_url": source_url,
                     "source_start_seconds": source_start, "source_end_seconds": source_end,
                     "source_sha256": source_sha256})
    try:
        write_catalogue(root, assets + [item])
    except Exception:
        if not internal:
            target.unlink(missing_ok=True)
        raise
    return item


def review_sfx(root: Path, ident: str, rights: str, effect_review: str, note: str) -> dict:
    root = validate_library(root)
    assets = read_catalogue(root)
    item = next((entry for entry in assets if entry["id"] == ident), None)
    if item is None or item["kind"] != "sfx":
        raise ValueError("SFX catalogue ID not found")
    if rights not in RIGHTS or effect_review not in EFFECT_REVIEWS or not note.strip():
        raise ValueError("Valid rights, effects-only review, and review note are required")
    # A later verified decision updates metadata in place; SHA-256 dedupe keeps one media copy.
    item.update({"rights": rights, "effect_review": effect_review,
                 "review_note": note.strip(),
                 "reuse_status": ("reusable" if rights != "unknown" and
                                  effect_review == "passed" else "reference-only")})
    write_catalogue(root, assets)
    return item


def _shot_tags(values: list[str]) -> list[str]:
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise ValueError("Shot tags must be nonempty lowercase slugs")
    tags = sorted({value.strip().lower() for value in values})
    if not tags or any(not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", tag)
                       for tag in tags):
        raise ValueError("Shot tags must be nonempty lowercase slugs")
    return tags


def describe_sfx(root: Path, ident: str, label: str, shot_tags: list[str], note: str,
                 identification_review: str = "pending") -> dict:
    """Store a reviewed description separately from rights and effects-only review."""
    root = validate_library(root)
    assets = read_catalogue(root)
    item = next((entry for entry in assets if entry["id"] == ident), None)
    if item is None or item["kind"] != "sfx":
        raise ValueError("SFX catalogue ID not found")
    if not label.strip() or not note.strip() or identification_review not in {"pending", "passed"}:
        raise ValueError("Sound label and identification evidence are required")
    item["sfx_profile"] = {"label": label.strip(), "shot_tags": _shot_tags(shot_tags),
                           "identification_note": note.strip(),
                           "identification_review": identification_review}
    write_catalogue(root, assets)
    return item


def suggest_sfx(assets: list[dict], manifest: dict, mode: str = "delivery") -> dict:
    """Rank exact tag matches; proposals never become approved timeline cues."""
    if mode not in {"delivery", "reference"}:
        raise ValueError("Mode must be delivery or reference")
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("shots"), list):
        raise ValueError("Unsupported shot manifest schema")
    seen = set()
    selections = []
    for shot in manifest["shots"]:
        ident = shot.get("id")
        start, end = shot.get("start_seconds"), shot.get("end_seconds")
        if (not isinstance(ident, str) or not ident or ident in seen or
                not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or
                not math.isfinite(start) or not math.isfinite(end) or
                start < 0 or end <= start or shot.get("audio_context") not in AUDIO_CONTEXTS or
                not isinstance(shot.get("shot_tags"), list)):
            raise ValueError("Invalid shot ID, range, tags, or audio context")
        seen.add(ident)
        tags = _shot_tags(shot["shot_tags"])
        ranked = []
        # Dialogue and natural sound are preserved unless an editor explicitly revises the shot plan.
        if shot["audio_context"] in {"quiet", "music"}:
            for item in assets:
                profile = item.get("sfx_profile", {})
                if (item.get("kind") != "sfx" or item.get("effect_review") != "passed" or
                        profile.get("identification_review") != "passed"):
                    continue
                cleared = (item.get("rights") in {"owned", "licensed", "permission"} and
                           item.get("reuse_status") == "reusable")
                if mode == "delivery" and not cleared:
                    continue
                overlap = sorted(set(tags) & set(profile.get("shot_tags", [])))
                if not overlap or item["media"]["duration_seconds"] > end - start + 0.05:
                    continue
                # More matching cues win; narrower sound profiles break ties.
                score = len(overlap) / len(tags) + len(overlap) / len(profile["shot_tags"])
                ranked.append((score, item["id"], item, overlap))
        ranked.sort(key=lambda row: (-row[0], row[1]))
        chosen = ranked[0] if ranked else None
        candidate = None
        if chosen:
            _, _, item, overlap = chosen
            candidate = {"asset_id": item["id"], "name": item["name"],
                         "sound_label": item["sfx_profile"]["label"],
                         "matched_tags": overlap, "score": round(chosen[0], 3),
                         "media_path": item["relative_path"],
                         "reuse_status": item["reuse_status"],
                         "placement_allowed": (item.get("rights") in
                                               {"owned", "licensed", "permission"} and
                                               item["reuse_status"] == "reusable")}
        reason = ("preserve shot audio" if shot["audio_context"] in {"dialogue", "natural"}
                  else "no eligible tagged effect fits this shot" if not chosen
                  else "tag and duration match; editor review required")
        selections.append({"shot_id": ident, "start_seconds": start, "end_seconds": end,
                           "candidate": candidate, "reason": reason,
                           "approval_required": True})
    return {"schema_version": 1, "mode": mode, "selections": selections,
            "timeline_changed": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True, type=Path,
                        help="Private asset folder outside the source repository")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("init")
    listing = sub.add_parser("list")
    listing.add_argument("--kind", choices=sorted(KINDS))
    listing.add_argument("--tag")
    entry = sub.add_parser("add")
    entry.add_argument("--file", required=True, type=Path)
    entry.add_argument("--name", required=True)
    entry.add_argument("--kind", required=True, choices=sorted(KINDS))
    entry.add_argument("--rights", required=True, choices=sorted(RIGHTS))
    entry.add_argument("--creator", required=True)
    entry.add_argument("--tags", default="", help="Comma-separated search tags")
    entry.add_argument("--source-url", default="", help="Canonical source URL for SFX")
    entry.add_argument("--source-start", type=float)
    entry.add_argument("--source-end", type=float)
    entry.add_argument("--source-sha256", default="")
    entry.add_argument("--effect-review", choices=sorted(EFFECT_REVIEWS), default="pending",
                       help="Passed only after listening to the entire effect for voice/music bleed")
    review = sub.add_parser("review")
    review.add_argument("--id", required=True)
    review.add_argument("--rights", required=True, choices=sorted(RIGHTS))
    review.add_argument("--effect-review", required=True, choices=sorted(EFFECT_REVIEWS))
    review.add_argument("--note", required=True, help="Human listening and rights evidence")
    description = sub.add_parser("describe-sfx")
    description.add_argument("--id", required=True)
    description.add_argument("--label", required=True, help="Reviewed audible identity")
    description.add_argument("--shot-tags", required=True,
                             help="Comma-separated shot situations where the effect fits")
    description.add_argument("--note", required=True, help="Identification evidence")
    description.add_argument("--identification-review", choices=("pending", "passed"),
                             default="pending", help="Passed only after the audible label is confirmed")
    suggestion = sub.add_parser("suggest-sfx")
    suggestion.add_argument("--shots", required=True, type=Path)
    suggestion.add_argument("--output", required=True, type=Path)
    suggestion.add_argument("--mode", choices=("delivery", "reference"), default="delivery")
    args = parser.parse_args()
    root = validate_library(args.library)
    if args.action == "init":
        write_catalogue(root, read_catalogue(root))
        print(root / "README.md")
    elif args.action == "add":
        item = add(root, args.file, args.name, args.kind, args.rights,
                   args.creator, args.tags.split(","), source_url=args.source_url,
                   source_start=args.source_start, source_end=args.source_end,
                   source_sha256=args.source_sha256, effect_review=args.effect_review)
        print(json.dumps(item, indent=2, ensure_ascii=False))
    elif args.action == "review":
        item = review_sfx(root, args.id, args.rights, args.effect_review, args.note)
        print(json.dumps(item, indent=2, ensure_ascii=False))
    elif args.action == "describe-sfx":
        item = describe_sfx(root, args.id, args.label, args.shot_tags.split(","), args.note,
                            args.identification_review)
        print(json.dumps(item, indent=2, ensure_ascii=False))
    elif args.action == "suggest-sfx":
        shots = json.loads(args.shots.read_text(encoding="utf-8"))
        result = suggest_sfx(read_catalogue(root), shots, args.mode)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
        print(args.output)
    else:
        items = read_catalogue(root)
        if args.kind:
            items = [item for item in items if item["kind"] == args.kind]
        if args.tag:
            items = [item for item in items if args.tag in item["tags"] or
                     args.tag in item.get("sfx_profile", {}).get("shot_tags", [])]
        print(json.dumps(items, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
