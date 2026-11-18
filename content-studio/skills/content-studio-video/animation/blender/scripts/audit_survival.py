"""Audit the survival refuge's resource language, zones, and craft payoff."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing survival object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    cart = required("SM_Survival_Salvage_Cart_Rig")
    fire = required("SM_Survival_Crafted_Fire")
    watcher = required("SM_Survival_Hazard_Watcher_Rig")
    cam = required("Survival safe-unsafe overview camera")
    variant = scene.get("survival_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown survival candidate")
    checks = {
        "recipe": scene.get("survival_recipe") ==
                  "warm safe refuge, cold unsafe salvage, iconic crafting bench, wood water steel, returning cart and crafted fire",
        "zone_read": (required("SM_Survival_Safe_Zone").active_material !=
                      required("SM_Survival_Unsafe_Zone").active_material and
                      required("SM_Survival_Safety_Boundary").type == "MESH" and
                      len([o for o in scene.objects if o.name.startswith("Survival boundary post")]) == 2),
        "crafting_bench": (required("SM_Survival_Iconic_Crafting_Bench").dimensions.x > 3.4 and
                           required("Survival bench hammer head").type == "MESH" and
                           len([o for o in scene.objects if o.name.startswith("Survival bench leg")]) == 4),
        "resource_triage": (all(required(f"SM_Survival_Wood_Log_{i}").type == "MESH"
                                for i in range(3)) and
                            required("SM_Survival_Water_Canteen").type == "MESH" and
                            all(required(f"SM_Survival_Steel_Scrap_{i}").type == "MESH"
                                for i in range(2))),
        "salvage_and_fire": (required("SM_Survival_Salvage_Cart").parent == cart and
                             required("Survival cart resource crate").parent == cart and
                             len([o for o in scene.objects if o.name.startswith("Survival cart wheel")]) == 4 and
                             required("SM_Survival_Campfire_Hearth").type == "MESH" and
                             fire.type == "MESH"),
        "unsafe_cues": (required("SM_Survival_Hazard_Eye").parent == watcher and
                        len([o for o in scene.objects if o.name.startswith("Survival unsafe spike")]) == 3),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Survival invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 52, 72):
        scene.frame_set(frame)
        poses[frame] = {"cart_x": cart.location.x,
                        "fire_scale": fire.scale.x,
                        "watcher_x": watcher.location.x,
                        "camera_y": cam.location.y}
    if variant == 2:
        if not (poses[52]["cart_x"] < -3.3 and
                poses[72]["fire_scale"] > 0.8 and
                poses[72]["watcher_x"] > 0.8 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 1):
            raise ValueError("Salvage crossing, crafted fire, or watcher motion changed")
    elif poses[72]["cart_x"] < -0.2 or poses[72]["fire_scale"] > 0:
        raise ValueError("Baseline survival action unexpectedly changed")
    return {"variant": variant, "wood_logs": 3, "steel_scraps": 2,
            "cart_wheels": 4, "unsafe_spikes": 3, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited survival resources, zones, cart, fire, and hazard motion")


if __name__ == "__main__":
    main()
