#!/usr/bin/env python3
"""Import Earshot's pinned bank and manage reviewed Content Studio SFX."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path


PINNED_COMMIT = "4ac3d2ac2b151e1c23376f9ce7f3047a17050013"
UPSTREAM = "https://github.com/Leonxlnx/earshot"
STOCK = Path(__file__).resolve().parents[3] / "stock-library"
spec = importlib.util.spec_from_file_location("content_studio_stock", STOCK / "scripts" / "library.py")
library = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(library)


def _sha(path: Path) -> str:
    return library.digest_file(path)


def _wav24(path: Path, audio, rate: int) -> None:
    """Write reproducible PCM without adding Earshot's analysis dependencies."""
    import numpy as np

    samples = np.asarray(audio, dtype=np.float64)
    if samples.ndim == 1:
        samples = samples[:, None]
    if samples.ndim != 2 or samples.shape[1] not in (1, 2):
        raise ValueError("Earshot returned unsupported audio channels")
    values = np.ascontiguousarray(
        np.rint(np.clip(samples, -1, 1 - 1 / 8388608) * 8388608).astype("<i4"))
    packed = values.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(samples.shape[1])
        output.setsampwidth(3)
        output.setframerate(rate)
        output.writeframes(packed)


def _load_bank(source: Path):
    source = source.resolve()
    if not (source / "earshot" / "forge" / "bank.py").is_file():
        raise ValueError("--earshot-root must point to an Earshot source checkout")
    revision = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    if revision != PINNED_COMMIT:
        raise ValueError(f"Earshot revision {revision} differs from pinned {PINNED_COMMIT}")
    sys.path.insert(0, str(source))
    from earshot.forge import bank  # noqa: E402
    return bank


def _fit_sources(source: Path) -> dict:
    path = source / "earshot" / "forge" / "bank" / "fit.json"
    return json.loads(path.read_text(encoding="utf-8"))["entries"]


_WORKER_BANK = None


def _start_worker(source: Path) -> None:
    global _WORKER_BANK
    sys.path.insert(0, str(source.resolve()))
    from earshot.forge import bank  # noqa: E402
    _WORKER_BANK = bank


def _render_sound(sound: dict, assets: Path) -> tuple[dict, dict, str]:
    """Independent renders can use separate CPUs; catalogue writes stay serialized."""
    sound_id = sound["id"]
    rendered, meta = _WORKER_BANK.render(sound_id)
    target = assets / "media" / "sfx" / "earshot" / Path(*sound_id.split("/"))
    target = target.with_suffix(".wav")
    if not target.exists():
        _wav24(target, rendered, int(meta["sr"]))
    return sound, meta, _sha(target)


