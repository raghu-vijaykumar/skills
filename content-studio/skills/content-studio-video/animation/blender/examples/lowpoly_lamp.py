"""Facet-first desk-lamp variant with a strict low-poly prop budget."""

from pathlib import Path

import bpy
from mathutils import Vector

from common import area_light, camera, cube, cylinder, material, reset_scene


def move_to(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def faceted_joint(name, location, radius, mat, collection):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return move_to(obj, collection)


def rod(name, start, end, radius, mat, collection):
    axis = Vector(end) - Vector(start)
    center = (Vector(start) + Vector(end)) / 2
    obj = cylinder(name, center, radius, axis.length, mat, vertices=6)
    obj.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()
    return move_to(obj, collection)


def parent_keep_world(obj, pivot):
    bpy.context.view_layer.update()
    transform = obj.matrix_world.copy()
    obj.parent = pivot
    obj.matrix_world = transform


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.014, 0.023, 0.04))
    prop = bpy.data.collections.new("COL_Lowpoly_Prop")
    scene.collection.children.link(prop)
    teal = material("Flat sea glass", (0.16, 0.43, 0.42), roughness=0.82)
    ochre = material("Flat ochre metal", (0.52, 0.32, 0.12), roughness=0.68)
    joint = material("Flat charcoal", (0.04, 0.065, 0.08), roughness=0.9)
    stage = material("Matte ink stage", (0.045, 0.065, 0.095), roughness=1)
    paper = material("Paper tile", (0.7, 0.54, 0.3), roughness=1)
    bulb = material("Graphic warm bulb", (0.9, 0.53, 0.18), roughness=1,
                    emission=(1.0, 0.55, 0.12), emission_strength=0.1)
    cube("SM_Lowpoly_Stage", (0, 0, -0.05), (2.2, 2.0, 0.08), stage)
    cube("SM_Lowpoly_Notebook", (-0.5, 0.04, 0), (0.32, 0.22, 0.016), paper)
    move_to(cylinder("SM_Lowpoly_Base", (0, 0, 0.035), 0.17, 0.07,
                     teal, vertices=8), prop)
    faceted_joint("SM_Lowpoly_Foot_Joint", (-0.1, 0, 0.11), 0.038, joint, prop)
    rod("SM_Lowpoly_Lower_Arm", (-0.1, 0, 0.11), (-0.17, 0, 0.37),
        0.024, ochre, prop)
    faceted_joint("SM_Lowpoly_Elbow", (-0.17, 0, 0.37), 0.042, joint, prop)
    bpy.ops.object.empty_add(location=(-0.17, 0, 0.37))
    pivot = bpy.context.object
    pivot.name = "Lowpoly lamp pivot"
    move_to(pivot, prop)
    upper = rod("SM_Lowpoly_Upper_Arm", (-0.17, 0, 0.37), (-0.4, 0, 0.51),
                0.021, ochre, prop)
    parent_keep_world(upper, pivot)
    cap = faceted_joint("SM_Lowpoly_Cap", (-0.4, 0, 0.51), 0.036, joint, prop)
    parent_keep_world(cap, pivot)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.15, radius2=0.055,
                                    depth=0.16, location=(-0.41, 0, 0.43))
    shade = bpy.context.object
    shade.name = "SM_Lowpoly_Shade"
    shade.data.materials.append(teal)
    move_to(shade, prop)
    parent_keep_world(shade, pivot)
    diffuser = move_to(cylinder("SM_Lowpoly_Bulb", (-0.41, 0, 0.347),
                                0.12, 0.01, bulb, vertices=8), prop)
    parent_keep_world(diffuser, pivot)
    bpy.ops.object.light_add(type="SPOT", location=(-0.41, 0, 0.32))
    task = bpy.context.object
    task.name = "Graphic task light"
    task.data.color = (1.0, 0.58, 0.2)
    task.data.spot_size = 0.95
    task.data.spot_blend = 0.1
    move_to(task, prop)
    parent_keep_world(task, pivot)

    pivot.rotation_euler.y = 0.2
    pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    pivot.rotation_euler.y = -0.3
    pivot.keyframe_insert(data_path="rotation_euler", frame=76)
    pivot.keyframe_insert(data_path="rotation_euler", frame=96)
    glow = bulb.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    glow.default_value = 0.1
    glow.keyframe_insert(data_path="default_value", frame=1)
    glow.default_value = 3.5
    glow.keyframe_insert(data_path="default_value", frame=45)
    task.data.energy = 0
    task.data.keyframe_insert(data_path="energy", frame=1)
    task.data.energy = 160
    task.data.keyframe_insert(data_path="energy", frame=45)
    task.data.keyframe_insert(data_path="energy", frame=96)
    cam = camera("Lowpoly camera", (1.1, -1.6, 0.94), (-0.18, 0, 0.27), ortho=1.45)
    cam.keyframe_insert(data_path="location", frame=1)
    cam.location = (1.04, -1.53, 0.9)
    cam.keyframe_insert(data_path="location", frame=96)
    area_light("Graphic key", (0.3, -1.3, 1.25), 180, 1.0,
               target=(-0.2, 0, 0.25))
    return scene
