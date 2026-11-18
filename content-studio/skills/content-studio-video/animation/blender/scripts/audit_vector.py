"""Audit flat vector fills, planar paths, staged leaves and flower growth."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing vector object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    panel = required("SM_Vector_Icon_Panel")
    stem = required("SM_Vector_Sprout_Stem")
    left = required("SM_Vector_Left_Leaf")
    right = required("SM_Vector_Right_Leaf")
    flower = required("SM_Vector_Flower_Center")
    sun = required("SM_Vector_Sun")
    bloom = required("Vector bloom control")
    leaf_controls = [required(f"Vector {side} leaf control")
                     for side in ("left", "right")]
    cam = required("Vector front camera")
    materials = [mat for mat in bpy.data.materials if mat.name.startswith("Vector ")]
    if len(materials) != 5:
        raise ValueError("The five-color vector palette changed")
    for mat in materials:
        nodes = {node.bl_idname for node in mat.node_tree.nodes}
        if not mat.get("flat_vector_fill") or nodes != {
                "ShaderNodeOutputMaterial", "ShaderNodeEmission"}:
            raise ValueError(f"A vector fill gained lighting or a gradient: {mat.name}")
    paths = [obj for obj in bpy.data.objects if obj.get("vector_path_points")]
    if (len(paths) < 24 or any(obj.type != "MESH" or len(obj.data.polygons) != 1 or
                                max(vertex.co.y for vertex in obj.data.vertices) -
                                min(vertex.co.y for vertex in obj.data.vertices) > 0.0001
                                for obj in paths)):
        raise ValueError("The icon lost its planar polygon paths")
    petals = [obj for obj in bpy.data.objects if obj.name.startswith("Vector coral petal ")]
    rays = [obj for obj in bpy.data.objects if obj.name.startswith("Vector sun ray ")]
    staged = bpy.data.objects.get("Vector petal 0 control") is not None
    masked = bool(petals[0].animation_data)
    if (len(petals) != 5 or len(rays) != 8 or
            cam.data.type != "ORTHO" or cam.animation_data or
            abs(cam.data.ortho_scale - 5.55) > 0.001 or
            any(obj.type == "LIGHT" for obj in bpy.data.objects) or
            flower.parent != bloom or
            left.parent != leaf_controls[0] or right.parent != leaf_controls[1] or
            scene.get("vector_recipe") !=
            "five emission-only flat fills, crisp 2D mesh paths, fixed front camera"):
        raise ValueError("The flat camera, sun, or sprout hierarchy changed")
    if staged and len([obj for obj in bpy.data.objects
                       if obj.name.startswith("Vector petal ") and
                       obj.name.endswith(" control")]) != 5:
        raise ValueError("The staged flower path controls changed")
    samples = {}
    for frame in (1, 36, 43, 52, 72):
        scene.frame_set(frame)
        samples[frame] = {"stem_scale_z": stem.scale.z,
                          "left_leaf_scale": leaf_controls[0].scale.x,
                          "right_leaf_scale": leaf_controls[1].scale.x,
                          "flower_scale": bloom.scale.x,
                          "first_petal_scale": required("Vector petal 0 control").scale.x
                          if staged else None,
                          "last_petal_scale": required("Vector petal 4 control").scale.x
                          if staged else None,
                          "last_petal_hidden": required("Vector coral petal 4").hide_render
                          if masked else None}
    if (not stem.animation_data or not bloom.animation_data or
            any(not obj.animation_data for obj in leaf_controls) or
            samples[1]["stem_scale_z"] > 0.01 or
            samples[36]["stem_scale_z"] < 0.99 or
            samples[43]["left_leaf_scale"] < 0.99 or
            samples[43]["right_leaf_scale"] < 0.99 or
            samples[43]["flower_scale"] > 0.2 or
            samples[72]["flower_scale"] < 0.99 or
            (staged and samples[52]["first_petal_scale"] <=
             samples[52]["last_petal_scale"]) or
            (masked and (not samples[1]["last_petal_hidden"] or
                         not samples[52]["last_petal_hidden"] or
                         samples[72]["last_petal_hidden"]))):
        raise ValueError("The sprout or staged bloom motion changed")
    return {"flat_emission_fills": [mat.name for mat in materials],
            "planar_paths": len(paths), "sun_rays": len(rays),
            "coral_petals": len(petals), "staggered_petals": staged,
            "subpixel_petals_masked": masked,
            "fixed_front_camera": True, "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited five flat fills, planar paths and staged vector bloom")


if __name__ == "__main__":
    main()
