"""Audit the reduced three-color pendulum and its diminishing swing."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing minimal object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    base = required("SM_Minimal_Base")
    support = required("SM_Minimal_Support")
    pivot = required("Minimal pendulum pivot")
    rod = required("SM_Minimal_Rod")
    bob = required("SM_Minimal_Red_Bob")
    cam = required("Minimal pendulum camera")
    required("Minimal upper beam")
    required("Minimal seamless floor")
    required("Minimal seamless wall")
    materials = [mat for mat in bpy.data.materials if mat.name.startswith("Minimal ")]
    arc = bpy.data.objects.get("Minimal swing arc")
    pin = bpy.data.objects.get("Minimal visible pivot pin")
    if (not base.get("reduced_form") or rod.parent != pivot or bob.parent != pivot or
            base.dimensions.x > 1.5 or support.dimensions.z > 2.2 or
            cam.data.type != "ORTHO" or cam.animation_data or
            abs(cam.data.ortho_scale - 6.45) > 0.001 or
            scene.get("negative_space_side") != "right" or
            len(materials) != 3 or
            scene.get("minimal_palette") != "warm bone, matte charcoal, one red accent" or
            bool(arc) != bool(pin)):
        raise ValueError("The reduced form, palette, or negative-space framing changed")
    if arc and (arc.type != "CURVE" or len(arc.data.splines[0].points) != 17):
        raise ValueError("The single hairline travel arc changed")
    samples = {}
    for frame in (1, 20, 38, 56, 72):
        scene.frame_set(frame)
        samples[frame] = {"swing_rad": pivot.rotation_euler.y,
                          "bob_world_x_m": bob.matrix_world.translation.x,
                          "bob_world_z_m": bob.matrix_world.translation.z}
    if (not pivot.animation_data or
            samples[1]["swing_rad"] > -0.75 or
            samples[20]["swing_rad"] < 0.75 or
            samples[38]["swing_rad"] > -0.65 or
            samples[56]["swing_rad"] < 0.50 or
            abs(samples[72]["swing_rad"]) > 0.4 or
            samples[20]["bob_world_x_m"] >= samples[1]["bob_world_x_m"]):
        raise ValueError("The pendulum stopped swinging or lost its damping")
    return {"limited_palette_materials": [mat.name for mat in materials],
            "visible_pivot_pin": bool(pin), "single_travel_arc": bool(arc),
            "negative_space_side": "right", "fixed_orthographic_camera": True,
            "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited three-color palette, negative space and diminishing swing")


if __name__ == "__main__":
    main()
