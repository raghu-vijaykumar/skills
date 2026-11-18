"""Audit the storybook island's shape language, packed paint, palette, and motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing stylized object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    roof = required("SM_Stylized_Painted_Roof")
    body = required("SM_Stylized_Cottage")
    canopy = required("SM_Stylized_Tree_Canopy")
    trunk = required("Stylized tree trunk")
    pivot = required("Stylized windmill control")
    cam = required("Stylized island camera")
    required("SM_Stylized_Island")
    required("SM_Stylized_Glow_Window")
    if cam.data.type != "ORTHO" or not scene.render.use_freestyle:
        raise ValueError("The storybook camera or outline pass is missing")
    roof_ratio = roof["roof_radius_m"] / body["body_radius_m"]
    canopy_ratio = canopy.dimensions.x / trunk.dimensions.x
    if roof_ratio < 1.7 or canopy_ratio < 4:
        raise ValueError("The intentionally exaggerated silhouettes were lost")
    if scene.get("core_palette") != "sage,cream,terracotta,warm" or not scene.get(
            "shape_language", "").startswith("circle-friendly"):
        raise ValueError("The shape and four-color direction is missing")
    roof_mat = roof.active_material
    tex = next((node for node in roof_mat.node_tree.nodes
                if node.bl_idname == "ShaderNodeTexImage"), None)
    if not roof_mat.get("painted_albedo") or not tex or not tex.image or not tex.image.packed_file:
        raise ValueError("The generated roof paint must remain packed in the blend")
    if tuple(tex.image.size) != (64, 64):
        raise ValueError("The roof paint budget changed")
    mats = [mat for mat in bpy.data.materials if mat.name.startswith("Stylized ") and
            mat.use_nodes and mat.node_tree.nodes.get("Principled BSDF")]
    if any(mat.node_tree.nodes.get("Principled BSDF").inputs["Metallic"].default_value > 0 or
           mat.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value < 0.85
           for mat in mats):
        raise ValueError("The island acquired a photoreal metal or glossy material")
    window = bpy.data.materials.get("Stylized animated window")
    if not window:
        raise ValueError("Animated window material is missing")
    bsdf = window.node_tree.nodes.get("Principled BSDF")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"windmill_y_rad": pivot.rotation_euler.y,
                          "window_emission": bsdf.inputs["Emission Strength"].default_value,
                          "window_base": list(bsdf.inputs["Base Color"].default_value)[:3]}
    if (not pivot.animation_data or not pivot.animation_data.action or
            samples[72]["windmill_y_rad"] < 3.9 or
            samples[1]["window_emission"] > 0.01 or
            samples[72]["window_emission"] < 2 or
            samples[72]["window_base"][0] < samples[1]["window_base"][0] * 4):
        raise ValueError("Windmill turn or warm window reveal did not happen")
    return {"roof_to_body_radius": roof_ratio,
            "canopy_to_trunk_width": canopy_ratio,
            "palette": scene["core_palette"],
            "packed_roof_texture": list(tex.image.size),
            "freestyle_outline_px": scene.view_layers[0].freestyle_settings.linesets[0].linestyle.thickness,
            "matte_materials": len(mats), "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Audited stylized silhouette, packed paint, palette, and motion")


if __name__ == "__main__":
    main()
