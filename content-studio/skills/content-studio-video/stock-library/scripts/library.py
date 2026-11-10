#!/usr/bin/env python3
"""Catalogue self-created reusable video assets in a private local folder."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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
}
RIGHTS = {"owned", "licensed", "permission"}
REPO_ROOT = Path(__file__).resolve().parents[4]


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
             "Private catalogue of imported, user-authorized reusable media.", "",
             "| ID | Name | Type | Size | Rights | Creator | Tags | File |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for item in sorted(assets, key=lambda row: row["name"].casefold()):
        cells = [_markdown(str(item[key])) for key in
                 ("id", "name", "kind")]
        cells.append(f"{item['media']['width']}×{item['media']['height']}")
        cells += [_markdown(str(item[key])) for key in ("rights", "creator")]
        cells.append(_markdown(", ".join(item["tags"])))
        cells.append(f"[media]({item['relative_path']})")
        lines.append("| " + " | ".join(cells) + " |")
    if not assets:
        lines.append("| — | No assets imported yet | — | — | — | — | — | — |")
    # Replace small metadata files atomically; imported source media is never rewritten.
    for target, payload in ((catalog, json.dumps({"schema_version": 1, "assets": assets},
                                                indent=2, ensure_ascii=False) + "\n"),
                            (readme, "\n".join(lines) + "\n")):
        temp = target.with_name(target.name + ".partial")
        temp.write_text(payload, encoding="utf-8")
        os.replace(temp, target)


def add(root: Path, source: Path, name: str, kind: str, rights: str,
        creator: str, tags: list[str]) -> dict:
    root = validate_library(root)
    source = source.expanduser().resolve()
    if not source.is_file():
        raise ValueError("Source file does not exist")
    if kind not in KINDS or source.suffix.lower() not in KINDS[kind]:
        raise ValueError("File extension is unsupported for this asset type")
    if rights not in RIGHTS or not name.strip() or not creator.strip():
        raise ValueError("Name, creator, and confirmed rights are required")
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
    item = {"id": ident, "name": name.strip(), "kind": kind, "rights": rights,
            "creator": creator.strip(), "tags": sorted(set(t.strip() for t in tags if t.strip())),
            "sha256": sha, "relative_path": relative.as_posix(), "media": media}
    try:
        write_catalogue(root, assets + [item])
    except Exception:
        if not internal:
            target.unlink(missing_ok=True)
        raise
    return item


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
    args = parser.parse_args()
    root = validate_library(args.library)
    if args.action == "init":
        write_catalogue(root, read_catalogue(root))
        print(root / "README.md")
    elif args.action == "add":
        item = add(root, args.file, args.name, args.kind, args.rights,
                   args.creator, args.tags.split(","))
        print(json.dumps(item, indent=2, ensure_ascii=False))
    else:
        items = read_catalogue(root)
        if args.kind:
            items = [item for item in items if item["kind"] == args.kind]
        if args.tag:
            items = [item for item in items if args.tag in item["tags"]]
        print(json.dumps(items, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
