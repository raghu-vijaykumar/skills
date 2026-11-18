"""Audit the three-card hand, icon geometry, choice lift, and reward stack."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing card-table object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("card_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown card-table candidate")
    sword = required("SM_Card_Sword_Rig")
    shield = required("SM_Card_Shield_Rig")
    coin = required("SM_Card_Coin_Rig")
    rewards = [required(f"SM_Card_Reward_Coin_{i}") for i in range(5)]
    checks = {
        "recipe": scene.get("card_recipe") ==
                  "three readable 3D icons on quiet table, one lifted choice, reward coin stack",
        "stage": required("SM_Card_Table_Stage").dimensions.x > 9.4,
        "hand": all(required(name + " border").parent == rig and
                    required(name + " face").parent == rig
                    for name, rig in (("SM_Card_Sword_Rig", sword),
                                      ("SM_Card_Shield_Rig", shield),
                                      ("SM_Card_Coin_Rig", coin))),
        "icons": (required("SM_Card_Sword_Rig sword blade").parent == sword and
                  required("SM_Card_Shield_Rig shield face").parent == shield and
                  required("SM_Card_Coin_Rig coin crest").parent == coin),
        "deck": required("Card deck stack top").type == "MESH",
        "rewards": len(rewards) == 5 and
                   all(rewards[i].location.z < rewards[i + 1].location.z
                       for i in range(4)),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Card-table invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 42, 72):
        scene.frame_set(frame)
        poses[frame] = {"shield_y": shield.location.y,
                        "shield_z": shield.location.z,
                        "shield_scale": shield.scale.x,
                        "reward_visible": sum(item.scale.x > 0.95 for item in rewards)}
    if variant == 2:
        if not (poses[1]["shield_z"] < 0.05 and
                poses[42]["shield_z"] > 0.35 and
                poses[72]["shield_z"] > 0.6 and
                poses[72]["shield_y"] > 0.5 and
                poses[72]["shield_scale"] > 1.05 and
                poses[1]["reward_visible"] == 2 and
                poses[72]["reward_visible"] == 5):
            raise ValueError("Selected card or reward growth changed")
    elif (poses[72]["shield_z"] > 0.05 or
          poses[72]["reward_visible"] != 2):
        raise ValueError("Baseline card-table candidate unexpectedly changed")
    return {"variant": variant, "cards": 3, "coins": 5, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited readable card hand, selection, and idle reward stack")


if __name__ == "__main__":
    main()
