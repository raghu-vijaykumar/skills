"""Audit material masters, clay baseline, three-point rig, and beauty-light sweep."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing material-light object: {name}")
    return obj


def principled(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        raise ValueError(f"Missing material master: {name}")
    return mat.node_tree.nodes.get("Principled BSDF")


def audit():
    scene = bpy.context.scene
    variant = scene.get("lookdev_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown material-light candidate")
    swatches = [required(f"SM_Lookdev_Swatch_{i}") for i in range(3)]
    key = required("LGT_Key_Main")
    fill = required("LGT_Fill_Soft")
    rim = required("LGT_Rim_Back")
    # Blender drops unused masters from the saved clay candidate.
    if variant == 2:
        polished = principled("MAT_Metal_Polished")
        brushed = principled("MAT_Metal_Brushed")
        ceramic = principled("MAT_Ceramic_Glaze")
        masters_ok = (polished.inputs["Metallic"].default_value == 1.0 and
                      brushed.inputs["Metallic"].default_value == 1.0 and
                      ceramic.inputs["Metallic"].default_value == 0.0 and
                      polished.inputs["Roughness"].default_value < 0.3 and
                      0.4 < brushed.inputs["Roughness"].default_value < 0.6 and
                      ceramic.inputs["Roughness"].default_value < 0.35)
    else:
        masters_ok = principled("MAT_Lookdev_Clay").inputs["Roughness"].default_value > 0.7
    checks = {
        "recipe": scene.get("lookdev_recipe") ==
                  "clay baseline, three reusable PBR masters, key fill rim, moving beauty key",
        "geometry": len(swatches) == 3 and
                    all(obj.type == "MESH" and len(obj.data.vertices) > 500
                        for obj in swatches),
        "masters": masters_ok,
        "three_point": all(obj.type == "LIGHT" for obj in (key, fill, rim)) and
                       key.data.energy > fill.data.energy and
                       rim.data.energy > fill.data.energy,
        "labels": [required(f"Lookdev label {i}").data.body
                   for i in range(3)] == ["POLISHED", "BRUSHED", "CERAMIC"],
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Material-light invariants failed: " + ", ".join(failed))
    assigned = [obj.data.materials[0].name for obj in swatches]
    expected = (["MAT_Lookdev_Clay"] * 3 if variant == 1 else
                ["MAT_Metal_Polished", "MAT_Metal_Brushed", "MAT_Ceramic_Glaze"])
    if assigned != expected:
        raise ValueError("Clay or beauty material assignments changed")
    poses = {}
    for frame in (1, 37, 72):
        scene.frame_set(frame)
        poses[frame] = {"key_x": key.location.x,
                        "fill_x": fill.location.x,
                        "rim_x": rim.location.x}
    if variant == 2:
        if not (poses[1]["key_x"] < -3.8 and
                abs(poses[37]["key_x"]) < 0.01 and
                poses[72]["key_x"] > 3.8 and
                poses[1]["fill_x"] == poses[72]["fill_x"] and
                poses[1]["rim_x"] == poses[72]["rim_x"]):
            raise ValueError("Beauty key or neutral rig changed")
    elif poses[1]["key_x"] != poses[72]["key_x"]:
        raise ValueError("Clay baseline unexpectedly sweeps the light")
    return {"variant": variant, "assigned_materials": assigned,
            "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited clay baseline, material masters, and moving three-point lookdev rig")


if __name__ == "__main__":
    main()
