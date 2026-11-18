"""Audit hard cel bands, outline, anime eyes and independent pose timing."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing anime object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    head = required("SM_Anime_Head")
    left = required("SM_Anime_Left_Eye")
    right = required("SM_Anime_Right_Eye")
    arm = required("SM_Anime_Raised_Arm")
    head_control = required("Anime head control")
    arm_control = required("Anime arm control")
    scarf = required("Anime scarf control")
    cam = required("Anime portrait camera")
    if cam.data.type != "ORTHO" or not scene.render.use_freestyle:
        raise ValueError("The graphic anime camera or contour pass is missing")
    thickness = scene.view_layers[0].freestyle_settings.linesets[0].linestyle.thickness
    if thickness < 1.5:
        raise ValueError("Anime contour is too thin to read in the GIF")
    materials = [mat for mat in bpy.data.materials if mat.name.startswith("Anime ") and
                 mat.get("cel_value_steps") == 3]
    if len(materials) < 6:
        raise ValueError("The authored palette lacks six explicit cel materials")
    for mat in materials:
        ramp = next((node for node in mat.node_tree.nodes
                     if node.bl_idname == "ShaderNodeValToRGB"), None)
        if not ramp or ramp.color_ramp.interpolation != "CONSTANT" or len(
                ramp.color_ramp.elements) != 3:
            raise ValueError(f"Cel material lacks three hard bands: {mat.name}")
    eye_ratio = (left.dimensions.x + right.dimensions.x) / head.dimensions.x
    if eye_ratio < 0.35:
        raise ValueError("Anime eye proportions lost their enlarged read")
    if arm.parent != arm_control or head.parent != head_control:
        raise ValueError("Arm or head lost its independently editable control")
    if any(not control.animation_data or not control.animation_data.action
           for control in (head_control, arm_control, scarf)):
        raise ValueError("The head, arm, and scarf need independent keys")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"arm_y_rad": arm_control.rotation_euler.y,
                          "head_z_rad": head_control.rotation_euler.z,
                          "eye_z_scale": left.scale.z,
                          "scarf_y_rad": scarf.rotation_euler.y}
    if (samples[72]["arm_y_rad"] > -1.4 or samples[36]["eye_z_scale"] > 0.1 or
            samples[1]["eye_z_scale"] < 1 or samples[72]["eye_z_scale"] < 1):
        raise ValueError("The arm pose or blink timing failed")
    return {"cel_materials": len(materials), "cel_value_steps": 3,
            "freestyle_outline_px": thickness, "eye_to_head_width_ratio": eye_ratio,
            "independent_controls": ["head", "arm", "scarf"], "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Audited anime cel bands, outline, blink and pose controls")


if __name__ == "__main__":
    main()
