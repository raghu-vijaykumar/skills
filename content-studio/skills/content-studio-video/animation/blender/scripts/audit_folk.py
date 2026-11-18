"""Audit the daylight rite, repeating handmade symbols, and held or moving cues."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing folk rite object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    field = required("SM_Rite_Field")
    spine = required("SM_Rite_Wicker_Spine")
    head = required("SM_Rite_Wicker_Sun_Disk")
    stones = [required(f"SM_Rite_Standing_Stone_{i}") for i in range(10)]
    ribbons = [required(f"SM_Rite_Red_Ribbon_{i}") for i in range(6)]
    stakes = [required(f"Rite offering stake {i}") for i in range(6)]
    huts = [required(f"Rite shut village hut {i}") for i in range(4)]
    trees = [required(f"Rite field tree canopy {i}") for i in range(4)]
    cam = required("Folk horror field camera")
    sun = required("Rite warm daylight")
    variant = scene.get("folk_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown folk candidate")
    checks = {
        "pastoral_field": field.type == "MESH" and len(trees) == 4 and
                          sun.type == "LIGHT" and sun.data.energy > 1500,
        "handmade_rite": spine.type == "MESH" and head.type == "MESH" and
                         head.get("wicker_hero") is True and
                         len([o for o in scene.objects if o.name.startswith("Rite torso weave ")]) == 11,
        "repeating_symbols": all(stone.get("symbol_index") == i for i, stone in enumerate(stones)) and
                             all(stake.get("offering_index") == i for i, stake in enumerate(stakes)),
        "village": len(huts) == 4 and all(required(f"Rite hut closed door {i}").type == "MESH"
                                           for i in range(4)),
        "camera": cam.type == "CAMERA" and cam.data.type == "PERSP" and
                  bool(cam.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "recipe": scene.get("folk_recipe") ==
                  "sunlit closed village, ritual stones, handmade wicker, repeated crimson offerings",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Wrong folk rite invariants: " + ", ".join(failed))
    if variant == 2 and any(not cloth.animation_data for cloth in ribbons):
        raise ValueError("The crimson offerings must sway")
    samples = {}
    for frame in (1, 24, 72):
        scene.frame_set(frame)
        samples[frame] = {"camera_y": cam.location.y,
                          "ribbon_rotation": ribbons[0].rotation_euler.z}
    if samples[72]["camera_y"] <= samples[1]["camera_y"] or (
            variant == 2 and
            (samples[72]["camera_y"] <= -8.0 or
             abs(samples[24]["ribbon_rotation"] - samples[1]["ribbon_rotation"]) < 0.25)):
        raise ValueError("Inspection push or ribbon sway changed")
    return {"variant": variant, "standing_stones": len(stones),
            "offering_ribbons": len(ribbons), "closed_huts": len(huts),
            "field_trees": len(trees), "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited sunlit village rite, repeated stones, wicker, ribbons, and inspection push")


if __name__ == "__main__":
    main()
