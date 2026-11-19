#!/usr/bin/env python3
"""Review a hero-led source range and hand its portrait crop to the delivery timeline."""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

VIDEO_ROOT = next(parent for parent in Path(__file__).resolve().parents
                  if parent.name == "content-studio-video")
TIMELINE_SCRIPTS = VIDEO_ROOT / "timeline" / "scripts"
UNDERSTAND_SCRIPTS = VIDEO_ROOT / "review" / "understand" / "scripts"
sys.path.insert(0, str(TIMELINE_SCRIPTS))
sys.path.insert(0, str(UNDERSTAND_SCRIPTS))
from compiler import compile_graph, media_info  # noqa: E402
from model import load as load_timeline  # noqa: E402
from model import revise, sha256_file, validate as validate_timeline  # noqa: E402
from understand import analyze as contact_sheets  # noqa: E402

SCHEMA = "content-studio.hero-clipping.v1"
METHODS = {"subjects", "saliency", "center"}
EPSILON = 0.0001


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _write_new(path: Path, value: dict) -> None:
    # Review revisions are immutable; never erase evidence used by an approval.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as target:
        json.dump(value, target, indent=2, ensure_ascii=False)
        target.write("\n")


def _positive_number(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be numeric") from error
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return number


def _relative_path(path: Path, base: Path) -> str:
    try:
        return os.path.relpath(path.resolve(), base.resolve()).replace("\\", "/")
    except ValueError as error:
        raise ValueError("Source and clipping review must be on the same drive") from error


def _source_path(selection_path: Path, record: dict) -> Path:
    relative = record.get("source", {}).get("path")
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Selection source.path must be relative to selection.json")
    source = (selection_path.parent / relative).resolve()
    if not source.is_file():
        raise ValueError(f"Selection source is missing: {source}")
    return source


def source_metadata(source: Path) -> dict:
    """Match the timeline's SDR safety gate before generating crop proposals."""
    info = media_info(source)
    video = info["video"]
    if not video or info["duration"] <= 0:
        raise ValueError("Source needs a video stream and positive duration")
    if int(video.get("width") or 0) < 2 or int(video.get("height") or 0) < 2:
        raise ValueError("Source picture dimensions are invalid")
    side_data = json.dumps(video.get("side_data_list", [])).lower()
    pixel_format = str(video.get("pix_fmt", ""))
    if (video.get("color_transfer") in {"smpte2084", "arib-std-b67"}
            or video.get("color_primaries") == "bt2020"
            or "dovi" in side_data or "dolby vision" in side_data
            or "10" in pixel_format or "12" in pixel_format):
        raise ValueError("HDR, Dolby Vision, or high-bit-depth picture is unsupported for clipping v1")
    try:
        average = float(Fraction(video.get("avg_frame_rate", "0/1")))
        nominal = float(Fraction(video.get("r_frame_rate", "0/1")))
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError("Source frame rate could not be read") from error
    if average < 1 or abs(average - nominal) > 0.01:
        raise ValueError("Variable frame rate needs a separately reviewed timing route")
    return {
        "duration": round(float(info["duration"]), 6),
        "width": int(video["width"]), "height": int(video["height"]),
        "fps": average, "color_transfer": video.get("color_transfer", "unknown"),
        "has_audio": bool(info["audio"]),
    }


def inspect_source(source: Path, out: Path, hero: str, *, start: float | None = None,
                   end: float | None = None, interval: float = 5.0) -> dict:
    """Create source-linked contact sheets and an editable selection proposal."""
    source, out = source.resolve(), out.resolve()
    if not source.is_file() or not hero.strip():
        raise ValueError("A finished source file and hero description are required")
    evidence_dir = out.parent / f"{out.stem}-source-review"
    if out.exists() or evidence_dir.exists():
        raise ValueError("Selection or source-review already exists; use a new revision path")
    metadata = source_metadata(source)
    if (start is None) != (end is None):
        raise ValueError("Supply both --start and --end, or neither")
    if start is not None and (not 0 <= start < end <= metadata["duration"] + EPSILON):
        raise ValueError("Selected range must be inside the source duration")
    interval = _positive_number(interval, "interval")
    # A narrow candidate needs several samples; whole-source discovery can stay sparse.
    if start is not None:
        interval = min(interval, max(0.1, (end - start) / 4))
    evidence = contact_sheets(source, evidence_dir, interval=interval,
                              start=start or 0, end=end)
    selected = ({"source_in": float(start), "source_out": float(end)}
                if start is not None else None)
    record = {
        "schema": SCHEMA, "source": {
            "path": _relative_path(source, out.parent),
            "sha256": evidence["source_sha256"], **metadata},
        "hero": hero.strip(),
        "candidates": ([{"id": "c001", **selected,
                         "story_notes": "", "sound_boundary_notes": ""}]
                       if selected else []),
        "selected": selected,
        "evidence": {
            "manifest": _relative_path(evidence_dir / "evidence.json", out.parent),
            "manifest_sha256": sha256_file(evidence_dir / "evidence.json"),
            "frame_ids": [frame["id"] for frame in evidence["frames"]],
        },
        "crop_intervals": [],
        "editorial_review": {"status": "pending_review", "reviewer": "", "note": ""},
        "status": "pending_review",
    }
    _write_new(out, record)
    return record


def _selection_range(record: dict, duration: float) -> tuple[float, float] | None:
    selected = record.get("selected")
    if selected is None:
        return None
    if not isinstance(selected, dict):
        raise ValueError("selected must be a source range object")
    try:
        start = float(selected["source_in"])
        end = float(selected["source_out"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("selected needs numeric source_in and source_out") from error
    if (not math.isfinite(start) or not math.isfinite(end)
            or start < 0 or end <= start or end > duration + EPSILON):
        raise ValueError("Selected source range is outside the video")
    return start, end


def _relative_evidence(selection_path: Path, name: object, label: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError(f"{label} needs a relative evidence path")
    path = (selection_path.parent / name).resolve()
    if not path.is_file():
        raise ValueError(f"{label} is missing: {path}")
    return path


def validate_selection(selection_path: Path, *, source_override: Path | None = None,
                       ready: bool = False) -> dict:
    """Check current source/evidence bytes and all selected crop intervals."""
    selection_path = selection_path.resolve()
    record = _read(selection_path)
    if (record.get("schema") != SCHEMA
            or not isinstance(record.get("source"), dict)
            or not str(record.get("hero", "")).strip()):
        raise ValueError("Selection schema or hero description is missing")
    source = _source_path(selection_path, record)
    if source_override is not None and source != source_override.resolve():
        raise ValueError("Selection points to a different source")
    if sha256_file(source) != record["source"].get("sha256"):
        raise ValueError("Selection source changed")
    metadata = source_metadata(source)
    for field in ("width", "height", "has_audio"):
        if metadata[field] != record["source"].get(field):
            raise ValueError(f"Selection source metadata changed: {field}")
    selected = _selection_range(record, metadata["duration"])
    evidence = record.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("Source evidence is missing")
    manifest_file = _relative_evidence(selection_path, evidence.get("manifest"),
                                       "Source evidence manifest")
    if sha256_file(manifest_file) != evidence.get("manifest_sha256"):
        raise ValueError("Source evidence manifest changed")
    manifest = _read(manifest_file)
    if manifest.get("source_sha256") != record["source"]["sha256"]:
        raise ValueError("Source evidence changed or belongs to another video")
    frames = {frame["id"]: frame for frame in manifest.get("frames", [])}
    frame_ids = evidence.get("frame_ids")
    if (not isinstance(frame_ids, list) or not frame_ids
            or any(frame_id not in frames for frame_id in frame_ids)):
        raise ValueError("Selection needs valid timestamped evidence frame IDs")
    if selected and not any(selected[0] - EPSILON <= frames[frame_id]["at_seconds"]
                            <= selected[1] + EPSILON for frame_id in frame_ids):
        raise ValueError("Selection has no evidence frame inside the chosen range")
    intervals = record.get("crop_intervals", [])
    if not isinstance(intervals, list):
        raise ValueError("crop_intervals must be a list")
    if intervals and selected is None:
        raise ValueError("Crop intervals need a selected source range")
    # Report an uncovered ending before checking individual proposal geometry.
    if ready and intervals and selected and isinstance(intervals[-1], dict):
        try:
            last_end = float(intervals[-1].get("source_out"))
        except (TypeError, ValueError):
            last_end = float("nan")
        if math.isfinite(last_end) and abs(last_end - selected[1]) > EPSILON:
            raise ValueError("Crop intervals must cover the entire selected range")
    previous_end = selected[0] if selected else 0
    for index, crop in enumerate(intervals):
        if not isinstance(crop, dict):
            raise ValueError("Crop interval must be an object")
        try:
            begin, finish = float(crop["source_in"]), float(crop["source_out"])
            x, y, w, h = (float(crop[key]) for key in ("x", "y", "w", "h"))
            target_width = int(crop["target_width"])
            target_height = int(crop["target_height"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Crop interval {index + 1} is incomplete") from error
        if (not all(math.isfinite(v) for v in (begin, finish, x, y, w, h))
                or not selected or begin < selected[0] - EPSILON
                or finish > selected[1] + EPSILON or finish <= begin):
            raise ValueError("Crop interval lies outside the selected range")
        if abs(begin - previous_end) > EPSILON:
            raise ValueError("Crop intervals must cover the selected range without gaps or overlaps")
        previous_end = finish
        if (x < 0 or y < 0 or w <= 0 or h <= 0
                or x + w > 1 + EPSILON or y + h > 1 + EPSILON):
            raise ValueError("Crop rectangle must fit within normalized source bounds")
        if (target_width < 2 or target_height < 2 or target_width % 2
                or target_height % 2 or 16 * target_width != 9 * target_height):
            raise ValueError("Crop target must be an even 9:16 portrait canvas")
        actual_aspect = w * metadata["width"] / (h * metadata["height"])
        target_aspect = target_width / target_height
        if abs(actual_aspect - target_aspect) > 0.002:
            raise ValueError("Crop aspect does not match the portrait target")
        if crop.get("method") not in METHODS:
            raise ValueError("Crop method is unsupported")
        proposal = _relative_evidence(selection_path, crop.get("proposal_file"),
                                      "Crop proposal")
        if sha256_file(proposal) != crop.get("proposal_sha256"):
            raise ValueError("Crop proposal changed")
        proposal_data = _read(proposal)
        if (proposal_data.get("source") != source.name
                or proposal_data.get("mode") != crop["method"]
                or proposal_data.get("target_width") != target_width
                or proposal_data.get("target_height") != target_height
                or proposal_data.get("range") != [round(begin, 3), round(finish, 3)]
                or any(abs(float(proposal_data.get("crop", {}).get(key, -10)) - float(crop[key]))
                       > 0.000001 for key in ("x", "y", "w", "h"))):
            raise ValueError("Crop geometry differs from the reviewed proposal")
        _relative_evidence(selection_path, crop.get("preview_file"), "Crop preview")
        if ready and (crop.get("review_status") != "approved"
                      or not str(crop.get("review_note", "")).strip()):
            raise ValueError("Every crop interval needs human review")
    if ready and intervals and selected and abs(previous_end - selected[1]) > EPSILON:
        raise ValueError("Crop intervals must cover the entire selected range")
    if ready:
        editorial = record.get("editorial_review", {})
        if (selected is None or not intervals or record.get("status") != "reviewed"
                or editorial.get("status") != "approved"
                or not str(editorial.get("reviewer", "")).strip()
                or not str(editorial.get("note", "")).strip()):
            raise ValueError("Selection range and story need human review")
    return {"status": record.get("status", "pending_review"),
            "source": str(source), "source_sha256": record["source"]["sha256"],
            "selected": selected, "crop_intervals": intervals,
            "has_audio": metadata["has_audio"]}


def propose_crop(selection_path: Path, out_selection: Path, output: Path, *,
                 method: str = "subjects", subjects: Path | None = None,
                 size: str = "1080x1920", start: float | None = None,
                 end: float | None = None) -> dict:
    """Reuse one specialist method and append its evidence to a new selection revision."""
    selection_path, out_selection, output = (selection_path.resolve(),
                                             out_selection.resolve(), output.resolve())
    if out_selection.parent != selection_path.parent:
        raise ValueError("Selection revisions must stay in one clipping directory")
    if out_selection.exists() or output.exists():
        raise ValueError("Crop output already exists; use new revision paths")
    if method not in METHODS or (method == "subjects" and not subjects):
        raise ValueError("Choose a supported crop method and supply subject boxes")
    checked = validate_selection(selection_path)
    selected = checked["selected"]
    if selected is None:
        raise ValueError("Choose a source range before proposing a crop")
    start = selected[0] if start is None else float(start)
    end = selected[1] if end is None else float(end)
    if not selected[0] - EPSILON <= start < end <= selected[1] + EPSILON:
        raise ValueError("Crop interval must stay inside the selected source range")
    record = copy.deepcopy(_read(selection_path))
    if any(start < item["source_out"] - EPSILON and end > item["source_in"] + EPSILON
           for item in record["crop_intervals"]):
        raise ValueError("Crop interval overlaps an existing proposal")
    try:
        width, height = (int(part) for part in size.lower().split("x"))
    except ValueError as error:
        raise ValueError("Crop size must be WIDTHxHEIGHT") from error
    if width < 2 or height < 2 or width % 2 or height % 2 or 16 * width != 9 * height:
        raise ValueError("Crop target must be an even 9:16 portrait canvas")
    script = VIDEO_ROOT / "edit" / "reframe" / "scripts" / f"{method}.py"
    command = [sys.executable, str(script), "--input", checked["source"],
               "--start", str(start), "--end", str(end), "--size", size,
               "--output", str(output)]
    if subjects:
        command.extend(["--subjects", str(subjects.resolve())])
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f"Crop {method} proposal failed: {result.stderr[-700:]}")
    proposal_file = output / "reframe.json"
    proposal = _read(proposal_file)
    if (proposal.get("mode") != method or proposal.get("source") != Path(checked["source"]).name
            or proposal.get("range") != [round(start, 3), round(end, 3)]):
        raise ValueError("Crop proposal does not match the requested source and method")
    crop = {
        "source_in": start, "source_out": end,
        "target_width": width, "target_height": height,
        "method": method, **proposal["crop"],
        "proposal_file": _relative_path(proposal_file, out_selection.parent),
        "proposal_sha256": sha256_file(proposal_file),
        "preview_file": _relative_path(output / "reframe-review.html", out_selection.parent),
        "review_status": "pending_review", "review_note": "",
    }
    record["crop_intervals"] = sorted([*record["crop_intervals"], crop],
                                      key=lambda item: item["source_in"])
    record["editorial_review"] = {"status": "pending_review", "reviewer": "", "note": ""}
    record["status"] = "pending_review"
    _write_new(out_selection, record)
    validate_selection(out_selection)
    return record


def emit_changes(selection_path: Path, timeline_path: Path, out: Path) -> dict:
    """Emit only pending timeline changes; approval remains the timeline owner's job."""
    selection_path, timeline_path, out = (selection_path.resolve(),
                                          timeline_path.resolve(), out.resolve())
    if out.exists():
        raise ValueError("Timeline changes output already exists")
    checked = validate_selection(selection_path, ready=True)
    timeline = load_timeline(timeline_path)
    resolved = validate_timeline(timeline, require_review=False)
    compile_graph(timeline, resolved)
    plan = _read(Path(timeline["plan_file"]))
    if not any(step.get("method_id") == "reviewed-hero-range"
               and "clipping" in str(step.get("route", ""))
               for step in plan["steps"]):
        raise ValueError("Approved preflight plan lacks the clipping method")
    if (resolved["video_policy"] != "encode" or timeline.get("color_policy") != "sdr"
            or resolved["audio_policy"] != "mix" or timeline.get("audio")
            or timeline.get("operations") or timeline.get("transitions")
            or len(resolved["clips"]) != 1):
        raise ValueError("Clipping v1 needs a clean SDR timeline with source audio")
    clip = resolved["clips"][0]
    if (clip["path"] != Path(checked["source"]) or
            clip["sha256"] != checked["source_sha256"] or
            clip["source_in"] != 0 or
            abs(clip["source_out"] - source_metadata(clip["path"])["duration"]) > 0.08):
        raise ValueError("Timeline must start from the selected full source")
    if 16 * resolved["width"] != 9 * resolved["height"]:
        raise ValueError("Timeline output must be 9:16 portrait")
    intervals = checked["crop_intervals"]
    if any((item["target_width"], item["target_height"]) !=
           (resolved["width"], resolved["height"]) for item in intervals):
        raise ValueError("Crop proposal size does not match timeline output")
    selection_hash = sha256_file(selection_path)
    manifest = _relative_evidence(selection_path,
                                  _read(selection_path)["evidence"]["manifest"],
                                  "Source evidence manifest")
    manifest_hash = sha256_file(manifest)
    picture, operations = [], []
    cursor = 0.0
    for index, item in enumerate(intervals, 1):
        length = item["source_out"] - item["source_in"]
        picture.append({"id": f"hero-p{index:04d}", "source": clip["source"],
                        "sha256": clip["sha256"], "source_in": item["source_in"],
                        "source_out": item["source_out"], "audio_gain": 1})
        proposal = _relative_evidence(selection_path, item["proposal_file"],
                                      "Crop proposal")
        operations.append({
            "id": f"hero-crop{index:04d}", "method": "crop",
            "start": round(cursor, 6), "end": round(cursor + length, 6),
            **{key: item[key] for key in ("x", "y", "w", "h")},
            "review_status": "pending_review",
            "clip_selection_file": str(selection_path),
            "clip_selection_sha256": selection_hash,
            "clip_proposal_file": str(proposal),
            "clip_proposal_sha256": item["proposal_sha256"],
            "clip_manifest_file": str(manifest),
            "clip_manifest_sha256": manifest_hash,
        })
        cursor += length
    changes = {"picture": picture, "operations": operations}
    candidate = revise(timeline, changes, new_output=timeline["output"])
    proposed = validate_timeline(candidate, require_review=False)
    compile_graph(candidate, proposed)
    _write_new(out, changes)
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    inspect = commands.add_parser("inspect", help="Create timestamped source evidence")
    inspect.add_argument("--source", type=Path, required=True)
    inspect.add_argument("--out", type=Path, required=True)
    inspect.add_argument("--hero", required=True)
    inspect.add_argument("--start", type=float)
    inspect.add_argument("--end", type=float)
    inspect.add_argument("--interval", type=float, default=5)
    crop = commands.add_parser("propose-crop", help="Create one portrait crop proposal")
    crop.add_argument("--selection", type=Path, required=True)
    crop.add_argument("--out-selection", type=Path, required=True)
    crop.add_argument("--output", type=Path, required=True)
    crop.add_argument("--method", choices=sorted(METHODS), default="subjects")
    crop.add_argument("--subjects", type=Path)
    crop.add_argument("--size", default="1080x1920")
    crop.add_argument("--start", type=float)
    crop.add_argument("--end", type=float)
    check = commands.add_parser("validate", help="Validate selection and current evidence")
    check.add_argument("--selection", type=Path, required=True)
    check.add_argument("--source", type=Path)
    check.add_argument("--ready", action="store_true")
    handoff = commands.add_parser("emit-changes", help="Write pending timeline changes")
    handoff.add_argument("--selection", type=Path, required=True)
    handoff.add_argument("--timeline", type=Path, required=True)
    handoff.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "inspect":
            record = inspect_source(args.source, args.out, args.hero,
                                    start=args.start, end=args.end,
                                    interval=args.interval)
            result = {"selection": str(args.out.resolve()),
                      "source_review": str((args.out.parent /
                                            f"{args.out.stem}-source-review").resolve()),
                      "selected": record["selected"], "status": record["status"]}
        elif args.action == "propose-crop":
            record = propose_crop(args.selection, args.out_selection, args.output,
                                  method=args.method, subjects=args.subjects,
                                  size=args.size, start=args.start, end=args.end)
            result = {"selection": str(args.out_selection.resolve()),
                      "crop_intervals": len(record["crop_intervals"]),
                      "status": record["status"]}
        elif args.action == "validate":
            result = validate_selection(args.selection, source_override=args.source,
                                        ready=args.ready)
        elif args.action == "emit-changes":
            changes = emit_changes(args.selection, args.timeline, args.out)
            result = {"changes": str(args.out.resolve()),
                      "picture_intervals": len(changes["picture"]),
                      "crop_operations": len(changes["operations"])}
        else:
            raise AssertionError(args.action)
        print(json.dumps(result, indent=2, default=str))
        return 0
    except (ValueError, OSError, KeyError, RuntimeError, json.JSONDecodeError) as error:
        parser.exit(2, f"Clipping {args.action} failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
