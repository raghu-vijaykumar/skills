"""Validate the portable contract for project-authored headless Blender shots."""

import hashlib
from pathlib import Path
import re

ID = re.compile(r"[a-z][a-z0-9-]*\Z")
ORIGINS = {"procedural", "generated", "recorded", "licensed"}


def _identifier(value, label):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError(f"{label} must be a stable lowercase ID")
    return value


def _integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer from {low} to {high}")
    return value


def validate_spec(spec, spec_dir):
    """Return reviewed IDs and fingerprints; legacy gallery specs remain readable."""
    if not isinstance(spec, dict):
        raise ValueError("Shot specification must be a JSON object")
    version = spec.get("schema_version", 1)
    if version == 1:
        return {"schema_version": 1, "required_objects": spec.get("required_objects", []),
                "review_frames": spec.get("review_frames", []), "asset_hashes": {}}
    if version != 2:
        raise ValueError(f"Unsupported shot specification version: {version}")
    shot_id = _identifier(spec.get("id"), "shot id")
    _integer(spec.get("width"), 320, 3840, "width")
    _integer(spec.get("height"), 240, 2160, "height")
    _integer(spec.get("fps"), 12, 60, "fps")
    last = _integer(spec.get("frames"), 3, 100000, "frames")
    if spec.get("render_engine") not in {"BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"}:
        raise ValueError("Shot needs a supported Blender render engine")
    if spec.get("codec") != "H264":
        raise ValueError("Shot codec must be H264")
    if not isinstance(spec.get("color_transform"), str) or not spec["color_transform"]:
        raise ValueError("Shot needs a color transform")

    objects = spec.get("objects")
    if not isinstance(objects, list) or not objects:
        raise ValueError("Shot needs stable object IDs")
    ids, names = set(), set()
    for obj in objects:
        if not isinstance(obj, dict):
            raise ValueError("Object records must be JSON objects")
        object_id = _identifier(obj.get("id"), "object id")
        name = obj.get("name")
        if not isinstance(name, str) or not name or object_id in ids or name in names:
            raise ValueError("Object IDs and Blender names must be unique and nonempty")
        ids.add(object_id)
        names.add(name)
    camera_name = spec.get("camera_object")
    if camera_name not in names:
        raise ValueError("camera_object must name a declared object")

    beats = spec.get("beats")
    if not isinstance(beats, list) or len(beats) < 3:
        raise ValueError("Shot needs initial, action, and result beats")
    beat_ids, beat_frames = set(), []
    for beat in beats:
        if not isinstance(beat, dict):
            raise ValueError("Beat records must be JSON objects")
        beat_id = _identifier(beat.get("id"), "beat id")
        frame = _integer(beat.get("frame"), 1, last, "beat frame")
        referenced = beat.get("object_ids")
        if (beat_id in beat_ids or not isinstance(beat.get("label"), str) or
                not beat["label"].strip() or not isinstance(referenced, list) or
                any(object_id not in ids for object_id in referenced)):
            raise ValueError(f"Invalid beat or object reference: {beat_id}")
        beat_ids.add(beat_id)
        beat_frames.append(frame)
    if beat_frames != sorted(set(beat_frames)) or beat_frames[0] != 1 or beat_frames[-1] != last:
        raise ValueError("Beats must have unique ascending frames from first to last")
    reviewed = spec.get("review_states")
    if (not isinstance(reviewed, list) or len(reviewed) < 3 or
            len(reviewed) != len(set(reviewed)) or
            not {beats[0]["id"], beats[-1]["id"]}.issubset(reviewed) or
            not any(beat_id not in {beats[0]["id"], beats[-1]["id"]}
                    for beat_id in reviewed) or
            any(beat_id not in beat_ids for beat_id in reviewed)):
        raise ValueError("Review states must cover initial, action, and result")

    assets = spec.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("Shot needs asset provenance")
    asset_ids, asset_hashes = set(), {}
    base = Path(spec_dir).resolve()
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("Asset records must be JSON objects")
        asset_id = _identifier(asset.get("id"), "asset id")
        if (asset_id in asset_ids or asset.get("origin") not in ORIGINS or
                not isinstance(asset.get("license"), str) or not asset["license"].strip()):
            raise ValueError(f"Invalid asset origin or license: {asset_id}")
        asset_ids.add(asset_id)
        source = asset.get("path")
        if asset["origin"] == "procedural":
            if source is not None:
                raise ValueError("Procedural assets use builder dependencies, not imported paths")
            continue
        if not isinstance(source, str) or not source:
            raise ValueError(f"Imported asset needs a path: {asset_id}")
        path = (base / source).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            raise ValueError(f"Asset path escapes the shot or is missing: {asset_id}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if asset.get("sha256") != digest:
            raise ValueError(f"Asset hash mismatch: {asset_id}")
        asset_hashes[source] = digest
    return {"schema_version": 2, "id": shot_id, "required_objects": sorted(names),
            "camera_object": camera_name, "object_ids": sorted(ids),
            "beat_ids": [beat["id"] for beat in beats],
            "review_frames": [beat["frame"] for beat in beats if beat["id"] in reviewed],
            "asset_hashes": asset_hashes}


def validate_scene(scene, spec, contract):
    """Compare authored scene settings and object inventory with the reviewed spec."""
    if contract["schema_version"] != 2:
        return
    if (scene.render.resolution_x != spec["width"] or
            scene.render.resolution_y != spec["height"] or
            scene.render.resolution_percentage != 100 or
            scene.render.fps != spec["fps"] or scene.frame_start != 1 or
            scene.frame_end != spec["frames"]):
        raise ValueError("Blender scene timing or dimensions differ from shot specification")
    if (scene.render.engine != spec["render_engine"] or
            scene.view_settings.view_transform != spec["color_transform"]):
        raise ValueError("Blender render settings differ from shot specification")
    if scene.camera is None or scene.camera.name != contract["camera_object"]:
        raise ValueError("Blender camera differs from shot specification")
    missing = [name for name in contract["required_objects"] if name not in scene.objects]
    if missing:
        raise ValueError("Declared Blender objects are missing: " + ", ".join(missing))
