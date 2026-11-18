"""Audit the four-color 8-bit sprite shot and its stepped impact motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing 8-bit object: {name}")
    return obj


def constant_location(obj):
    if not obj.animation_data:
        return False
    action = obj.animation_data.action
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves
    else:
        curves = action.fcurves
    locations = [curve for curve in curves if curve.data_path == "location"]
    return bool(locations) and all(key.interpolation == "CONSTANT"
                                   for curve in locations for key in curve.keyframe_points)


def audit():
    scene = bpy.context.scene
    mats = [mat for mat in bpy.data.materials if mat.name.startswith("8bit palette ")]
    if len(mats) != 4 or {mat.get("8bit_palette_index") for mat in mats} != set(range(4)):
        raise ValueError("The authored four-color palette changed")
    for mat in mats:
        if {node.bl_idname for node in mat.node_tree.nodes} != {
                "ShaderNodeOutputMaterial", "ShaderNodeEmission"}:
            raise ValueError("An 8-bit fill gained lighting or gradients")
    roots = [obj for obj in bpy.data.objects if obj.get("sprite_grid")]
    parts = [obj for obj in bpy.data.objects if obj.get("sprite_pixel_count")]
    if len(roots) < 15 or not parts:
        raise ValueError("Sprite roots or square-pixel geometry missing")
    for part in parts:
        if part.type != "MESH" or len(part.data.polygons) != part["sprite_pixel_count"]:
            raise ValueError(f"Pixel face count changed: {part.name}")
        for polygon in part.data.polygons:
            vertices = [part.data.vertices[i].co for i in polygon.vertices]
            xs = [v.x for v in vertices]
            zs = [v.z for v in vertices]
            if (len(vertices) != 4 or abs(max(xs)-min(xs)-0.07) > 0.0001 or
                    abs(max(zs)-min(zs)-0.07) > 0.0001 or
                    max(v.y for v in vertices)-min(v.y for v in vertices) > 0.0001):
                raise ValueError(f"Non-square sprite pixel: {part.name}")
    ship = required("SM_8bit_Ship")
    ctrl = required("8bit ship control")
    asteroid = required("SM_8bit_Asteroid")
    projectile = required("SM_8bit_Projectile")
    fragments = [required(f"SM_8bit_Fragment_{i}") for i in range(4)]
    backdrop = required("8bit flat backdrop")
    cam = required("8bit locked camera")
    if (ship.parent != ctrl or cam.data.type != "ORTHO" or
            abs(cam.data.ortho_scale - 5.0) > 0.001 or cam.animation_data or
            any(obj.type == "LIGHT" for obj in bpy.data.objects) or
            backdrop.data.materials[0] != mats[0] or
            (scene.render.resolution_x, scene.render.resolution_y,
             scene.render.fps, scene.frame_end) != (320, 240, 12, 48) or
            scene.render.dither_intensity != 0 or
            scene.get("retro_recipe") !=
            "four emission colors, grid square sprites, held motion, fixed low raster"):
        raise ValueError("8-bit camera, raster, palette, or hierarchy changed")
    if not all(constant_location(obj) for obj in [ctrl, projectile, *fragments]):
        raise ValueError("Sprite travel lost held keyframes")
    samples = {}
    for frame in (1, 26, 31, 48):
        scene.frame_set(frame)
        samples[frame] = {
            "ship_x": ctrl.location.x,
            "projectile_visible": not projectile.children[0].hide_render,
            "asteroid_visible": not asteroid.children[0].hide_render,
            "fragment_visible": not fragments[0].children[0].hide_render,
            "fragment_x": [obj.location.x for obj in fragments],
        }
    if (samples[1]["projectile_visible"] or not samples[1]["asteroid_visible"] or
            samples[1]["fragment_visible"] or not samples[26]["projectile_visible"] or
            samples[31]["asteroid_visible"] or not samples[31]["fragment_visible"] or
            samples[48]["asteroid_visible"] or samples[48]["projectile_visible"] or
            samples[48]["fragment_x"][1] <= samples[31]["fragment_x"][1]):
        raise ValueError("Sprite approach, fire, or impact timing changed")
    return {"palette_size": len(mats), "square_pixel_faces": sum(
                obj["sprite_pixel_count"] for obj in parts),
            "sprite_roots": len(roots), "held_motion": True,
            "variant": scene.get("retro_variant"), "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited four-color square sprites and held impact motion")


if __name__ == "__main__":
    main()
