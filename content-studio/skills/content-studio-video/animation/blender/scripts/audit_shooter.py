"""Audit the shooter lane's camera height, cover, landmark, and peek timing."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing shooter object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    cam = required("Shooter human-height first-person camera")
    target_rig = required("SM_Shooter_Target_Rig")
    lid = required("SM_Shooter_Loot_Case_Lid")
    muzzle = required("SM_Shooter_Muzzle_Flash")
    variant = scene.get("shooter_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown shooter candidate")
    checks = {
        "recipe": scene.get("shooter_recipe") ==
                  "human-height first-person peek, asymmetrical cover, open sightline, orange landmark, lime loot",
        "camera_height": (cam.type == "CAMERA" and cam["eye_height_m"] == 1.68 and
                          required("SM_Shooter_Visible_Gun_Body").parent == cam and
                          muzzle.parent == cam),
        "sightline_and_cover": (required("SM_Shooter_Near_Chest_Cover").dimensions.z >= 1.6 and
                                required("SM_Shooter_Mid_Half_Cover").dimensions.z >= 1.24 and
                                all(required(f"Shooter broken lane dash {i}").type == "MESH"
                                    for i in range(9)) and
                                len([o for o in scene.objects if o.name.startswith("Shooter reticle")]) == 4),
        "navigation_and_loot": (required("SM_Shooter_Orange_Landmark_Tower").dimensions.z > 6.6 and
                                required("SM_Shooter_Lime_Loot_Case").type == "MESH" and
                                lid.type == "MESH"),
        "target_silhouette": (required("SM_Shooter_Red_Target").parent == target_rig and
                              required("Shooter target head").parent == target_rig and
                              all(required(f"Shooter target arm {side}").parent == target_rig and
                                  required(f"Shooter target leg {side}").parent == target_rig
                                  for side in (-1, 1))),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Shooter invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 51, 72):
        scene.frame_set(frame)
        poses[frame] = {"camera_x": cam.location.x, "camera_y": cam.location.y,
                        "target_tilt_x": target_rig.rotation_euler.x,
                        "loot_lid_z": lid.location.z,
                        "muzzle_scale": muzzle.scale.x}
    if variant == 2:
        if not (poses[51]["camera_x"] > poses[1]["camera_x"] + 1 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 2 and
                poses[51]["muzzle_scale"] > 0.9 and
                poses[72]["target_tilt_x"] > 1 and
                poses[72]["loot_lid_z"] > 1.1):
            raise ValueError("Peek, shot, target fall, or loot opening changed")
    elif (poses[72]["camera_x"] > poses[1]["camera_x"] + 0.3 or
          poses[51]["muzzle_scale"] > 0):
        raise ValueError("Baseline action unexpectedly changed")
    return {"variant": variant, "eye_height_m": cam["eye_height_m"],
            "lane_dashes": 9, "reticle_marks": 4, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited shooter cover, camera height, landmark, loot, and peek")


if __name__ == "__main__":
    main()