def import_bank(source: Path, assets: Path) -> dict:
    """Ship every pinned sound; audit and listening remain separate gates."""
    assets = library.validate_library(assets)
    bank = _load_bank(source)
    sounds = bank.list_sounds()
    if len(sounds) != 252:
        raise ValueError(f"Pinned Earshot bank changed: expected 252, found {len(sounds)}")
    fitted = _fit_sources(source)
    existing = library.read_catalogue(assets)
    by_sound = {item.get("origin", {}).get("sound_id"): item for item in existing
                if item.get("origin", {}).get("source") == "earshot" and
                item.get("origin", {}).get("bank_version")}
    imported = []
    audit_failed = 0
    # Earshot's synthesis is CPU-heavy. Process workers keep the import bounded
    # without sharing catalogue writes or changing source media.
    with ProcessPoolExecutor(max_workers=min(6, os.cpu_count() or 4),
                             initializer=_start_worker, initargs=(source,)) as pool:
        rendered_sounds = list(pool.map(_render_sound, sounds,
                                        [assets] * len(sounds), chunksize=1))
    for sound, meta, rendered_sha in rendered_sounds:
        sound_id = sound["id"]
        recipe = bank.get(sound_id)
        target = assets / "media" / "sfx" / "earshot" / Path(*sound_id.split("/"))
        target = target.with_suffix(".wav")
        with wave.open(str(target), "rb") as playable:
            channels = playable.getnchannels()
        # Preserve prior human listening decisions on an idempotent import.
        previous = by_sound.get(sound_id)
        if previous and previous["sha256"] != rendered_sha:
            raise ValueError(f"Stored Earshot WAV changed for {sound_id}")
        check = meta["checks"]
        passed = bool(check["ok"])
        audit_failed += not passed
        fit = fitted.get(sound_id, {}).get("source", {})
        license_name = "CC0-1.0" if sound_id.startswith("fit/") else "MIT"
        label = sound.get("notes") or sound_id.replace("/", " ").replace("_", " ")
        item = previous or {
            "id": "stock-" + rendered_sha[:16], "name": sound_id,
            "kind": "sfx", "rights": "licensed", "creator": "Leon Lin",
            "tags": sorted({"earshot", sound["category"], *sound.get("kinds", [])}),
            "sha256": rendered_sha,
            "relative_path": target.relative_to(assets).as_posix(),
            "media": {"duration_seconds": float(meta["dur_s"]),
                      "sample_rate": int(meta["sr"]),
                      "channels": channels,
                      "codec": "pcm_s24le"},
            "reuse_status": "reference-only", "effect_review": "pending",
            "source_url": UPSTREAM + "/tree/" + PINNED_COMMIT,
            "source_start_seconds": None, "source_end_seconds": None,
            "source_sha256": "",
            "sfx_profile": {"label": label, "shot_tags": [],
                            "identification_review": "pending",
                            "identification_note": "Earshot bank description; listen before final use"},
        }
        item["media"]["channels"] = channels
        item["origin"] = {
            "source": "earshot", "commit": PINNED_COMMIT,
            "bank_version": bank.VERSION, "sound_id": sound_id,
            "family": sound["category"],
            "recipe_id": recipe.get("recipe") or f"fit/{sound['member']}",
            "recipe_sha256": hashlib.sha256(json.dumps(recipe, sort_keys=True,
                default=str).encode()).hexdigest(),
            "parameters": recipe.get("params") or {},
            "license": license_name, "recording": fit or None,
            "seed": int(meta["seed"]), "render_edits": {},
            "cue_roles": sound.get("kinds", []),
            "sync": {"onset_s": float(meta["onset_s"]),
                     "peak_s": float(meta["peak_s"]), "end_s": float(meta["end_s"])},
            "audit": {"status": "passed" if passed else "failed",
                      "warnings": check["warnings"]},
        }
        if not passed:
            item["reuse_status"] = "reference-only"
        imported.append(item)
    other = [item for item in existing if not (
        item.get("origin", {}).get("source") == "earshot" and
        item.get("origin", {}).get("bank_version"))]
    library.write_catalogue(assets, other + imported)
    gallery(assets, [item for item in other
                     if item.get("origin", {}).get("source") == "earshot"] + imported)
    return {"count": len(imported), "audit_failed": audit_failed,
            "bank_version": bank.VERSION, "commit": PINNED_COMMIT,
            "gallery": str(assets / "earshot-gallery.html")}


