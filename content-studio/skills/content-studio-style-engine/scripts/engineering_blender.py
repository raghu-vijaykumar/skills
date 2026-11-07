#!/usr/bin/env python3
"""Blender background renderer for authored engineering assemblies.
Run with: blender -b --python engineering_blender.py -- scene.json output.mp4
Requires Blender 4.x. Components are illustrative unless supplied as validated assets.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from model_assets import load_component

def material(name, color, alpha=1.0, metallic=0.2):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, alpha)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = 0.3
    bsdf.inputs["Alpha"].default_value = alpha
    if alpha < 1:
        mat.surface_render_method = "DITHERED"
    return mat

def cube(name, location, scale, mat, bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modifier = obj.modifiers.new("Soft machined edges", "BEVEL")
    modifier.width = min(bevel, min(scale) / 5)
    modifier.segments = 3
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    obj.data.materials.append(mat)
    return obj

def animate_location(obj, start, end, frames):
    obj.location = start
    obj.keyframe_insert(data_path="location", frame=1)
    obj.location = end
    obj.keyframe_insert(data_path="location", frame=frames)
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"

def make_scene(spec, spec_dir=Path(".")):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    fps = int(spec.get("fps", 24))
    duration = float(spec.get("duration_seconds", 8))
    if not 1 <= duration <= 120 or not 12 <= fps <= 60:
        raise ValueError("Unsupported duration or fps")
    frames = max(2, round(fps * duration))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.fps = fps
    scene.frame_end = frames
    scene.render.resolution_x = int(spec.get("width", 1280))
    scene.render.resolution_y = int(spec.get("height", 720))
    scene.render.resolution_percentage = 100
    if not (320 <= scene.render.resolution_x <= 3840 and 240 <= scene.render.resolution_y <= 2160):
        raise ValueError("Unsupported resolution")
    scene.world.color = (0.025, 0.035, 0.055)
    components = spec.get("components")
    if not isinstance(components, list) or not 1 <= len(components) <= 80:
        raise ValueError("Supply 1-80 explicitly authored components")
    names = set()
    for i, item in enumerate(components):
        name = str(item["name"])
        if name in names:
            raise ValueError("Duplicate component name")
        names.add(name)
        dims = [float(v) for v in item.get("dimensions", [1, 1, 1])]
        pos = [float(v) for v in item["position"]]
        if len(dims) != 3 or len(pos) != 3 or any(not 0.01 <= d <= 20 for d in dims):
            raise ValueError("Invalid component dimensions/position")
        rgba = item.get("color", [0.12, 0.65, 0.8])
        if len(rgba) != 3 or any(not 0 <= float(c) <= 1 for c in rgba):
            raise ValueError("Invalid RGB color")
        alpha = float(item.get("opacity", 1))
        if not 0.05 <= alpha <= 1:
            raise ValueError("Invalid opacity")
        obj = load_component(item["asset"], name, spec_dir)[0] if "asset" in item else cube(name, pos, dims, material(name + "_mat", rgba, alpha, float(item.get("metallic", 0.2))))
        if "asset" in item:
            obj.location = pos
        if item.get("highlight") and obj.type == "MESH":
            obj.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.08, 0.55, 0.8, 1)
            obj.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.5
        offset = Vector(item.get("explode_offset", [0, 0, 0]))
        if len(offset) != 3:
            raise ValueError("explode_offset must be a 3-vector")
        if spec.get("animation", "explode") == "assemble":
            animate_location(obj, Vector(pos) + offset, Vector(pos), frames)
        else:
            animate_location(obj, Vector(pos), Vector(pos) + offset, frames)
    bpy.ops.object.camera_add(location=(8, -11, 8))
    camera = bpy.context.object
    direction = Vector((0, 0, 0.4)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = float(spec.get("camera_scale", 11))
    scene.camera = camera
    camera.keyframe_insert(data_path="location", frame=1)
    camera.location.x += float(spec.get("camera_dolly", 0.8))
    camera.keyframe_insert(data_path="location", frame=frames)
    for loc, power, size in [((2, -5, 9), 1300, 7), ((-6, 2, 4), 900, 5)]:
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object.data
        light.energy = power
        light.shape = "DISK"
        light.size = size
    return scene

def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 2:
        raise SystemExit("Usage: blender -b --python engineering_blender.py -- spec.json output.mp4")
    spec = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    scene = make_scene(spec, Path(args[0]).resolve().parent)
    target = Path(args[1]).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.filepath = str(target)
    bpy.ops.render.render(animation=True)
    print("Rendered:", target)

if __name__ == "__main__":
    main()
