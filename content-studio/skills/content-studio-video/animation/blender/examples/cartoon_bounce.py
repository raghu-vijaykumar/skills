"""Original orange cartoon mascot with keyed squash, stretch, jump and shadow."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, material, reset_scene, sphere


def attach(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def hose(name, points, radius, mat, parent):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, position in zip(spline.bezier_points, points):
        point.co = position
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.materials.append(mat)
    return attach(obj, parent)


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.72, 0.81, 0.75))
    orange = material("Cartoon bold orange", (0.92, 0.18, 0.025), roughness=0.93)
    yellow = material("Cartoon yellow mitts", (0.95, 0.59, 0.045), roughness=0.94)
    cream = material("Cartoon eye cream", (0.99, 0.95, 0.78), roughness=0.94)
    teal = material("Cartoon pupil teal", (0.04, 0.22, 0.23), roughness=1)
    ink = material("Cartoon graphic ink", (0.025, 0.10, 0.13), roughness=1)
    ground = material("Cartoon mint stage", (0.54, 0.75, 0.67), roughness=1)
    shadow_mat = material("Cartoon blue shadow", (0.10, 0.30, 0.45), roughness=1)
    cube("Cartoon mint floor", (0, 0, -0.08), (8, 8, 0.16), ground)
    shadow = sphere("SM_Cartoon_Shadow", (0, 0.05, 0.012), 0.62,
                    shadow_mat, segments=32, rings=12, scale=(1.0, 0.43, 0.018))

    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    root.name = "Cartoon bounce control"
    attach(sphere("SM_Cartoon_Body", (0, 0, 0.63), 0.58, orange,
                  segments=32, rings=20), root)
    for x, side in ((-0.20, "Left"), (0.20, "Right")):
        attach(sphere(f"SM_Cartoon_{side}_Eye", (x, -0.515, 0.78),
                      0.15, cream, segments=20, rings=12,
                      scale=(0.86, 0.32, 1.16)), root)
        attach(sphere(f"Cartoon {side} pupil", (x + 0.018, -0.565, 0.76),
                      0.075, teal, segments=16, rings=10,
                      scale=(0.78, 0.30, 1.15)), root)
        sign = -1 if x < 0 else 1
        hose(f"Cartoon {side} rubber arm",
             [(sign * 0.48, 0, 0.72), (sign * 0.67, -0.03, 0.72),
              (sign * 0.78, -0.06, 0.91)], 0.055, ink, root)
        attach(sphere(f"SM_Cartoon_{side}_Mitt", (sign * 0.80, -0.07, 0.93),
                      0.15, yellow, segments=20, rings=12,
                      scale=(1.15, 0.83, 0.92)), root)
    hose("Cartoon broad smile",
         [(-0.18, -0.56, 0.48), (-0.09, -0.59, 0.42),
          (0, -0.61, 0.40), (0.09, -0.59, 0.42),
          (0.18, -0.56, 0.48)], 0.014, ink, root)
    for x in (-0.28, 0.28):
        attach(sphere("Cartoon cheek blush", (x, -0.50, 0.52),
                      0.075, yellow, segments=16, rings=8,
                      scale=(1, 0.15, 0.53)), root)

    # Strong pose keys make the same simple silhouette read as squash then jump.
    for frame, height, xy, z in ((1, 0, 1, 1),
                                 (15, 0, 1.20, 0.70),
                                 (24, 0.28, 0.83, 1.32),
                                 (36, 0.92, 0.88, 1.22),
                                 (44, 1.05, 1, 1),
                                 (58, 0.08, 1.08, 0.90),
                                 (62, 0, 1.22, 0.68),
                                 (72, 0, 1, 1)):
        root.location.z = height
        root.scale = (xy, xy, z)
        root.keyframe_insert(data_path="location", frame=frame)
        root.keyframe_insert(data_path="scale", frame=frame)
        # The contact shadow contracts under the airborne pose.
        shadow.scale.x = 1 - min(height, 1.05) * 0.34
        shadow.scale.y = 0.43 - min(height, 1.05) * 0.13
        shadow.keyframe_insert(data_path="scale", frame=frame)

    camera("Cartoon mascot camera", (0, -5.6, 1.35),
           (0, 0, 1.12), ortho=5.00)
    area_light("Cartoon soft key", (-2.5, -3, 4.5), 700, 3,
               target=(0, 0, 0.8))
    scene.render.use_freestyle = True
    scene.view_layers[0].freestyle_settings.linesets[0].linestyle.thickness = 2.8
    scene["cartoon_shape_language"] = "friendly circular mascot, enlarged mitts, rubber-hose arms"
    return scene