def gallery(assets: Path, items: list[dict] | None = None) -> Path:
    items = items if items is not None else [item for item in library.read_catalogue(assets)
                                            if item.get("origin", {}).get("source") == "earshot"]
    groups: dict[str, list[dict]] = {}
    for item in items:
        groups.setdefault(item["origin"]["sound_id"].split("/")[0], []).append(item)
    sections = []
    for category, sounds in sorted(groups.items()):
        cards = []
        for item in sorted(sounds, key=lambda row: row["name"]):
            origin = item["origin"]
            cards.append("<article><strong>{}</strong><small>{:.2f}s · {} · audit {} · listening {}</small>"
                         "<audio controls preload='none' src='{}'></audio><p>{}</p></article>".format(
                             html.escape(item["name"]), item["media"]["duration_seconds"],
                             html.escape(origin["license"]), origin["audit"]["status"],
                             item.get("effect_review", "pending"),
                             html.escape(item["relative_path"], quote=True),
                             html.escape(item.get("sfx_profile", {}).get("label", ""))))
        sections.append(f"<section><h2>{html.escape(category)}</h2>{''.join(cards)}</section>")
    page = assets / "earshot-gallery.html"
    page.write_text("<!doctype html><meta charset='utf-8'><title>Content Studio Earshot SFX</title>"
                    "<style>body{font:16px system-ui;background:#10151d;color:#eef;max-width:1100px;"
                    "margin:auto;padding:24px}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));"
                    "gap:12px}h2{grid-column:1/-1}article{background:#202b39;padding:14px;border-radius:8px}"
                    "small{display:block;color:#bac;margin:8px 0}audio{width:100%}</style>"
                    "<h1>Earshot sound bank</h1><p>Review the complete sound and tail before approving use.</p>"
                    + "".join(sections), encoding="utf-8")
    return page


def review(assets: Path, sound_id: str, note: str) -> dict:
    assets = library.validate_library(assets)
    items = library.read_catalogue(assets)
    item = next((row for row in items if row.get("origin", {}).get("sound_id") == sound_id), None)
    if not item or not note.strip():
        raise ValueError("Known Earshot sound and listening note are required")
    if item["origin"]["audit"]["status"] != "passed":
        raise ValueError("Earshot audit failed; repair and re-audit before approval")
    if item["rights"] == "unknown":
        raise ValueError("Unknown rights block sound reuse")
    path = assets / item["relative_path"]
    if not path.is_file() or _sha(path) != item["sha256"]:
        raise ValueError("Sound file missing or changed")
    item["effect_review"] = "passed"
    item["reuse_status"] = "reusable"
    item["sfx_profile"]["identification_review"] = "passed"
    item["sfx_profile"]["identification_note"] = note.strip()
    library.write_catalogue(assets, items)
    gallery(assets)
    return item


def adopt(assets: Path, source: Path, earshot_root: Path, mode: str,
          recipe: Path, creator: str, rights: str, redistribute: bool,
          recording: Path | None = None, recording_license: str = "") -> dict:
    """Catalogue a generated candidate, retaining derivative rights and audit evidence."""
    if (mode not in {"forge", "fit"} or not source.is_file() or
            source.suffix.lower() != ".wav" or not recipe.is_file()):
        raise ValueError("A generated WAV and its forge/fit recipe are required")
    if mode == "fit" and (not recording or not recording.is_file() or not recording_license):
        raise ValueError("Fit requires the source recording and its license")
    if redistribute and rights == "unknown":
        raise ValueError("Unknown-rights sound cannot ship in Git")
    assets = library.validate_library(assets)
    _load_bank(earshot_root)
    import numpy as np
    from earshot.forge import sfx as earshot_sfx  # noqa: E402
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(source),
                          "-ac", "2", "-ar", "48000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    samples = np.frombuffer(raw, dtype="<f4").reshape(-1, 2)
    audit = earshot_sfx.check(samples, sr=48000)
    sha = _sha(source)
    subdir = "earshot/created" if redistribute else "local"
    target = assets / "media" / "sfx" / subdir / (sha + ".wav")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(source, target)
    recipe_target = assets / ("recipes/earshot" if redistribute else "recipes/local") / (sha + recipe.suffix)
    recipe_target.parent.mkdir(parents=True, exist_ok=True)
    if not recipe_target.exists():
        shutil.copy2(recipe, recipe_target)
    item = library.add(assets, target, source.stem, "sfx", rights, creator,
                       ["sfx", mode], source_url=UPSTREAM + "/tree/" + PINNED_COMMIT,
                       effect_review="pending")
    entries = library.read_catalogue(assets)
    entry = next(row for row in entries if row["id"] == item["id"])
    entry["origin"] = {"source": "earshot", "commit": PINNED_COMMIT,
                       "sound_id": "created/" + sha[:16], "mode": mode,
                       "recipe_sha256": _sha(recipe),
                       "recipe_relative_path": recipe_target.relative_to(assets).as_posix(),
                       "recording_sha256": _sha(recording) if recording else None,
                       "recording_license": recording_license or None,
                       "license": recording_license if mode == "fit" else "MIT",
                       "redistributable": redistribute,
                       "audit": {"status": "passed" if audit["ok"] else "failed",
                                 "warnings": audit["warnings"]},
                       "cue_roles": [], "sync": {}}
    entry["sfx_profile"] = {"label": source.stem.replace("_", " "),
                             "shot_tags": [], "identification_review": "pending",
                             "identification_note": "New Earshot candidate; listen before use"}
    entry["reuse_status"] = "reference-only"
    library.write_catalogue(assets, entries)
    return {"id": entry["id"], "audit": entry["origin"]["audit"],
            "tracked_asset": redistribute, "review_required": True}


