"""Audit the authored reading-nook recipe and its warm, gentle motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing cozy nook object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    chair = required("SM_Nook_Rocking_Chair_Rig")
    seat = required("SM_Nook_Sage_Chair_Seat")
    lamp = required("SM_Nook_Warm_Reading_Light")
    camera = required("Cozy nook friendly-eye camera")
    bulb = bpy.data.materials.get("Nook warm lamp bulb")
    leaves = [required(f"Nook safe plant leaf {i}") for i in range(7)]
    books = [required(f"Nook safe shelf book {level} {i}")
             for level in range(2) for i in range(5)]
    rocker = [required(f"Nook walnut rocker rail {side}") for side in (-1, 1)]
    variant = scene.get("cozy_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown cozy candidate")
    checks = {
        "recipe": scene.get("cozy_recipe") ==
                  "warm soft key and fill, rounded sage chair, safe books and plant, gentle rocking, friendly-eye camera",
        "soft_hero": seat.parent == chair and len(rocker) == 2 and
                     all(obj.parent == chair for obj in rocker) and
                     any(mod.type == "BEVEL" for mod in seat.modifiers),
        "safe_clutter": (len(leaves), len(books)) == (7, 10) and
                        required("Nook tea mug").type == "MESH" and
                        required("SM_Nook_Round_Rug").type == "MESH",
        "soft_lighting": all(required(name).type == "LIGHT" for name in
                             ("Nook soft window key", "Nook warm soft fill")) and
                         lamp.type == "LIGHT" and lamp.data.shape == "DISK",
        "camera": camera.type == "CAMERA" and bool(camera.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Cozy nook invariants failed: " + ", ".join(failed))
    glow = bulb.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    poses = {}
    for frame in (1, 24, 48, 72):
        scene.frame_set(frame)
        poses[frame] = {"chair_rotation_x": chair.rotation_euler.x,
                        "lamp_watts": lamp.data.energy,
                        "bulb_emission": glow.default_value,
                        "camera_y": camera.location.y}
    if variant == 2:
        if not (poses[24]["chair_rotation_x"] > 0.07 and
                poses[48]["chair_rotation_x"] < -0.06 and
                poses[48]["lamp_watts"] > poses[1]["lamp_watts"] * 4 and
                poses[48]["bulb_emission"] > poses[1]["bulb_emission"] * 10 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 1):
            raise ValueError("Chair, light, bulb, or camera animation lost")
    else:
        if abs(poses[72]["chair_rotation_x"]) > 0.01:
            raise ValueError("Baseline chair motion unexpectedly changed")
    return {"variant": variant, "chair_parts":
            len([obj for obj in scene.objects if obj.parent == chair]),
            "plant_leaves": len(leaves), "shelf_books": len(books),
            "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited cozy nook furniture, light, clutter, and motion")


if __name__ == "__main__":
    main()
