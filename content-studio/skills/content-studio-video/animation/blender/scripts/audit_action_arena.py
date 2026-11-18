"""Audit the combat arena's clear fight plane, actor controls, and impact timing."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing action arena object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    hero = required("SM_Arena_Hero_Rig")
    rival = required("SM_Arena_Rival_Rig")
    sword = required("SM_Arena_Sword_Pivot")
    shield = required("SM_Arena_Shield_Pivot")
    burst = required("SM_Arena_Impact_Burst_Rig")
    chunks = [required(f"SM_Arena_Breakable_Clay_Chunk_{i}") for i in range(4)]
    variant = scene.get("arena_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown action arena candidate")
    checks = {
        "recipe": scene.get("arena_recipe") ==
                  "clear octagonal arena, blue blade versus coral shield, readable breakable clay, unobstructed camera",
        "fight_plane": required("SM_Arena_Readable_Octagonal_Ring").type == "MESH" and
                       required("Arena clear central fight plane").type == "MESH" and
                       len([o for o in scene.objects if o.name.startswith("Arena low corner marker")]) == 4,
        "fighter_silhouettes": (required("SM_Arena_Hero_Blade").parent == sword and
                                sword.parent == hero and
                                required("SM_Arena_Rival_Shield").parent == shield and
                                shield.parent == rival),
        "breakables": len(chunks) == 4 and all(o.type == "MESH" for o in chunks),
        "impact": burst.type == "EMPTY" and
                  len([o for o in scene.objects if o.name.startswith("Arena impact spoke")]) == 6,
        "camera": required("Arena unobstructed combat camera").type == "CAMERA",
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Action arena invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 53, 72):
        scene.frame_set(frame)
        poses[frame] = {"hero_x": hero.location.x,
                        "sword_y_rotation": sword.rotation_euler.y,
                        "shield_y_rotation": shield.rotation_euler.y,
                        "impact_scale": burst.scale.x,
                        "chunk_0_x": chunks[0].location.x,
                        "rival_x": rival.location.x}
    if variant == 2:
        if not (poses[53]["hero_x"] > 1.3 and
                poses[53]["sword_y_rotation"] > 1 and
                poses[53]["shield_y_rotation"] < -0.8 and
                poses[53]["impact_scale"] > 0.7 and
                poses[72]["chunk_0_x"] < poses[1]["chunk_0_x"] - 0.6 and
                poses[72]["rival_x"] > 0.6):
            raise ValueError("Sword clash, recoil, or breakable motion changed")
    elif poses[72]["hero_x"] > 0.2 or poses[53]["impact_scale"] > 0:
        raise ValueError("Baseline action unexpectedly changed")
    return {"variant": variant, "breakable_chunks": 4, "impact_spokes": 6,
            "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited action arena, combat controls, impact, and breakables")


if __name__ == "__main__":
    main()