def run_creator(mode: str, source: Path, output: Path, args: list[str]) -> dict:
    """Run Earshot creation in its checkout; selection/import require later review."""
    _load_bank(source)
    args = args[1:] if args[:1] == ["--"] else args
    if mode not in {"forge", "fit"} or any(arg in {"--out", "--dir", "-o"} for arg in args):
        raise ValueError("Use forge or fit and let Content Studio set the output location")
    output = output.resolve()
    if output.exists():
        raise ValueError("Creation output already exists")
    command = [sys.executable, "-m", "earshot", mode, *args,
               "--dir" if mode == "forge" else "-o", str(output)]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source.resolve()) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-900:])
    return {"mode": mode, "output": str(output), "source_commit": PINNED_COMMIT,
            "review_required": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    importer = actions.add_parser("import-bank")
    importer.add_argument("--earshot-root", type=Path, required=True)
    importer.add_argument("--library", type=Path, default=library.STOCK_ASSETS)
    listing = actions.add_parser("gallery")
    listing.add_argument("--library", type=Path, default=library.STOCK_ASSETS)
    approve = actions.add_parser("review")
    approve.add_argument("--library", type=Path, default=library.STOCK_ASSETS)
    approve.add_argument("--sound-id", required=True)
    approve.add_argument("--note", required=True)
    adoption = actions.add_parser("adopt")
    adoption.add_argument("--library", type=Path, default=library.STOCK_ASSETS)
    adoption.add_argument("--earshot-root", type=Path, required=True)
    adoption.add_argument("--file", type=Path, required=True)
    adoption.add_argument("--recipe", type=Path, required=True)
    adoption.add_argument("--mode", choices=["forge", "fit"], required=True)
    adoption.add_argument("--creator", required=True)
    adoption.add_argument("--rights", choices=sorted(library.RIGHTS), required=True)
    adoption.add_argument("--redistributable", action="store_true")
    adoption.add_argument("--source-recording", type=Path)
    adoption.add_argument("--source-license", default="")
    for mode in ("forge", "fit"):
        create = actions.add_parser(mode)
        create.add_argument("--earshot-root", type=Path, required=True)
        create.add_argument("--output", type=Path, required=True)
        create.add_argument("earshot_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.action == "import-bank":
            result = import_bank(args.earshot_root, args.library)
        elif args.action == "gallery":
            result = {"gallery": str(gallery(args.library))}
        elif args.action == "review":
            item = review(args.library, args.sound_id, args.note)
            result = {"id": item["id"], "sound_id": args.sound_id,
                      "reuse_status": item["reuse_status"]}
        elif args.action == "adopt":
            result = adopt(args.library, args.file, args.earshot_root, args.mode,
                           args.recipe, args.creator, args.rights,
                           args.redistributable, args.source_recording,
                           args.source_license)
        else:
            result = run_creator(args.action, args.earshot_root, args.output,
                                 args.earshot_args)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"SFX {args.action} failed: {exc}\n")


if __name__ == "__main__":
    main()
