"""Original three-color kinetic sculpture with deliberate negative space."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def parent_keep_world(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.91, 0.88, 0.81))
    scene.unit_settings.system = "METRIC"
    bone = material("Minimal warm bone", (0.91, 0.88, 0.81), roughness=1,
                    emission=(0.91, 0.88, 0.81), emission_strength=0.12)
    ink = material("Minimal matte charcoal", (0.035, 0.043, 0.051), roughness=1)
    red = material("Minimal single red accent", (0.78, 0.09, 0.075), roughness=0.92)
    # The orthographic stage and the right half of the frame remain nearly empty.
    cube("Minimal seamless floor", (0, 0, -0.065), (9, 5, 0.13), bone)
    cube("Minimal seamless wall", (0, 2.35, 1.5), (9, 0.1, 3.2), bone)
    base = cube("SM_Minimal_Base", (-1.15, 0, 0.045), (1.48, 0.30, 0.09), ink)
    base["reduced_form"] = True
    support = cube("SM_Minimal_Support", (-1.64, 0, 1.12),
                   (0.065, 0.065, 2.17), ink)
    cube("Minimal upper beam", (-1.13, 0, 2.19), (1.08, 0.065, 0.065), ink)
    bpy.ops.object.empty_add(location=(-0.62, 0, 2.19))
    pivot = bpy.context.object
    pivot.name = "Minimal pendulum pivot"
    # One small joint and one hairline arc clarify the mechanism without adding a motif.
    cylinder("Minimal visible pivot pin", (-0.62, -0.075, 2.19),
             0.061, 0.025, ink, vertices=24,
             rotation=(math.pi / 2, 0, 0))
    path = bpy.data.curves.new("Minimal travel arc path", "CURVE")
    path.dimensions = "3D"
    path.bevel_depth = 0.003
    path.bevel_resolution = 1
    spline = path.splines.new("POLY")
    spline.points.add(16)
    for index, point in enumerate(spline.points):
        angle = -0.8 + index * 0.1
        point.co = (-0.62 + 1.44 * math.sin(angle), 0.08,
                    2.19 - 1.44 * math.cos(angle), 1)
    path.materials.append(ink)
    bpy.context.scene.collection.objects.link(
        bpy.data.objects.new("Minimal swing arc", path))
    rod = parent_keep_world(cylinder("SM_Minimal_Rod", (-0.62, 0, 1.47),
                                     0.026, 1.44, ink, vertices=16), pivot)
    bob = parent_keep_world(sphere("SM_Minimal_Red_Bob", (-0.62, 0, 0.74),
                                   0.205, red), pivot)
    # A diminishing angular cycle gives one action without crowding the composition.
    for frame, angle in ((1, -0.78), (20, 0.78), (38, -0.68),
                         (56, 0.54), (72, -0.38)):
        pivot.rotation_euler.y = angle
        pivot.keyframe_insert(data_path="rotation_euler", frame=frame)

    camera("Minimal pendulum camera", (0, -6.5, 1.70),
           (0, 0, 1.18), ortho=6.45)
    area_light("Minimal softbox", (-2, -3, 4.2), 550, 3.3,
               target=(-0.75, 0, 1.15))
    scene["minimal_palette"] = "warm bone, matte charcoal, one red accent"
    scene["negative_space_side"] = "right"
    return scene
