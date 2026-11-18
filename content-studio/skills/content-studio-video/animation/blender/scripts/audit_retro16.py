"""Audit the packed dithered 16-bit backdrop and held fox/water sprite motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing 16-bit object: {name}")
    return obj


def held(obj):
    if not obj.animation_data:
        return False
    action = obj.animation_data.action
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves
    else:
        curves = action.fcurves
    paths = [curve for curve in curves if curve.data_path == "location"]
    return bool(paths) and all(key.interpolation == "CONSTANT"
                               for curve in paths for key in curve.keyframe_points)


def audit():
    scene = bpy.context.scene
    mats = [mat for mat in bpy.data.materials if mat.name.startswith("16bit palette ")]
    if len(mats) < 4 or not {0, 13, 14, 15}.issubset(
            {mat.get("16bit_palette_index") for mat in mats}):
        raise ValueError("The fox and water palette fills changed")
    if any({node.bl_idname for node in mat.node_tree.nodes} != {
            "ShaderNodeOutputMaterial", "ShaderNodeEmission"} for mat in mats):
        raise ValueError("A sprite fill gained gradient shading")
    image = bpy.data.images.get("16bit dithered landscape")
    backdrop = required("SM_16bit_Dithered_Backdrop")
    packed = backdrop.data.materials[0]
    texture = next((node for node in packed.node_tree.nodes
                    if node.bl_idname == "ShaderNodeTexImage"), None)
    if (image is None or tuple(image.size) != (160, 120) or not image.packed_file or
            texture is None or texture.image != image or
            texture.interpolation != "Closest" or
            packed.get("16bit_packed_texels") != 160 * 120):
        raise ValueError("The packed nearest dithered background changed")
    # Unused Blender materials are discarded on save; the packed image retains
    # the full source palette actually used by the landscape.
    packed_colors = {tuple(round(v, 4) for v in image.pixels[i:i + 3])
                     for i in range(0, len(image.pixels), 4)}
    if len(packed_colors) < 12 or len(packed_colors) > 16:
        raise ValueError(f"The richer packed palette changed: {len(packed_colors)} colors")
    fox = required("SM_16bit_Fox")
    alt = required("16bit fox alternate pose")
    ctrl = required("16bit fox control")
    water = required("SM_16bit_Water_Highlight")
    cam = required("16bit locked camera")
    if (fox.parent != ctrl or alt.parent != ctrl or not held(ctrl) or
            not held(water) or cam.data.type != "ORTHO" or cam.animation_data or
            abs(cam.data.ortho_scale - 5) > 0.001 or
            any(obj.type == "LIGHT" for obj in bpy.data.objects) or
            (scene.render.resolution_x, scene.render.resolution_y,
             scene.render.fps, scene.frame_end) != (320, 240, 12, 48) or
            scene.render.dither_intensity != 0 or
            scene.get("retro16_recipe") !=
            "packed 160x120 dithered landscape, 16 colors, nearest texels, held sprite walk"):
        raise ValueError("The 16-bit camera, raster, or animation contract changed")
    parts = [obj for obj in bpy.data.objects if obj.get("16bit_pixel_faces")]
    if len(parts) < 5 or any(obj.type != "MESH" or len(obj.data.polygons) !=
                            obj["16bit_pixel_faces"] for obj in parts):
        raise ValueError("Fox or water square-pixel meshes changed")
    variant = scene.get("retro16_variant")
    extra = [obj for obj in bpy.data.objects if obj.name.startswith("16bit second water glint ")
             and obj.get("16bit_sprite_grid")]
    if (variant == 1 and extra) or (variant == 2 and (len(extra) != 2 or
            not all(held(obj) for obj in extra))):
        raise ValueError("The water-glint candidate differentiation changed")
    samples = {}
    for frame in (1, 5, 25, 48):
        scene.frame_set(frame)
        samples[frame] = {"fox_x": ctrl.location.x,
                          "fox_visible": not fox.children[0].hide_render,
                          "alternate_visible": not alt.children[0].hide_render,
                          "water_z": water.location.z}
    if (samples[1]["fox_x"] >= samples[48]["fox_x"] or
            samples[1]["water_z"] <= samples[48]["water_z"] or
            not samples[1]["fox_visible"] or samples[1]["alternate_visible"] or
            (variant == 1 and (not samples[5]["fox_visible"] or
                               samples[5]["alternate_visible"])) or
            (variant == 2 and (samples[5]["fox_visible"] or
                               not samples[5]["alternate_visible"]))):
        raise ValueError("Fox walk or waterfall timing changed")
    return {"palette_size": len(mats), "packed_colors": len(packed_colors),
            "packed_backdrop_px": list(image.size),
            "sprite_pixel_faces": sum(obj["16bit_pixel_faces"] for obj in parts),
            "extra_water_glints": len(extra), "variant": variant,
            "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited packed dither, 16-entry source palette, held fox walk and waterfall")


if __name__ == "__main__":
    main()
