"""Audit the depot's industrial wear, low-key light, and gantry motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing freight-depot object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    load = required("SM_Depot_Suspended_Load_Rig")
    beam = required("SM_Depot_Gantry_Beam")
    hook = required("SM_Depot_Crane_Hook")
    cage = required("SM_Depot_Cargo_Cage_Base")
    cam = required("Gritty depot inspection camera")
    steel = bpy.data.materials["Depot oxidized structural steel"]
    nodes = steel.node_tree.nodes
    variant = scene.get("dark_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown dark-depot candidate")
    checks = {
        "recipe": scene.get("dark_recipe") ==
                  "low-key cold shaft, lone warm practical, oxidized industrial weight, flaking repair, lonely moving load",
        "gantry": beam.type == "MESH" and hook.parent == load and
                  cage.parent == load and
                  all(required(f"Depot heavy chain link {i}").parent == load
                      for i in range(11)),
        "industrial_weight": all(required(f"Depot overhead truss {i}").type == "MESH"
                                 for i in range(5)) and
                             all(required(f"Depot structural upright {i} {side}").type == "MESH"
                                 for i in range(5) for side in (-1, 1)),
        "wear_as_story": (any(node.type == "TEX_NOISE" for node in nodes) and
                          any(node.type == "VALTORGB" for node in nodes) and
                          all(required(f"Depot chipped paint patch {i}").type == "MESH"
                              for i in range(9)) and
                          all(required(f"Depot shutter rust drip {i}").type == "MESH"
                              for i in range(5)) and
                          required("Depot cage flaking repair plate").parent == load),
        "low_key_lighting": all(required(name).type == "LIGHT" for name in
                                ("Depot cold roof shaft", "Depot lonely warm practical",
                                 "Depot dark steel fill")) and
                            required("Depot dark steel fill").data.energy <
                            required("Depot cold roof shaft").data.energy / 4,
        "camera": cam.type == "CAMERA" and bool(cam.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Dark depot invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 38, 72):
        scene.frame_set(frame)
        poses[frame] = {"load_x": load.location.x,
                        "load_z": load.location.z,
                        "load_swing_y": load.rotation_euler.y,
                        "camera_y": cam.location.y}
    if variant == 2:
        if not (poses[38]["load_x"] > 2.3 and
                poses[72]["load_x"] > 4.1 and
                abs(poses[38]["load_swing_y"]) > 0.01 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 1 and
                abs(poses[72]["load_z"]) < 0.01):
            raise ValueError("Gantry travel, swing, camera, or beam contact changed")
    elif poses[72]["load_x"] > 0.2:
        raise ValueError("Baseline load motion unexpectedly changed")
    return {"variant": variant, "chain_links": 11, "trusses": 5,
            "paint_chips": 9, "rust_drips": 5, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited dark freight depot wear, lighting, and gantry travel")


if __name__ == "__main__":
    main()
