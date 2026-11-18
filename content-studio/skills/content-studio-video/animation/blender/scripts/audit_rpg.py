"""Audit the RPG hub's regions, quest cue, class gear, rarity, and reveal."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing RPG object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    marker = required("SM_RPG_Quest_Marker_Rig")
    lid = required("SM_RPG_Rare_Chest_Lid_Rig")
    gem = required("SM_RPG_Rare_Loot_Gem")
    cam = required("RPG quest hub camera")
    variant = scene.get("rpg_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown RPG candidate")
    common = required("SM_RPG_Common_Loot_Pedestal")
    rare = required("SM_RPG_Rare_Chest")
    epic = required("SM_RPG_Epic_Loot_Pedestal")
    checks = {
        "recipe": scene.get("rpg_recipe") ==
                  "split-region quest hub, class-readable warrior and mage gear, common rare epic loot colors, rising quest marker",
        "region_identity": (required("SM_RPG_Forest_Region").type == "MESH" and
                            required("SM_RPG_Highland_Region").type == "MESH" and
                            all(required(f"RPG forest pine {i}").type == "MESH" for i in range(3)) and
                            all(required(f"RPG highland standing stone {i}").type == "MESH" for i in range(3))),
        "quest_hub": (required("SM_RPG_Guild_Quest_Board").type == "MESH" and
                      required("SM_RPG_Quest_Exclamation").parent == marker and
                      required("RPG quest exclamation dot").parent == marker),
        "class_gear": (required("SM_RPG_Warrior_Sword").type == "MESH" and
                       required("SM_RPG_Warrior_Shield").type == "MESH" and
                       required("SM_RPG_Mage_Hat").type == "MESH" and
                       required("SM_RPG_Mage_Staff").type == "MESH"),
        "rarity_language": (len({common.active_material.name, rare.active_material.name,
                                 epic.active_material.name}) == 3 and
                            required("SM_RPG_Rare_Chest_Lid").parent == lid and
                            gem.active_material == epic.active_material),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("RPG invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 45, 72):
        scene.frame_set(frame)
        poses[frame] = {"marker_z": marker.location.z,
                        "lid_rotation_x": lid.rotation_euler.x,
                        "gem_scale": gem.scale.x,
                        "gem_z": gem.location.z,
                        "camera_y": cam.location.y}
    if variant == 2:
        if not (poses[45]["marker_z"] > 0.35 and
                poses[72]["lid_rotation_x"] < -1 and
                poses[72]["gem_scale"] > 0.9 and
                poses[72]["gem_z"] > 1.8 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 1):
            raise ValueError("Quest, chest, gem, or camera reveal changed")
    elif poses[72]["lid_rotation_x"] < -0.1 or poses[72]["gem_scale"] > 0:
        raise ValueError("Baseline reveal unexpectedly changed")
    return {"variant": variant, "forest_pines": 3, "highland_stones": 3,
            "rarity_tiers": 3, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited RPG region identity, gear, quest cue, and loot reveal")


if __name__ == "__main__":
    main()
