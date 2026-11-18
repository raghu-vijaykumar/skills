"""Audit platform gaps, hazard language, and the authored switch-to-goal beats."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing puzzle object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("puzzle_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown puzzle candidate")
    start = required("SM_Puzzle_Start_Platform")
    switch = required("SM_Puzzle_Switch_Platform")
    goal = required("SM_Puzzle_Goal_Platform")
    pad = required("SM_Puzzle_Pressure_Pad")
    bridge = required("SM_Puzzle_Extending_Bridge")
    hero = required("SM_Puzzle_Jumper_Rig")
    ring = required("SM_Puzzle_Pad_Cyan_Ring")
    spikes = [required(f"SM_Puzzle_Red_Spike_{i}") for i in range(5)]
    scene.frame_set(1)
    # The measured mesh gaps, rather than a camera trick, define the jump.
    first_gap = (switch.location.x - switch.dimensions.x / 2 -
                 (start.location.x + start.dimensions.x / 2))
    second_gap = (goal.location.x - goal.dimensions.x / 2 -
                  (switch.location.x + switch.dimensions.x / 2))
    checks = {
        "recipe": scene.get("puzzle_recipe") ==
                  "readable cyan pad and bridge, red triangular hazards, 0.7m first jump, 1m second span, gold goal",
        "honest_first_jump": 0.68 < first_gap < 0.72,
        "honest_second_span": 0.98 < second_gap < 1.02,
        "hazard_language": (len(spikes) == 5 and all(len(obj.data.vertices) == 5 for obj in spikes)
                            and spikes[0].active_material != ring.active_material),
        "interactable": (pad.type == "MESH" and bridge.active_material == ring.active_material
                         and required("SM_Puzzle_Goal_Arch").active_material != ring.active_material),
        "jumper": required("SM_Puzzle_Jumper_Body").parent == hero,
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Puzzle invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 26, 43, 62, 72):
        scene.frame_set(frame)
        poses[frame] = {"hero_x": hero.location.x, "hero_z": hero.location.z,
                        "bridge_scale": bridge.scale.x, "ring_scale": ring.scale.x}
    if variant == 2:
        scene.frame_set(62)
        bridge_left = bridge.location.x - bridge.dimensions.x / 2
        bridge_right = bridge.location.x + bridge.dimensions.x / 2
        switch_edge = switch.location.x + switch.dimensions.x / 2
        goal_edge = goal.location.x - goal.dimensions.x / 2
        # The extended mesh must actually cover both landing edges.
        if not (poses[26]["hero_z"] > 0.65 and
                start.location.x + start.dimensions.x / 2 <
                -3.20 + poses[26]["hero_x"] <
                switch.location.x - switch.dimensions.x / 2 and
                poses[43]["hero_x"] > 3.1 and
                poses[43]["hero_z"] < 0.05 and
                poses[62]["bridge_scale"] > 0.9 and
                bridge_left < switch_edge and bridge_right > goal_edge and
                poses[72]["hero_x"] > 6.7 and
                poses[72]["ring_scale"] > 0.9):
            raise ValueError("Puzzle jump, switch, bridge, or goal motion changed")
    elif (poses[72]["hero_x"] > 0.2 or poses[72]["bridge_scale"] > 0.1):
        raise ValueError("Baseline puzzle action unexpectedly changed")
    return {"variant": variant, "first_gap_m": first_gap,
            "second_gap_m": second_gap, "red_spikes": 5, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited puzzle gaps, hazards, switch, bridge, and jumper")


if __name__ == "__main__":
    main()
