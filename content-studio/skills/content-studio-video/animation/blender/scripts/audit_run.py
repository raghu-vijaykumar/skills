"""Audit modular rooms, ability gate, biome props, and run modifier poses."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing modular-run object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("run_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown modular-run candidate")
    moss = required("SM_Run_Moss_Room_Module")
    stone = required("SM_Run_Stone_Room_Module")
    crystal = required("SM_Run_Crystal_Room_Module")
    ability = required("SM_Run_Dash_Ability_Orb")
    gate_left = required("SM_Run_Ability_Gate_Left")
    gate_right = required("SM_Run_Ability_Gate_Right")
    curse = required("SM_Run_Curse_Modifier")
    shield = required("SM_Run_Shield_Modifier")
    runner = required("SM_Run_Traveler_Rig")
    checks = {
        "recipe": scene.get("run_recipe") ==
                  "three equal modules, moss and crystal biomes, cyan ability gate, red curse and gold shield modifiers",
        "modular_footprints": (abs(moss.dimensions.x - stone.dimensions.x) < 0.01 and
                               abs(stone.dimensions.x - crystal.dimensions.x) < 0.01 and
                               abs(moss.dimensions.y - crystal.dimensions.y) < 0.01),
        "biome_identity": len({moss.active_material.name, stone.active_material.name,
                               crystal.active_material.name}) == 3,
        "biome_props": (len([o for o in scene.objects if o.name.startswith(
            "SM_Run_Moss_Tuft_")]) == 3 and
                        len([o for o in scene.objects if o.name.startswith(
                            "SM_Run_Crystal_Spire_")]) == 3),
        "ability_match": (ability.active_material != moss.active_material and
                          gate_left.active_material == gate_right.active_material),
        "modifier_read": curse.active_material != shield.active_material,
        "runner": required("SM_Run_Traveler_Body").parent == runner,
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Modular-run invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 39, 53, 72):
        scene.frame_set(frame)
        poses[frame] = {"runner_x": runner.location.x,
                        "ability_scale": ability.scale.x,
                        "gate_left_y": gate_left.location.y,
                        "gate_right_y": gate_right.location.y,
                        "shield_scale": shield.scale.x}
    if variant == 2:
        if not (poses[39]["runner_x"] > 3.5 and
                poses[39]["ability_scale"] < 0.1 and
                poses[53]["gate_left_y"] < -1.6 and
                poses[53]["gate_right_y"] > 1.6 and
                poses[72]["runner_x"] > 8.3 and
                poses[72]["shield_scale"] > 1.1):
            raise ValueError("Ability collection, gate opening, or biome crossing changed")
    elif (poses[72]["runner_x"] > 0.2 or poses[72]["ability_scale"] < 0.9 or
          poses[72]["gate_left_y"] < -0.7):
        raise ValueError("Baseline modular-run action unexpectedly changed")
    return {"variant": variant, "modules": 3, "moss_tufts": 3,
            "crystal_spires": 3, "modifiers": 2, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited modular rooms, ability gate, biomes, and modifiers")


if __name__ == "__main__":
    main()
