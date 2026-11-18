"""Check narrow horror geometry, eye-height push, sparse prop, fog and flicker."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing horror scene object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    floor = required("SM_Horror_Floor")
    ceiling = required("SM_Horror_Ceiling")
    cam = required("Horror eye camera")
    chair = required("SM_Horror_Chair_Seat")
    hinge = required("Horror door hinge")
    handle = required("SM_Horror_Door_Handle")
    fog = required("Horror corridor fog")
    tube = required("SM_Horror_Fluorescent_Tube")
    practical = required("Horror single practical")
    warm = required("Horror distant warm bleed")
    if abs(floor.dimensions.x - 1.44) > 1e-5 or abs(ceiling.location.z - 2.36) > 1e-5:
        raise ValueError("The claustrophobic hallway dimensions changed")
    if cam.data.type != "PERSP" or abs(cam.location.z - 1.6) > 1e-5:
        raise ValueError("Player-eye camera must stay 1.6 m above the floor")
    if handle.parent != hinge or chair.type != "MESH":
        raise ValueError("Narrative chair or door mechanism is incomplete")
    seats = [obj for obj in bpy.data.objects if obj.name.startswith("SM_Horror_Chair_Seat")]
    if len(seats) != 1:
        raise ValueError("Horror scene must keep one narrative chair")
    volume = next((node for node in fog.data.materials[0].node_tree.nodes
                   if node.bl_idname == "ShaderNodeVolumePrincipled"), None)
    if not volume or not 0.015 <= volume.inputs["Density"].default_value <= 0.05:
        raise ValueError("Fog volume or restrained density is missing")
    if not tube.get("single_flicker_source") or not practical.data.animation_data:
        raise ValueError("The single fluorescent source must be keyed")
    samples = {}
    for frame in (1, 33, 49, 72):
        scene.frame_set(frame)
        samples[frame] = {"camera_y": cam.location.y,
                          "door_rad": hinge.rotation_euler.z,
                          "light_power": practical.data.energy}
    if (samples[72]["camera_y"] - samples[1]["camera_y"] < 1 or
            samples[72]["door_rad"] > -0.5 or
            samples[33]["light_power"] > 12 or samples[49]["light_power"] > 12 or
            samples[1]["light_power"] / warm.data.energy < 8):
        raise ValueError("The eye-height push, reveal, or high-contrast flicker failed")
    return {"corridor_width_m": 1.44, "ceiling_height_m": 2.3,
            "camera_eye_height_m": 1.6, "narrative_chairs": len(seats),
            "fog_density": volume.inputs["Density"].default_value,
            "key_to_warm_fill_ratio": samples[1]["light_power"] / warm.data.energy,
            "sampled_frames": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Audited narrow fog corridor, eye-height push and single flicker")


if __name__ == "__main__":
    main()
