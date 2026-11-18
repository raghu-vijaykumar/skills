"""Audit the strategy shot's grid, systems props, units, and keyed dispatch."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing strategy object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("strategy_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown strategy candidate")
    miner = required("SM_Strategy_Miner_Rig")
    farmer = required("SM_Strategy_Farmer_Rig")
    tower = required("SM_Strategy_Watch_Tower")
    crown = required("Strategy watch platform")
    tiles = [o for o in scene.objects if o.name.startswith("SM_Strategy_Tile_")]
    crops = [o for o in scene.objects if o.name.startswith("Strategy crop ")]
    ore = [o for o in scene.objects if o.name.startswith("Strategy ore seam ")]
    checks = {
        "recipe": scene.get("strategy_recipe") ==
                  "readable tiles, iconic hall and resource buildings, color-coded units, growing watch tower",
        "grid": len(tiles) == 12 and len({round(o.location.x, 2) for o in tiles}) == 4
                and len({round(o.location.y, 2) for o in tiles}) == 3,
        "buildings": all(required(name).type == "MESH" for name in (
            "SM_Strategy_Command_Hall", "SM_Strategy_Farm", "SM_Strategy_Mine",
            "SM_Strategy_Watch_Tower")),
        "resources": len(crops) == 12 and len(ore) == 3,
        "units": len([o for o in scene.objects if o.parent == miner]) == 3
                 and len([o for o in scene.objects if o.parent == farmer]) == 3,
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Strategy invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 42, 72):
        scene.frame_set(frame)
        poses[frame] = {"miner_x": miner.location.x,
                        "farmer_y": farmer.location.y,
                        "tower_height": tower.dimensions.z,
                        "platform_height": crown.location.z}
    if variant == 2:
        if not (poses[42]["miner_x"] > 0.5 and
                poses[72]["miner_x"] > 2 and
                poses[72]["farmer_y"] > 1.15 and
                poses[72]["tower_height"] > poses[1]["tower_height"] * 4 and
                poses[72]["platform_height"] > poses[1]["platform_height"] + 0.8):
            raise ValueError("Resource dispatch or tower build changed")
    elif (poses[72]["miner_x"] > -1.2 or
          poses[72]["tower_height"] > poses[1]["tower_height"] * 1.2):
        raise ValueError("Baseline strategy candidate unexpectedly changed")
    return {"variant": variant, "tiles": len(tiles), "crops": len(crops),
            "ore_seams": len(ore), "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited strategy grid, resources, units, and tower")


if __name__ == "__main__":
    main()
