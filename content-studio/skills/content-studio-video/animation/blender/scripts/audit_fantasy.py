"""Audit the low-magic keep's materials, heraldry, gateway, and bridge crossing."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing fantasy keep object: {name}")
    return obj


def roughness(name):
    return bpy.data.materials[name].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value


def audit():
    scene = bpy.context.scene
    # Inspect the bridge footprint at its delivered lowered pose.
    scene.frame_set(72)
    bank = required("SM_Keep_Bank")
    moat = required("SM_Keep_Moat")
    bridge = required("SM_Keep_Oak_Drawbridge")
    hinge = required("Keep drawbridge hinge control")
    gate = required("SM_Keep_Gate_Lintel")
    piers = [required(f"SM_Keep_Wall_Pier_{s}") for s in (-1, 1)]
    towers = [required(f"SM_Keep_Tower_{s}") for s in (-1, 1)]
    banners = [required(f"Keep banner wool {s}") for s in (-1, 1)]
    merlons = [required(f"Keep tower merlon {s} {i}")
               for s in (-1, 1) for i in range(8)]
    planks = [required(f"Keep oak plank seam {i}") for i in range(9)]
    cam = required("Fantasy gate inspection camera")
    variant = scene.get("fantasy_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown fantasy gate candidate")
    opening_width = 2 * (piers[1].location.x - piers[1].dimensions.x / 2)
    bank_edge_y = bank.location.y + bank.dimensions.y / 2
    bridge_front_y = hinge.location.y - bridge.dimensions.y
    checks = {
        "masonry": all(tower.get("masonry_tower") == s for tower, s in zip(towers, (-1, 1))) and
                   len(merlons) == 16 and all(obj.type == "MESH" for obj in piers),
        "honest_materials": roughness("Keep limestone ashlar") >= 0.9 and
                            roughness("Keep oak drawbridge") >= 0.75 and
                            roughness("Keep heraldic red wool") >= 0.9,
        "heraldry": all(obj.type == "MESH" for obj in banners) and
                    len([obj for obj in scene.objects if obj.name.startswith("Keep banner heraldic bar ")]) == 2,
        "bridge_craft": bridge.get("hinged_bridge") is True and
                        bool(hinge.animation_data) and len(planks) == 9 and
                        all(plank.parent == hinge for plank in planks),
        "gateway_fit": opening_width > bridge.dimensions.x and
                       bank_edge_y >= bridge_front_y and gate.type == "MESH" and
                       moat.type == "MESH",
        "camera": cam.type == "CAMERA" and bool(cam.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "recipe": scene.get("fantasy_recipe") ==
                  "medieval low-magic stone keep, wool heraldry, oak drawbridge, iron fittings",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Wrong low-magic keep invariants: " + ", ".join(failed))
    samples = {}
    for frame in (1, 48, 72):
        scene.frame_set(frame)
        samples[frame] = {"bridge_angle": hinge.rotation_euler.x,
                          "camera_y": cam.location.y}
    if (samples[1]["bridge_angle"] > -1.3 or
            samples[72]["bridge_angle"] <= samples[1]["bridge_angle"] or
            variant == 2 and (abs(samples[72]["bridge_angle"]) > 0.05 or
                              samples[72]["camera_y"] < -7.5)):
        raise ValueError("Bridge lowering or inspection push changed")
    return {"variant": variant, "masonry_towers": len(towers),
            "tower_merlons": len(merlons), "heraldic_banners": len(banners),
            "bridge_planks": len(planks), "opening_width": opening_width,
            "bridge_width": bridge.dimensions.x,
            "bank_overlap": bank_edge_y - bridge_front_y,
            "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited low-magic stone keep, heraldry, gateway fit, and hinged bridge")


if __name__ == "__main__":
    main()
