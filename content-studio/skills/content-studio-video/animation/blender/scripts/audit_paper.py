"""Audit paper stock, layered seams and held stop-motion animation poses."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing paper craft object: {name}")
    return obj


def paper_material(name):
    mat = bpy.data.materials.get(name)
    tex = next((node for node in mat.node_tree.nodes
                if node.bl_idname == "ShaderNodeTexImage"), None) if mat else None
    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat else None
    if (not mat or not mat.get("craft_fiber") or not tex or not tex.image or
            not tex.image.packed_file or tuple(tex.image.size) != (128, 128) or
            not bsdf or bsdf.inputs["Roughness"].default_value < 0.9 or
            bsdf.inputs["Metallic"].default_value > 0):
        raise ValueError(f"The matte packed paper stock changed: {name}")
    return tex.image


def held_animation(obj, path):
    """Verify that the saved action actually holds between hand-placed poses."""
    animation = obj.animation_data
    if not animation or not animation.action:
        return False
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(animation.action, animation.action_slot).fcurves
    else:
        curves = animation.action.fcurves
    relevant = [curve for curve in curves if curve.data_path == path]
    return bool(relevant) and all(point.interpolation == "CONSTANT"
                                  for curve in relevant for point in curve.keyframe_points)


def audit():
    scene = bpy.context.scene
    root = required("Paper butterfly root")
    body = required("SM_Paper_Butterfly_Body")
    left = required("SM_Paper_Left_Upper_Wing")
    right = required("SM_Paper_Right_Upper_Wing")
    lh = required("Paper left wing hinge")
    rh = required("Paper right wing hinge")
    table = required("SM_Paper_Craft_Table")
    cam = required("Paper butterfly camera")
    required("Paper rolled body seam")
    required("Paper left fold seam")
    required("Paper right fold seam")
    required("Paper practical warm lamp")
    images = [paper_material(name) for name in
              ("Paper coral wing stock", "Paper ochre wing stock",
               "Paper cream applique")]
    backdrop = bpy.data.objects.get("Paper stock backdrop")
    shadow = bpy.data.objects.get("SM_Paper_Butterfly_Shadow")
    if backdrop:
        images.append(paper_material("Paper warm backdrop stock"))
        if backdrop.active_material.name != "Paper warm backdrop stock" or shadow is None:
            raise ValueError("The stock backdrop or tracked table shadow is incomplete")
    if (cam.data.type != "ORTHO" or cam.animation_data or
            body.parent != root or lh.parent != root or rh.parent != root or
            left.parent != lh or right.parent != rh or
            not body.get("rolled_paper") or
            list(table.get("real_table_m", [])) != [4.6, 2.8, 0.18] or
            not scene.get("craft_sublook", "").startswith("cut paper")):
        raise ValueError("The editable paper puppet, craft table, or fixed camera changed")
    layers = [obj for obj in bpy.data.objects if obj.get("cut_paper_layer")]
    if (len(layers) != 6 or any(not obj.modifiers.get("Physical paper thickness")
                               or obj.modifiers["Physical paper thickness"].thickness < 0.02
                               for obj in layers)):
        raise ValueError("Cut paper layers lost their physical thickness")
    if len([obj for obj in bpy.data.objects if obj.name.startswith(
            "Paper wing fastener")]) != 2 or len([obj for obj in bpy.data.objects
               if obj.name.startswith("Paper masking tape")]) != 2:
        raise ValueError("The hand-assembled fasteners or tape are missing")
    if (len([obj for obj in bpy.data.objects if obj.name.startswith(
            "Paper grid vertical")]) != 11 or
            len([obj for obj in bpy.data.objects if obj.name.startswith(
                "Paper grid horizontal")]) != 7):
        raise ValueError("The practical cutting-mat scale grid changed")
    samples = {}
    for frame in (1, 4, 7, 10, 37, 72):
        scene.frame_set(frame)
        samples[frame] = {"left_fold_rad": lh.rotation_euler.z,
                          "right_fold_rad": rh.rotation_euler.z,
                          "root_x_m": root.location.x,
                          "root_z_m": root.location.z,
                          "shadow_x_m": shadow.location.x if shadow else None}
    if (not held_animation(lh, "rotation_euler") or
            not held_animation(rh, "rotation_euler") or
            not held_animation(root, "location") or
            (shadow and not held_animation(shadow, "location")) or
            abs(samples[4]["right_fold_rad"] - samples[1]["right_fold_rad"]) > 0.001 or
            abs(samples[4]["left_fold_rad"] - samples[1]["left_fold_rad"]) > 0.001 or
            abs(samples[10]["right_fold_rad"] - samples[7]["right_fold_rad"]) > 0.001 or
            abs(samples[10]["left_fold_rad"] - samples[7]["left_fold_rad"]) > 0.001 or
            samples[37]["right_fold_rad"] < 0.85 or
            abs(samples[37]["left_fold_rad"] + samples[37]["right_fold_rad"]) > 0.01 or
            samples[72]["root_x_m"] - samples[1]["root_x_m"] < 1.1 or
            (shadow and any(abs(sample["root_x_m"] - sample["shadow_x_m"]) > 0.01
                            for sample in samples.values()))):
        raise ValueError("The held wing poses or stop-motion travel failed")
    return {"packed_paper_images": [list(image.size) for image in images],
            "cut_paper_layers": len(layers), "wing_fasteners": 2,
            "masking_tape_pieces": 2, "grid_lines": [11, 7],
            "packed_stock_backdrop": bool(backdrop),
            "tracked_table_shadow": bool(shadow),
            "fixed_orthographic_camera": True, "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited cut paper, fiber stock, craft table and held puppet poses")


if __name__ == "__main__":
    main()
