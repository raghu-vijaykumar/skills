"""Validate immutable delivery timelines and resolve cut/transition timing."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

SCHEMA = "content-studio.delivery-timeline.v1"
PICTURE_METHODS = {
    "crop", "lens-correction",
    "denoise-light", "denoise-medium", "deflicker",
    "upscale-lanczos", "color-eq", "sharpen-light", "sharpen-medium",
}
GRAPHIC_METHODS = {"title", "motion-graphics-ass"}
AUDIO_METHODS = {"highpass", "audio-denoise", "compress", "loudnorm"}
JOIN_TRANSITIONS = {"cross-fade": "fade", "fade-through-black": "fadeblack",
                    "wipe-left": "wipeleft", "wipe-right": "wiperight",
                    "push-left": "slideleft", "push-right": "slideright"}
POINT_TRANSITIONS = {"fade-through-black", "fade-through-white", "cross-blur"}


def sha256_file(path: Path) -> str:
    """Hash actual bytes so a replaced asset invalidates approval."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as target:
        json.dump(value, target, indent=2, ensure_ascii=False)
        target.write("\n")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def asset_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError(f"Asset path must be relative to source_root: {relative!r}")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"Missing or unsafe asset: {relative}")
    return resolved


def _number(value: object, name: str, *, minimum: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number) or number < minimum:
        raise ValueError(f"{name} must be finite and >= {minimum}")
    return number


def make_initial(plan: Path, source: Path, output: Path, *, fps: int,
                 width: int, height: int) -> dict:
    plan = plan.resolve()
    source = source.resolve()
    output = output.resolve()
    if not plan.is_file() or not source.is_file():
        raise ValueError("Approved plan and source must exist")
    root = source.parent
    if output == source or output == plan:
        raise ValueError("Output cannot overwrite an input")
    return {
        "schema": SCHEMA, "revision": 1, "parent_sha256": None,
        "plan_file": str(plan), "plan_sha256": sha256_file(plan),
        "source_root": str(root),
        "output": str(output),
        "fps": fps, "width": width, "height": height,
        "color_policy": "sdr",
        "picture": [{"id": "p0001", "source": source.name,
                     "sha256": sha256_file(source), "source_in": 0}],
        "transitions": [], "operations": [], "audio": [],
    }


