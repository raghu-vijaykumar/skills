"""Audit the archive's monumental scale, material restraint, and shutter motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing brutalist object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    left = required("SM_Archive_Left_Monolith")
    right = required("SM_Archive_Right_Monolith")
    gate = required("SM_Archive_Sliding_Gate_Rig")
    person = required("SM_Archive_Tiny_Witness_Rig")
    cam = required("Archive low witness camera")
    shutter = required("SM_Archive_Concrete_Shutter")
    concrete = bpy.data.materials["Archive raw gray board-formed concrete"]
    used_materials = {material.name for obj in scene.objects if obj.type == "MESH"
                      for material in obj.data.materials if material}
    variant = scene.get("brutalist_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown brutalist archive candidate")
    key = required("Archive hard high concrete key")
    fill = required("Archive restrained stone fill")
    checks = {
        "recipe": scene.get("brutalist_recipe") ==
                  "monumental raw concrete, board-form seams, one tiny witness, deep gate shadow, austere low camera",
        "monumental_scale": (min(left.dimensions.z, right.dimensions.z) / person["height_m"] > 6
                             and required("SM_Archive_Cantilever_Crown").dimensions.x >= 13),
        "concrete_craft": (all(required(f"Archive board-form seam {side} {i}").type == "MESH"
                               for side in (-1, 1) for i in range(7)) and
                           all(required(f"Archive concrete tie hole {side} {i}").type == "MESH"
                               for side in (-1, 1) for i in range(4)) and
                           concrete.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value >= 0.9),
        "restrained_materials": len(used_materials) == 5,
        "aperture_mechanism": (required("SM_Archive_Recessed_Dark_Void").type == "MESH"
                               and shutter.parent == gate and
                               all(required(f"Archive heavy gate track {i}").type == "MESH"
                                   for i in range(2))),
        "lighting": key.type == fill.type == "LIGHT" and fill.data.energy < key.data.energy / 4,
        "camera": cam.type == "CAMERA" and bool(cam.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Brutalist invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 48, 72):
        scene.frame_set(frame)
        poses[frame] = {"gate_x": gate.location.x, "witness_y": person.location.y,
                        "camera_y": cam.location.y}
    if variant == 2:
        if not (poses[48]["gate_x"] > 2 and poses[72]["gate_x"] > 4 and
                poses[72]["witness_y"] > 4 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 2):
            raise ValueError("Shutter, witness, or camera motion changed")
    elif poses[72]["gate_x"] > 0.2 or poses[72]["witness_y"] > 0.2:
        raise ValueError("Baseline motion unexpectedly changed")
    return {"variant": variant, "material_count": len(used_materials),
            "board_seams": 14, "tie_holes": 8,
            "monolith_to_witness_ratio": min(left.dimensions.z, right.dimensions.z) / person["height_m"],
            "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited concrete scale, restraint, gateway, and motion")


if __name__ == "__main__":
    main()
