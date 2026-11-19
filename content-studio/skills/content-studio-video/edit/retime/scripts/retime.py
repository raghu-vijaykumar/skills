"""Draft reviewable retime changes and bounded previews for a delivery timeline."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "timeline" / "scripts"))
from compiler import compile_graph, media_info, preview  # noqa: E402
from model import load, revise, sha256_file, validate, write_new  # noqa: E402


def propose(timeline_path: Path, clip_id: str, source_start: float, source_end: float,
            retime: dict, final_output: Path) -> tuple[dict, dict]:
    timeline = load(timeline_path)
    baseline = validate(timeline, require_review=False)
    if baseline["transitions"]:
        raise ValueError("Retime proposal does not remap existing join transitions")
    match = next((clip for clip in baseline["clips"] if clip["id"] == clip_id), None)
    if not match or "retime_resolved" in match:
        raise ValueError("Select one unretimed picture clip")
    if (not match["source_in"] <= source_start < source_end <= match["source_out"]
            or source_end - source_start < 1 / baseline["fps"] - .002):
        raise ValueError("Retime source span is outside the selected clip")
    if (retime.get("method") == "speed" and
            isinstance(retime.get("factor"), (int, float)) and
            abs(retime["factor"] - 1) < .01):
        return {}, {"status": "SKIP", "issue": "requested speed is effectively unchanged",
                    "baseline": {"timeline_sha256": sha256_file(timeline_path),
                                 "source_sha256": match["sha256"],
                                 "duration_seconds": baseline["duration"]},
                    "fallback": "Keep the original clip and timeline revision"}
    start = match["start"] + source_start - match["source_in"]
    end = match["start"] + source_end - match["source_in"]
    pictures = []
    original = next(clip for clip in timeline["picture"] if clip["id"] == clip_id)
    for item in timeline["picture"]:
        if item["id"] != clip_id:
            pictures.append(copy.deepcopy(item))
            continue
        if source_start > match["source_in"] + .002:
            before = {**original, "id": f"{clip_id}-before", "source_out": source_start}
            pictures.append(before)
        changed = {**original, "id": f"{clip_id}-retime",
                   "source_in": source_start, "source_out": source_end,
                   "retime": retime, "retime_review_status": "pending_review"}
        pictures.append(changed)
        if source_end < match["source_out"] - .002:
            after = {**original, "id": f"{clip_id}-after", "source_in": source_end}
            pictures.append(after)
    if len({item["id"] for item in pictures}) != len(pictures):
        raise ValueError("Retime split would duplicate a picture ID")
    operations = copy.deepcopy(timeline["operations"])
    audio = copy.deepcopy(timeline["audio"])
    # An operation crossing the new span needs a human timing decision; never
    # stretch narration or visual cues silently. Whole-mix loudnorm is global.
    for item in operations:
        if item["method"] in {"motion-graphics-ass", "object-blur"} and item["end"] > start:
            raise ValueError(f"{item['method']} {item['id']} needs regenerated timing or masks after retime")
        if item["method"] == "loudnorm" and abs(item["start"]) < .001 and abs(
                item["end"] - baseline["duration"]) < .001:
            continue
        if item["end"] > start + .001 and item["start"] < end - .001:
            raise ValueError(f"Operation {item['id']} overlaps retime; review its timing first")
    for cue in audio:
        if cue["kind"] == "external_sync":
            raise ValueError("External sync must be redone after a retime")
        source = baseline["root"] / cue["source"]
        length = float(cue["duration"]) if cue.get("loop") else media_info(source)["duration"]
        if cue["start"] < end - .001 and cue["start"] + length > start + .001:
            raise ValueError(f"Audio cue {cue['id']} crosses retime; review placement first")
    changes = {"picture": pictures, "operations": operations, "audio": audio}
    # Resolve the proposed picture before shifting later cues. This also
    # triggers format, frame timing, duration, and audio-policy guards.
    initial = revise(timeline, {"picture": pictures, "operations": [], "audio": []},
                     new_output=str(final_output))
    temporary = validate(initial, require_review=False)
    selected = next(clip for clip in temporary["clips"] if clip["id"] == f"{clip_id}-retime")
    delta = selected["duration"] - (source_end - source_start)
    for item in operations:
        if item["method"] == "loudnorm" and abs(item["start"]) < .001 and abs(
                item["end"] - baseline["duration"]) < .001:
            item["end"] += delta
        elif item["start"] >= end - .001:
            item["start"] += delta
            item["end"] += delta
    for cue in audio:
        if cue["start"] >= end - .001:
            cue["start"] += delta
    changes["operations"] = operations
    changes["audio"] = audio
    proposed = revise(timeline, changes, new_output=str(final_output))
    resolved = validate(proposed, require_review=False)
    compile_graph(proposed, resolved)
    report = {
        "status": "REVIEW", "issue": "requested source range needs a finite retime",
        "baseline": {"timeline_sha256": sha256_file(timeline_path),
                     "source_sha256": match["sha256"],
                     "duration_seconds": baseline["duration"],
                     "source_range": [source_start, source_end]},
        "candidate": {"method": retime["method"], "source_audio": retime["audio"],
                      "resolved_duration_seconds": selected["duration"],
                      "new_timeline_duration_seconds": resolved["duration"],
                      "downstream_shift_seconds": delta,
                      "effective_factor": selected["retime_resolved"]["effective_factor"]},
        "acceptance": "Review motion, sound, total duration and every shifted cue in bounded preview; then verify exact master",
        "human_preview_review": "pending", "exact_master_review": "pending",
        "fallback": "Keep the original clip and timeline revision",
    }
    return changes, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    draft = commands.add_parser("propose")
    draft.add_argument("--timeline", type=Path, required=True)
    draft.add_argument("--clip-id", required=True)
    draft.add_argument("--source-start", type=float, required=True)
    draft.add_argument("--source-end", type=float, required=True)
    draft.add_argument("--method", choices=["speed", "freeze", "reverse", "loop"], required=True)
    draft.add_argument("--factor", type=float)
    draft.add_argument("--hold-seconds", type=float)
    draft.add_argument("--count", type=int)
    draft.add_argument("--audio", choices=["tempo", "mute", "reverse", "repeat"], required=True)
    draft.add_argument("--changes", type=Path, required=True)
    draft.add_argument("--report", type=Path, required=True)
    draft.add_argument("--final-output", type=Path, required=True)
    sample = commands.add_parser("preview")
    sample.add_argument("--timeline", type=Path, required=True)
    sample.add_argument("--start", type=float, required=True)
    sample.add_argument("--duration", type=float, required=True)
    sample.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "preview":
            timeline = load(args.timeline)
            result = preview(timeline, validate(timeline, require_review=False),
                             args.out, args.start, args.duration)
        else:
            if (args.changes.resolve() == args.report.resolve()
                    or args.changes.exists() or args.report.exists()):
                raise ValueError("Proposal files already exist")
            retime = {"method": args.method, "audio": args.audio}
            selected = {"speed": ("factor", args.factor),
                        "freeze": ("hold_seconds", args.hold_seconds),
                        "loop": ("count", args.count)}.get(args.method)
            if selected:
                retime[selected[0]] = selected[1]
            changes, result = propose(args.timeline, args.clip_id,
                                      args.source_start, args.source_end,
                                      retime, args.final_output)
            if result["status"] != "SKIP":
                write_new(args.changes, changes)
                result["changes_file"] = str(args.changes.resolve())
            write_new(args.report, result)
            result["report_file"] = str(args.report.resolve())
        print(json.dumps(result, indent=2, default=str))
        return 0
    except (ValueError, OSError, KeyError, RuntimeError) as exc:
        parser.exit(2, f"Retime {args.action} failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