def validate(timeline: dict, *, require_review: bool = True) -> dict:
    if timeline.get("schema") != SCHEMA:
        raise ValueError("Unsupported delivery timeline schema")
    if not isinstance(timeline.get("revision"), int) or timeline["revision"] < 1:
        raise ValueError("Invalid timeline revision")
    root = Path(timeline["source_root"]).resolve()
    if not root.is_dir():
        raise ValueError("Missing source_root")
    plan = Path(timeline["plan_file"]).resolve()
    if not plan.is_file() or sha256_file(plan) != timeline.get("plan_sha256"):
        raise ValueError("Production plan changed or is missing")
    plan_data = load(plan)
    if (plan.name != "plan.json"
            or plan_data.get("schema_version") != 1
            or plan_data.get("kind") != "edited"
            or plan_data.get("stage") != "edited-render"
            or not isinstance(plan_data.get("steps"), list)
            or not plan_data["steps"]):
        raise ValueError("A versioned edited-render Content Studio plan is required")
    plan_approval = plan.with_name("approval.json")
    if not plan_approval.is_file():
        raise ValueError("Human plan approval is missing")
    approved_plan = load(plan_approval)
    if (approved_plan.get("plan_sha256") != timeline["plan_sha256"]
            or not approved_plan.get("review_note")):
        raise ValueError("Production plan approval is stale or incomplete")
    checklist = plan.with_name("checklist.json")
    if not checklist.is_file():
        raise ValueError("Approved plan checklist is missing")
    checklist_data = load(checklist)
    if (checklist_data.get("plan_sha256") != timeline["plan_sha256"]
            or [item.get("id") for item in checklist_data.get("items", [])]
            != [step.get("id") for step in plan_data["steps"]]):
        raise ValueError("Approved plan checklist is stale")
    fps = _number(timeline.get("fps"), "fps", minimum=1)
    width, height = timeline.get("width"), timeline.get("height")
    if (not isinstance(width, int) or not isinstance(height, int)
            or width < 2 or height < 2 or width % 2 or height % 2):
        raise ValueError("Output dimensions must be positive even integers")
    if timeline.get("color_policy") != "sdr":
        raise ValueError("Only reviewed SDR output is currently supported")
    output = Path(timeline["output"]).resolve()

    picture = timeline.get("picture")
    if not isinstance(picture, list) or not picture:
        raise ValueError("Timeline needs at least one picture clip")
    ids: set[str] = set()
    resolved: list[dict] = []
    for clip in picture:
        clip_id = clip.get("id")
        if not isinstance(clip_id, str) or not clip_id or clip_id in ids:
            raise ValueError("Duplicate or missing picture clip ID")
        ids.add(clip_id)
        source = asset_path(root, clip.get("source"))
        if sha256_file(source) != clip.get("sha256"):
            raise ValueError(f"Picture source changed: {clip_id}")
        gain = _number(clip.get("audio_gain", 1), f"{clip_id}.audio_gain")
        if gain > 2:
            raise ValueError("Source audio gain must be <= 2")
        source_in = _number(clip.get("source_in"), f"{clip_id}.source_in")
        source_out = clip.get("source_out")
        if source_out is None:
            raise ValueError(f"{clip_id}.source_out is required before approval")
        source_out = _number(source_out, f"{clip_id}.source_out")
        if source_out <= source_in:
            raise ValueError(f"Invalid source range: {clip_id}")
        resolved.append({**clip, "path": source, "duration": source_out - source_in,
                         "source_in": source_in, "source_out": source_out})
    transitions = timeline.get("transitions", [])
    if not isinstance(transitions, list):
        raise ValueError("transitions must be a list")
    by_after: dict[str, dict] = {}
    for cue in transitions:
        after = cue.get("after")
        if after not in ids or after == resolved[-1]["id"] or after in by_after:
            raise ValueError(f"Invalid transition boundary: {after}")
        if cue.get("id") not in JOIN_TRANSITIONS:
            raise ValueError(f"Unsupported join transition: {cue.get('id')}")
        if require_review and cue.get("review_status") != "approved":
            raise ValueError(f"Transition after {after} lacks human review")
        duration = _number(cue.get("duration"), "transition.duration", minimum=0.001)
        by_after[after] = {**cue, "duration": duration}
    cursor = 0.0
    for clip in resolved:
        clip["start"] = cursor
        clip["end"] = cursor + clip["duration"]
        overlap = by_after.get(clip["id"], {}).get("duration", 0.0)
        if overlap and overlap >= clip["duration"]:
            raise ValueError("Transition overlap must be shorter than its clip")
        cursor = clip["end"] - overlap
    duration = resolved[-1]["end"]
    for index in range(len(resolved) - 1):
        overlap = by_after.get(resolved[index]["id"], {}).get("duration", 0.0)
        if overlap and overlap >= resolved[index + 1]["duration"]:
            raise ValueError("Transition overlap must be shorter than the next clip")
    operations = timeline.get("operations", [])
    if not isinstance(operations, list):
        raise ValueError("operations must be a list")
    for item in operations:
        op_id = item.get("id")
        if not isinstance(op_id, str) or not op_id or op_id in ids:
            raise ValueError("Duplicate or missing operation ID")
        ids.add(op_id)
        kind = item.get("method")
        if kind not in PICTURE_METHODS | GRAPHIC_METHODS | AUDIO_METHODS | POINT_TRANSITIONS:
            raise ValueError(f"Unsupported timeline method: {kind}")
        if require_review and item.get("review_status") != "approved":
            raise ValueError(f"Operation {op_id} lacks human review")
        start = _number(item.get("start"), f"{op_id}.start")
        end = _number(item.get("end"), f"{op_id}.end")
        if not start < end <= duration + 1e-6:
            raise ValueError(f"Operation {op_id} is outside the resolved timeline")
        if kind in PICTURE_METHODS:
            affected = [c for c in resolved if start < c["end"] and end > c["start"]]
            if not affected:
                raise ValueError(f"Picture operation {op_id} affects no surviving frames")
        if kind == "color-eq":
            for field, low, high, default in (
                    ("brightness", -.3, .3, 0),
                    ("contrast", .5, 1.5, 1),
                    ("saturation", 0, 2, 1)):
                value = _number(item.get(field, default), f"{op_id}.{field}",
                                minimum=low)
                if value > high:
                    raise ValueError(f"{op_id}.{field} exceeds {high}")
        if kind == "crop":
            coordinates = {
                name: _number(item.get(name), f"{op_id}.{name}")
                for name in ("x", "y", "w", "h")
            }
            if (coordinates["w"] <= 0 or coordinates["h"] <= 0
                    or coordinates["x"] + coordinates["w"] > 1
                    or coordinates["y"] + coordinates["h"] > 1):
                raise ValueError(f"{op_id} crop must fit within normalized source bounds")
        if kind == "lens-correction":
            for field in ("k1", "k2"):
                value = _number(item.get(field, 0), f"{op_id}.{field}", minimum=-.5)
                if value > .5:
                    raise ValueError(f"{op_id}.{field} must be between -0.5 and 0.5")
        if kind == "upscale-lanczos" and item.get("scale") not in (2, 4):
            raise ValueError("Lanczos upscale scale must be 2 or 4")
        if kind == "title":
            font = asset_path(root, item.get("font_source"))
            if sha256_file(font) != item.get("font_sha256"):
                raise ValueError(f"Title font changed: {op_id}")
        if kind == "motion-graphics-ass":
            # ASS cues carry their own times, so the sidecar spans the full edit.
            if abs(start) > 1e-6 or abs(end - duration) > 1e-6:
                raise ValueError("ASS sidecar must span the full timeline")
            sidecar = asset_path(root, item.get("source"))
            if sidecar.suffix.lower() != ".ass" or sha256_file(sidecar) != item.get("sha256"):
                raise ValueError(f"Motion-graphics sidecar changed or is invalid: {op_id}")
    audio = timeline.get("audio", [])
    if not isinstance(audio, list):
        raise ValueError("audio must be a list")
    for cue in audio:
        cue_id = cue.get("id")
        if not isinstance(cue_id, str) or not cue_id or cue_id in ids:
            raise ValueError("Duplicate or missing audio cue ID")
        ids.add(cue_id)
        if cue.get("kind") not in {"voice", "music", "sfx"}:
            raise ValueError(f"Unsupported audio cue: {cue.get('kind')}")
        source = asset_path(root, cue.get("source"))
        if sha256_file(source) != cue.get("sha256"):
            raise ValueError(f"Audio asset changed: {cue_id}")
        if require_review and cue.get("review_status") != "approved":
            raise ValueError(f"Audio cue {cue_id} lacks human review")
        at = _number(cue.get("start"), f"{cue_id}.start")
        if at >= duration:
            raise ValueError(f"Audio cue {cue_id} starts outside the timeline")
        gain = _number(cue.get("gain", 1), f"{cue_id}.gain")
        if gain > 2:
            raise ValueError("Audio cue gain must be <= 2")
    input_paths = [c["path"] for c in resolved]
    input_paths += [asset_path(root, c["source"]) for c in audio]
    input_paths += [asset_path(root, o["font_source"]) for o in operations if o["method"] == "title"]
    input_paths += [asset_path(root, o["source"]) for o in operations if o["method"] == "motion-graphics-ass"]
    if output in input_paths or output == plan:
        raise ValueError("Output cannot overwrite an input")
    return {"clips": resolved, "transitions": by_after, "operations": operations,
            "audio": audio, "duration": duration, "fps": fps, "width": width,
            "height": height, "root": root, "output": output}


def revise(timeline: dict, changes: dict, *, new_output: str) -> dict:
    """A revision is a copy; the old bytes remain eligible for audit."""
    allowed = {"picture", "transitions", "operations", "audio", "fps",
               "width", "height", "color_policy"}
    if not isinstance(changes, dict) or not changes or set(changes) - allowed:
        raise ValueError("Revision changes contain unsupported fields")
    updated = copy.deepcopy(timeline)
    for key, value in changes.items():
        updated[key] = value
    updated["revision"] = timeline["revision"] + 1
    updated["parent_sha256"] = hashlib.sha256(
        json.dumps(timeline, sort_keys=True).encode("utf-8")).hexdigest()
    updated["output"] = str(Path(new_output).resolve())
    return updated
