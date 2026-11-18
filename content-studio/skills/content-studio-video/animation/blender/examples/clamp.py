"""Original realistic clamp with a visible screw-driven closing action."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def thread_curve(radius, height, turns, mat):
    curve = bpy.data.curves.new("Thread path", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = 0.014
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    count = turns * 32 + 1
    spline.points.add(count - 1)
    for i, point in enumerate(spline.points):
        angle = i / 32 * 2 * math.pi
        point.co = (radius * math.cos(angle), radius * math.sin(angle),
                    i / (count - 1) * height, 1)
    obj = bpy.data.objects.new("Screw thread", curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def attach(obj, root):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = root
    obj.matrix_world = world


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.012, 0.018, 0.026))
    gunmetal = material("Gunmetal cast frame", (0.09, 0.16, 0.18), metallic=0.78, roughness=0.28)
    steel = material("Brushed steel", (0.52, 0.59, 0.6), metallic=0.93, roughness=0.24)
    dark = material("Dark grip", (0.055, 0.065, 0.07), metallic=0.12, roughness=0.5)
    bronze = material("Warm accent", (0.55, 0.29, 0.11), metallic=0.7, roughness=0.3)
    block = material("Demonstration block material", (0.5, 0.27, 0.1), metallic=0, roughness=0.65)
    stage = material("Slate stage", (0.055, 0.065, 0.075), roughness=0.86)

    cube("Stage", (0, 0, -0.2), (12, 12, 0.25), stage, 0.08)
    # The visible C profile is one joined parent with separately editable arms.
    bpy.ops.object.empty_add(location=(0, 0, 0))
    frame = bpy.context.object
    frame.name = "Clamp frame"
    for name, position, size in [
        ("Clamp spine", (-1.48, 0, 1.4), (0.42, 0.72, 2.45)),
        ("Clamp upper arm", (-0.33, 0, 2.45), (2.7, 0.72, 0.37)),
        ("Clamp lower arm", (-0.33, 0, 0.35), (2.7, 0.72, 0.37)),
    ]:
        attach(cube(name, position, size, gunmetal, 0.08), frame)
    cylinder("Fixed pad", (0.66, 0, 2.2), 0.34, 0.12, steel, edge=0.025)
    cylinder("Lower guide", (0.66, 0, 0.6), 0.27, 0.19, bronze, edge=0.025)
    cube("Demonstration block", (0.66, 0, 2.01), (0.62, 0.55, 0.22), block, 0.025)

    bpy.ops.object.empty_add(location=(0.66, 0, 0.73))
    screw_root = bpy.context.object
    screw_root.name = "Screw control"
    screw = cylinder("Lead screw", (0.66, 0, 1.10), 0.115, 1.08, steel)
    attach(screw, screw_root)
    thread = thread_curve(0.121, 0.78, 9, bronze)
    thread.location = (0.66, 0, 0.70)
    attach(thread, screw_root)
    pad = cylinder("Pressure pad", (0.66, 0, 1.55), 0.31, 0.11, steel, edge=0.025)
    attach(pad, screw_root)
    handle = cylinder("T handle", (0.66, 0, 0.73), 0.052, 1.06, steel,
                      rotation=(0, math.pi / 2, 0), edge=0.012)
    attach(handle, screw_root)
    for x in (0.13, 1.19):
        attach(sphere("Handle grip", (x, 0, 0.73), 0.095, dark), screw_root)

    screw_root.location.z = 0.73
    screw_root.keyframe_insert(data_path="location", frame=1)
    screw_root.rotation_euler.z = 0
    screw_root.keyframe_insert(data_path="rotation_euler", frame=1)
    screw_root.location.z = 1.04
    screw_root.keyframe_insert(data_path="location", frame=75)
    screw_root.rotation_euler.z = math.tau * 1.5
    screw_root.keyframe_insert(data_path="rotation_euler", frame=75)
    screw_root.keyframe_insert(data_path="location", frame=96)
    screw_root.keyframe_insert(data_path="rotation_euler", frame=96)

    cam = camera("Hero camera", (4.8, -7.4, 4.0), (-0.27, 0, 1.32), lens=50)
    cam.keyframe_insert(data_path="location", frame=1)
    cam.location = (4.5, -7.0, 3.8)
    cam.keyframe_insert(data_path="location", frame=96)
    area_light("Large key", (0.4, -3.4, 5.4), 1100, 4.0, target=(0, 0, 1.4))
    area_light("Cool rim", (-3.4, 1.9, 4.0), 1500, 3.0, color=(0.52, 0.8, 1.0), target=(0, 0, 1.3))
    area_light("Warm fill", (3.1, 3.2, 2.8), 850, 3.5, color=(1.0, 0.65, 0.42), target=(0, 0, 1.4))
    return scene
