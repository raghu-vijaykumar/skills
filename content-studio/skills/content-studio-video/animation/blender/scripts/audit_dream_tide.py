"""Audit unsupported geometry, symbolic scale, and the dream-tide reveal."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing dream-tide object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    door = required("SM_Dream_Opening_Door_Rig")
    panel = required("SM_Dream_Rose_Door_Panel")
    ring = required("SM_Dream_Revealed_Lunar_Ring")
    key = required("SM_Dream_Giant_Key_Ring")
    boat = required("SM_Dream_Tiny_Boat_Rig")
    cam = required("Dream tide witness camera")
    steps = [required(f"SM_Dream_Floating_Step_{i}") for i in range(8)]
    variant = scene.get("dream_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown dream-tide candidate")
    checks = {
        "recipe": scene.get("dream_recipe") ==
                  "unsupported doorway, giant symbolic key, tiny boat, levitating stairs, soft pastel physics",
        "unsupported_threshold": (required("SM_Dream_Unsupported_Doorway").type == "MESH"
                                  and panel.parent == door and
                                  required("Dream door keyhole crown").parent == door and
                                  required("Dream door keyhole stem").parent == door),
        "lunar_reveal": ring.type == "MESH" and
                        bpy.data.materials["Dream revealed lunar portal symbol"].node_tree.nodes[
                            "Principled BSDF"].inputs["Emission Strength"].default_value >= 3,
        "scale_play": (key.get("scale_play") == "giant key beside tiny boat" and
                       required("Dream giant key shaft").dimensions.z >
                       required("SM_Dream_Small_Boat_Hull").dimensions.x * 2),
        "soft_stairs": len(steps) == 8 and
                       all(step.get("unsupported") is True for step in steps),
        "pastel_lighting": all(required(name).type == "LIGHT" for name in
                               ("Dream large peach softbox", "Dream lilac door rim",
                                "Dream low misty fill")),
        "camera": cam.type == "CAMERA" and bool(cam.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Dream-tide invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        poses[frame] = {"door_rotation_z": door.rotation_euler.z,
                        "first_step_z": steps[0].location.z,
                        "boat_y": boat.location.y,
                        "camera_y": cam.location.y}
    if variant == 2:
        if not (poses[72]["door_rotation_z"] < -1.1 and
                poses[36]["first_step_z"] > poses[1]["first_step_z"] + 0.17 and
                poses[72]["boat_y"] > poses[1]["boat_y"] + 2 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 1):
            raise ValueError("Door, levitation, boat, or camera motion changed")
    elif abs(poses[72]["door_rotation_z"]) > 0.06:
        raise ValueError("Baseline door motion unexpectedly changed")
    return {"variant": variant, "floating_steps": len(steps),
            "tide_ripples": 6, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited dream doorway, symbolic scale, levitation, and reveal")


if __name__ == "__main__":
    main()
