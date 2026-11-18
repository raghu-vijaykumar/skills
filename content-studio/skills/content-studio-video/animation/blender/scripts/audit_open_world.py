"""Audit the two-biome crossing, landmark, traversal, and sparse discoveries."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing crossing object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("crossing_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown crossing candidate")
    meadow = required("SM_Crossing_Meadow_Biome")
    badlands = required("SM_Crossing_Badlands_Biome")
    bridge = required("SM_Crossing_Bridge_Deck")
    traveler = required("SM_Crossing_Traveler_Rig")
    tower = required("SM_Crossing_Landmark_Tower")
    beacon = required("SM_Crossing_Landmark_Beacon")
    checks = {
        "recipe": scene.get("crossing_recipe") ==
                  "two biomes, bridged river, tall landmark, traversing explorer, sparse discovery",
        "biome_border": meadow.location.x < -3 and badlands.location.x > 3 and
                        meadow.data.materials[0] != badlands.data.materials[0],
        "traversal": abs(bridge.location.x) < 0.1 and
                     required("SM_Crossing_River").dimensions.y > 7,
        "landmark": tower.dimensions.z > 2 and beacon.location.z > tower.location.z,
        "discoveries": all(required(f"SM_Crossing_Discovery_Crumb_{i}")
                           for i in range(3)) and
                       required("SM_Crossing_Discovery_Cache").type == "MESH",
        "hero": required("Crossing traveler body").parent == traveler and
                required("Crossing traveler head").parent == traveler and
                required("Crossing traveler pack").parent == traveler,
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Crossing invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 40, 72):
        scene.frame_set(frame)
        poses[frame] = {"traveler_x": traveler.location.x,
                        "beacon_scale": beacon.scale.x}
    if variant == 2:
        if not (poses[1]["traveler_x"] < -4.5 and
                abs(poses[40]["traveler_x"]) < 0.2 and
                poses[72]["traveler_x"] > 2.4 and
                poses[1]["beacon_scale"] < 0.6 and
                poses[72]["beacon_scale"] > 1.3):
            raise ValueError("Crossing or beacon reveal changed")
    elif poses[72]["traveler_x"] > -4.5:
        raise ValueError("Baseline crossing candidate unexpectedly traverses")
    return {"variant": variant, "biomes": 2, "crumbs": 3, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited biome border, bridge, landmark, traveler, and discoveries")


if __name__ == "__main__":
    main()
