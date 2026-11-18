"""Original one-tile isometric lamp diorama with a locked true-iso camera."""

from pathlib import Path

import bpy
from mathutils import Vector

from common import area_light, camera, cube, cylinder, material, reset_scene


TILE_M = 0.8


def move_to(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def rod(name, start, end, radius, mat, collection):
    axis = Vector(end) - Vector(start)
    center = (Vector(start) + Vector(end)) / 2
    obj = cylinder(name, center, radius, axis.length, mat, vertices=16, edge=0.005)
    obj.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()
    return move_to(obj, collection)


def parent_keep_world(obj, pivot):
    bpy.context.view_layer.update()
    transform = obj.matrix_world.copy()
    obj.parent = pivot
    obj.matrix_world = transform


def make_scene(spec, spec_dir=Path(".")):
    if abs(float(spec.get("tile_size_m", TILE_M)) - TILE_M) > 1e-8:
        raise ValueError("This authored diorama uses a 0.8 m tile")
    scene = reset_scene(spec, background=(0.055, 0.09, 0.12))
    scene.unit_settings.system = "METRIC"
    kit = bpy.data.collections.new("COL_Iso_One_Tile_Kit")
    scene.collection.children.link(kit)
    tile_side = material("Iso tile slate edge", (0.065, 0.19, 0.23), roughness=0.9)
    tile_top = material("Iso tile mint top", (0.22, 0.49, 0.47), roughness=0.85)
    brass = material("Iso warm brass", (0.8, 0.43, 0.15), metallic=0.35, roughness=0.46)
    blue = material("Iso blue enamel", (0.08, 0.27, 0.4), roughness=0.4)
    cream = material("Iso cream paper", (0.85, 0.76, 0.55), roughness=0.95)
    ink = material("Iso dark ink", (0.1, 0.2, 0.22), roughness=1)
    glow_mat = material("Iso warm diffuser", (1.0, 0.64, 0.23), roughness=0.6,
                        emission=(1.0, 0.48, 0.1), emission_strength=0.1)
    # The square tile has a center pivot and an explicit 1x1 footprint for kit reuse.
    tile = move_to(cube("SM_Iso_Tile", (0, 0, -0.045),
                        (TILE_M, TILE_M, 0.09), tile_side, edge=0.012), kit)
    tile["tile_size_m"] = TILE_M
    tile["footprint_cells"] = [1, 1]
    tile["pivot_rule"] = "center"
    move_to(cube("SM_Iso_Tile_Top", (0, 0, 0.006),
                 (TILE_M - 0.02, TILE_M - 0.02, 0.012), tile_top, edge=0.006), kit)
    move_to(cube("SM_Iso_Notebook", (-0.17, -0.16, 0.03),
                 (0.28, 0.2, 0.025), cream, edge=0.008), kit)
    move_to(cube("SM_Iso_Notebook_Spine", (-0.3, -0.16, 0.047),
                 (0.018, 0.2, 0.008), blue), kit)
    move_to(cube("SM_Iso_Paper_Line", (-0.18, -0.16, 0.047),
                 (0.09, 0.006, 0.002), ink), kit)

    base_point = (0.2, 0.16)
    move_to(cylinder("SM_Iso_Lamp_Base", (*base_point, 0.045),
                     0.12, 0.075, blue, edge=0.009), kit)
    rod("SM_Iso_Lower_Arm", (0.18, 0.16, 0.1), (0.12, 0.11, 0.34),
        0.015, brass, kit)
    move_to(cylinder("SM_Iso_Elbow", (0.12, 0.11, 0.34),
                     0.027, 0.04, blue), kit)
    bpy.ops.object.empty_add(location=(0.12, 0.11, 0.34))
    pivot = bpy.context.object
    pivot.name = "Iso lamp pivot"
    move_to(pivot, kit)
    upper = rod("SM_Iso_Upper_Arm", (0.12, 0.11, 0.34), (-0.11, -0.07, 0.49),
                0.014, brass, kit)
    parent_keep_world(upper, pivot)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.125, radius2=0.045,
                                    depth=0.14, location=(-0.12, -0.08, 0.415))
    shade = move_to(bpy.context.object, kit)
    shade.name = "SM_Iso_Lamp_Shade"
    shade.data.materials.append(blue)
    bevel = shade.modifiers.new("Graphic rim", "BEVEL")
    bevel.width = 0.006
    bevel.segments = 2
    parent_keep_world(shade, pivot)
    diffuser = move_to(cylinder("SM_Iso_Diffuser", (-0.12, -0.08, 0.345),
                                0.105, 0.007, glow_mat), kit)
    parent_keep_world(diffuser, pivot)
    bpy.ops.object.light_add(type="SPOT", location=(-0.12, -0.08, 0.33))
    task = move_to(bpy.context.object, kit)
    task.name = "Iso task light"
    task.data.color = (1.0, 0.63, 0.24)
    task.data.spot_size = 1.25
    task.data.spot_blend = 0.3
    parent_keep_world(task, pivot)

    pivot.rotation_euler.y = 0.3
    pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    pivot.rotation_euler.y = -0.23
    pivot.keyframe_insert(data_path="rotation_euler", frame=55)
    pivot.keyframe_insert(data_path="rotation_euler", frame=72)
    glow = glow_mat.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    glow.default_value = 0.1
    glow.keyframe_insert(data_path="default_value", frame=1)
    glow.default_value = 3.0
    glow.keyframe_insert(data_path="default_value", frame=38)
    task.data.energy = 0
    task.data.keyframe_insert(data_path="energy", frame=1)
    task.data.energy = 145
    task.data.keyframe_insert(data_path="energy", frame=38)
    task.data.keyframe_insert(data_path="energy", frame=72)

    # Equal camera offsets give a true orthographic isometric axis projection.
    target = (0, 0, 0.12)
    cam = camera("CAM_Iso_Lamp", (1.5, -1.5, 1.62), target, ortho=1.85)
    cam["tile_size_m"] = TILE_M
    cam["locked_for_kit"] = True
    area_light("Iso soft key", (0.35, -0.65, 1.5), 160, 1.0,
               target=(0, 0, 0.2))
    area_light("Iso cool fill", (-0.8, 0.7, 1.2), 80, 0.9,
               color=(0.5, 0.8, 1.0), target=(0, 0, 0.2))
    return scene
