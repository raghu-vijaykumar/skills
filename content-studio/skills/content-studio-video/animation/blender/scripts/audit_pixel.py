"""Audit the pixel chest's packed texels, palette, fixed camera and motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing pixel chest object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    cam = required("Pixel locked camera")
    hinge = required("Pixel lid hinge")
    treasure = required("SM_Pixel_Treasure")
    lid = required("SM_Pixel_Chest_Lid")
    front = required("SM_Pixel_Chest_Front")
    required("SM_Pixel_Chest_Body")
    if (cam.data.type != "ORTHO" or cam.animation_data or
            lid.parent != hinge or scene.render.resolution_x != 320 or
            scene.render.resolution_y != 240 or scene.render.fps != 12):
        raise ValueError("The low-resolution locked camera or editable lid is missing")
    if (scene.get("pixel_palette_size") != 8 or
            scene.render.filter_size > 0.02 or
            scene.view_settings.view_transform != "Standard"):
        raise ValueError("The eight-color crisp pixel output settings changed")
    palette = [mat for mat in bpy.data.materials if mat.name.startswith("Pixel palette ")]
    if len(palette) != 8 or {mat.get("palette_index") for mat in palette} != set(range(8)):
        raise ValueError(f"The flat eight-color palette is incomplete: "
                         f"{[(mat.name, mat.get('palette_index')) for mat in palette]}")
    textures = {}
    for name in ("Pixel chest front 16x16", "Pixel lid face 16x16"):
        mat = bpy.data.materials.get(name)
        tex = next((node for node in mat.node_tree.nodes
                    if node.bl_idname == "ShaderNodeTexImage"), None) if mat else None
        if (not mat or mat.get("texel_size_px") != 16 or not tex or
                tex.interpolation != "Closest" or not tex.image or
                tuple(tex.image.size) != (16, 16) or not tex.image.packed_file):
            raise ValueError(f"The packed nearest 16x16 texture changed: {name}")
        textures[name] = list(tex.image.size)
    if front.active_material.name != "Pixel chest front 16x16":
        raise ValueError("The front print is not assigned to the chest")
    if len([obj for obj in bpy.data.objects if obj.name.startswith("SM_Pixel_Spark_")]) != 4:
        raise ValueError("The square treasure sparks are missing")
    samples = {}
    for frame in (1, 24, 48):
        scene.frame_set(frame)
        samples[frame] = {"lid_angle_rad": hinge.rotation_euler.x,
                          "treasure_z_m": treasure.location.z,
                          "spark_z_m": required("SM_Pixel_Spark_0").location.z}
    if (not hinge.animation_data or not treasure.animation_data or
            samples[48]["lid_angle_rad"] > -1 or
            samples[48]["treasure_z_m"] - samples[1]["treasure_z_m"] < 0.5 or
            samples[48]["spark_z_m"] - samples[1]["spark_z_m"] < 0.4):
        raise ValueError("The lid and square treasure reveal no longer read")
    return {"raster_px": [320, 240], "fps": 12, "palette_colors": len(palette),
            "packed_nearest_textures": textures, "orthographic_locked_camera": True,
            "spark_count": 4, "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited packed nearest texels, palette, locked camera and reveal")


if __name__ == "__main__":
    main()
