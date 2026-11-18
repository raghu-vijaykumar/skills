"""Audit the stealth lane's concealment, noise contrast, route, and patrol poses."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing stealth object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("stealth_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown stealth candidate")
    hero = required("SM_Stealth_Infiltrator_Rig")
    guard = required("SM_Stealth_Patrol_Guard_Rig")
    pool = required("SM_Stealth_Guard_Light_Pool")
    screen = required("SM_Stealth_Terminal_Screen")
    cam = required("Stealth shadow-and-catwalk camera")
    checks = {
        "recipe": scene.get("stealth_recipe") ==
                  "quiet shadow cover, noisy exposed plates, patrolling guard, ladder to elevated objective",
        "shadow_contrast": required("SM_Stealth_Quiet_Shadow_Lane").active_material !=
                           required("SM_Stealth_Noisy_Plate_0").active_material,
        "concealment": len([o for o in scene.objects if o.name.startswith(
            "SM_Stealth_Concealment_Crate_")]) == 3,
        "noise_material": len([o for o in scene.objects if o.name.startswith(
            "SM_Stealth_Noisy_Plate_")]) == 5,
        "vertical_route": (required("SM_Stealth_Upper_Catwalk").location.z > 2.0 and
                           required("SM_Stealth_Ladder_Left_Rail").type == "MESH" and
                           required("SM_Stealth_Ladder_Right_Rail").type == "MESH" and
                           len([o for o in scene.objects if o.name.startswith(
                               "Stealth ladder rung")]) == 5),
        "actors": (required("SM_Stealth_Infiltrator_Body").parent == hero and
                   required("SM_Stealth_Guard_Body").parent == guard and
                   required("SM_Stealth_Objective_Terminal").type == "MESH" and
                   pool.type == "MESH"),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Stealth invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 50, 72):
        scene.frame_set(frame)
        poses[frame] = {"hero_x": hero.location.x, "hero_y": hero.location.y,
                        "hero_z": hero.location.z, "guard_x": guard.location.x,
                        "pool_x": pool.location.x, "screen_scale": screen.scale.x,
                        "camera_y": cam.location.y}
    if variant == 2:
        if not (poses[50]["hero_x"] > 2.3 and
                poses[72]["hero_z"] > 2.2 and
                poses[72]["hero_y"] > 4.5 and
                poses[72]["guard_x"] > 0.6 and
                poses[72]["pool_x"] > 3.0 and
                poses[72]["screen_scale"] > 0.9 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 0.8):
            raise ValueError("Stealth infiltration or patrol motion changed")
    elif (poses[72]["hero_x"] > 0.2 or poses[72]["hero_z"] > 0.1 or
          poses[72]["screen_scale"] > 0.3):
        raise ValueError("Baseline stealth action unexpectedly changed")
    return {"variant": variant, "concealment_crates": 3, "noise_plates": 5,
            "ladder_rungs": 5, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited stealth shadow, noise, patrol, and upper route")


if __name__ == "__main__":
    main()
