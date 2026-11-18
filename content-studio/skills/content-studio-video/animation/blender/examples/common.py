"""Small reusable Blender primitives for the original headless gallery scenes."""

import math
import bpy
from mathutils import Vector


def reset_scene(spec, background=(0.018, 0.025, 0.04)):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if bpy.app.version >= (5, 0) else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = int(spec.get("width", 1280))
    scene.render.resolution_y = int(spec.get("height", 720))
    scene.render.resolution_percentage = 100
    scene.render.fps = int(spec.get("fps", 24))
    scene.frame_start = 1
    scene.frame_end = int(spec.get("frames", 96))
    if not (320 <= scene.render.resolution_x <= 3840 and 240 <= scene.render.resolution_y <= 2160):
        raise ValueError("Unsupported gallery resolution")
    if not (12 <= scene.render.fps <= 60 and 2 <= scene.frame_end <= 720):
        raise ValueError("Unsupported gallery frame count or frame rate")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*background, 1)
    bg.inputs["Strength"].default_value = 0.7
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.color_mode = "RGBA"
    return scene


def material(name, color, metallic=0, roughness=0.5, emission=None, emission_strength=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def bevel(obj, width=0.04, segments=3):
    mod = obj.modifiers.new("Machined edge", "BEVEL")
    mod.width = width
    mod.segments = segments
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def cube(name, location, dimensions, mat, edge=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if edge:
        bevel(obj, edge)
    return obj


def cylinder(name, location, radius, depth, mat, vertices=48, rotation=(0, 0, 0), edge=0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    if edge:
        bevel(obj, edge, 2)
    return obj


def sphere(name, location, radius, mat, segments=32, rings=16, scale=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    if scale is not None:
        obj.scale = scale
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def camera(name, location, target, lens=50, ortho=None):
    bpy.ops.object.camera_add(location=location)
    obj = bpy.context.object
    obj.name = name
    look_at(obj, target)
    if ortho is not None:
        obj.data.type = "ORTHO"
        obj.data.ortho_scale = ortho
    else:
        obj.data.lens = lens
    bpy.context.scene.camera = obj
    return obj


def area_light(name, location, energy, size, color=(1, 1, 1), target=(0, 0, 0)):
    bpy.ops.object.light_add(type="AREA", location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.energy = energy
    obj.data.shape = "DISK"
    obj.data.size = size
    obj.data.color = color
    look_at(obj, target)
    return obj


def linear_keys(obj, data_path, frames):
    """Use straight motion only for deliberately mechanical movement."""
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves
    else:
        curves = action.fcurves
    for curve in curves:
        if curve.data_path == data_path:
            for point in curve.keyframe_points:
                if round(point.co.x) in frames:
                    point.interpolation = "LINEAR"
