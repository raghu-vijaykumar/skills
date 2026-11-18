"""Audit human recognition, fused materials, sixth digit, and opening motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing mutating hand object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    palm = required("SM_Body_Horror_Palm")
    extra = required("SM_Body_Horror_Extra_Digit knuckle control")
    cam = required("Body horror hand camera")
    variant = scene.get("body_horror_variant")
    if variant not in (1, 2, 3):
        raise ValueError("Unknown hand candidate")
    fingers = [required(f"Hand digit {i} knuckle control")
               for i in range(4 if variant == 3 else 5)]
    thumb = required("Hand thumb knuckle control")
    plates = [required(f"SM_Body_Horror_Fusion_{i}") for i in range(3)]
    if (not palm.get("human_anatomy") or not extra.get("mutation_branch") or
            any(not plate.get("material_transition") for plate in plates) or
            any(not finger.animation_data for finger in fingers) or
            not thumb.animation_data or cam.data.type != "ORTHO" or
            abs(cam.data.ortho_scale - 6.6) > 0.01 or
            (scene.render.resolution_x, scene.render.resolution_y,
             scene.render.fps, scene.frame_end) != (960, 540, 24, 72) or
            scene.get("body_horror_recipe") !=
            "recognized hand, sixth digit, skin-to-metal-to-plastic fusion"):
        raise ValueError("Hand recognition, fusion, motion, or shot contract changed")
    material_names = {mat.name for mat in bpy.data.materials}
    if not {"Hand pallid living skin", "Hand surgical steel fusion",
            "Hand bone white plastic"}.issubset(material_names):
        raise ValueError("Skin, metal, or plastic transition missing")
    if variant == 3 and bpy.data.objects.get("Hand digit 4 knuckle control") is not None:
        raise ValueError("The final candidate still has two extra digits")
    if variant >= 2 and (not extra.animation_data or
                         any(not plate.animation_data for plate in plates)):
        raise ValueError("The growing sixth digit or spreading plates are static")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"index_bend": fingers[1].rotation_euler.x,
                          "extra_height_scale": extra.scale.z,
                          "first_plate_width": plates[0].scale.x,
                          "camera_x": cam.location.x}
    if (samples[1]["index_bend"] <= samples[72]["index_bend"] or
            samples[1]["camera_x"] <= samples[72]["camera_x"] or
            (variant >= 2 and
             (samples[1]["extra_height_scale"] >= samples[72]["extra_height_scale"] or
              samples[1]["first_plate_width"] >= samples[72]["first_plate_width"]))):
        raise ValueError("Hand opening, mutation growth, or camera inspection changed")
    return {"variant": variant, "human_fingers": len(fingers) + 1,
            "extra_digit": True, "fusion_plates": len(plates),
            "surface_materials": sorted(material_names), "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited recognizable fingers, sixth digit, fused surfaces, and opening motion")


if __name__ == "__main__":
    main()
