"""Original anime bust with hard cel bands, clear contour and pose accents."""

from pathlib import Path
import math

import bpy
from mathutils import Vector

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def cel(name, color):
    """Use exactly three hard value regions rather than continuous PBR shading."""
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = (*color, 1)
    shader_rgb = nodes.new("ShaderNodeShaderToRGB")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    stops = ramp.color_ramp.elements
    stops.remove(stops[1])
    stops[0].position = 0
    stops[0].color = (*(value * 0.44 for value in color), 1)
    mid = stops.new(0.44)
    mid.color = (*color, 1)
    high = stops.new(0.8)
    high.color = (*(min(1, value * 1.2) for value in color), 1)
    emission = nodes.new("ShaderNodeEmission")
    links = mat.node_tree.links
    links.new(diffuse.outputs["BSDF"], shader_rgb.inputs["Shader"])
    links.new(shader_rgb.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    mat["cel_value_steps"] = 3
    return mat


def attach(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def rod(name, start, end, radius, mat):
    axis = Vector(end) - Vector(start)
    midpoint = (Vector(start) + Vector(end)) / 2
    obj = cylinder(name, midpoint, radius, axis.length, mat, vertices=16)
    obj.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()
    return obj


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.63, 0.72, 0.72))
    navy = cel("Anime ink navy hair", (0.055, 0.095, 0.22))
    skin = cel("Anime peach skin", (0.94, 0.58, 0.43))
    coat = cel("Anime cobalt coat", (0.09, 0.26, 0.7))
    red = cel("Anime red scarf", (0.83, 0.13, 0.15))
    cream = cel("Anime eye cream", (0.94, 0.93, 0.81))
    eye = cel("Anime iris teal", (0.03, 0.42, 0.43))
    ink = material("Anime line ink", (0.012, 0.025, 0.08), roughness=1)
    backdrop = material("Anime paper backdrop", (0.67, 0.76, 0.74), roughness=1)
    halo = material("Anime graphic halo", (0.92, 0.78, 0.41), roughness=1)
    cube("Anime backdrop", (0, 1.8, 1.45), (7, 0.05, 4), backdrop)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.06, depth=0.012,
                                        location=(0.0, 1.70, 1.65),
                                        rotation=(math.pi / 2, 0, 0))
    disc = bpy.context.object
    disc.name = "Anime graphic disc"
    disc.data.materials.append(halo)

    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    root.name = "Anime character root"
    attach(cube("SM_Anime_Torso", (0, 0, 0.9),
                (0.78, 0.37, 0.94), coat, edge=0.12), root)
    attach(cube("Anime collar left", (-0.17, -0.22, 1.41),
                (0.26, 0.08, 0.19), cream, edge=0.025), root)
    attach(cube("Anime collar right", (0.17, -0.22, 1.41),
                (0.26, 0.08, 0.19), cream, edge=0.025), root)
    attach(cylinder("Anime neck", (0, 0, 1.48), 0.12, 0.3, skin), root)
    attach(cube("Anime scarf knot", (0, -0.29, 1.37),
                (0.22, 0.10, 0.16), red, edge=0.035), root)
    bpy.ops.object.empty_add(location=(0, -0.27, 1.37))
    scarf_control = attach(bpy.context.object, root)
    scarf_control.name = "Anime scarf control"
    attach(cube("SM_Anime_Scarf_Tail", (-0.09, -0.34, 1.05),
                (0.16, 0.05, 0.52), red, edge=0.025), scarf_control)

    bpy.ops.object.empty_add(location=(0, 0, 1.62))
    head_control = attach(bpy.context.object, root)
    head_control.name = "Anime head control"
    attach(sphere("SM_Anime_Head", (0, -0.02, 2.04), 0.52,
                  skin, scale=(0.94, 0.78, 1.08)), head_control)
    attach(sphere("SM_Anime_Hair_Cap", (0, 0.045, 2.39), 0.52,
                  navy, scale=(1.04, 0.88, 0.56)), head_control)
    for x in (-0.43, 0.43):
        attach(cube(f"Anime side hair {x}", (x, 0.015, 1.95),
                    (0.16, 0.34, 0.66), navy, edge=0.07), head_control)
    for x, height in ((-0.32, 2.31), (-0.12, 2.38), (0.12, 2.37), (0.32, 2.30)):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.13,
                                        radius2=0.005, depth=0.38,
                                        location=(x, -0.36, height),
                                        rotation=(math.pi, 0, 0))
        fringe = bpy.context.object
        fringe.name = f"Anime fringe {x}"
        fringe.data.materials.append(navy)
        attach(fringe, head_control)

    for x, side in ((-0.2, "Left"), (0.2, "Right")):
        eye_white = attach(sphere(f"SM_Anime_{side}_Eye", (x, -0.425, 2.08),
                                  0.142, cream, scale=(0.84, 0.33, 1.22)), head_control)
        pupil = attach(sphere(f"Anime {side} iris", (x, -0.468, 2.07),
                              0.078, eye, scale=(0.75, 0.32, 1.27)), head_control)
        attach(cube(f"Anime {side} upper lid", (x, -0.47, 2.24),
                    (0.27, 0.025, 0.025), ink, edge=0.008), head_control)
        for frame, height in ((1, 1), (31, 1), (36, 0.06), (40, 1), (72, 1)):
            eye_white.scale.z = 1.22 * height
            eye_white.keyframe_insert(data_path="scale", frame=frame)
            pupil.scale.z = 1.27 * height
            pupil.keyframe_insert(data_path="scale", frame=frame)
    # A shallow graphic smile reads at the compact GIF size without facial texture noise.
    mouth_curve = bpy.data.curves.new("Anime smile stroke", "CURVE")
    mouth_curve.dimensions = "3D"
    mouth_curve.bevel_depth = 0.007
    mouth_curve.bevel_resolution = 2
    smile = mouth_curve.splines.new("POLY")
    smile.points.add(4)
    for point, location in zip(smile.points,
                               ((-0.1, -0.48, 1.87), (-0.05, -0.485, 1.854),
                                (0, -0.49, 1.85), (0.05, -0.485, 1.854),
                                (0.1, -0.48, 1.87))):
        point.co = (*location, 1)
    smile_obj = bpy.data.objects.new("Anime smile", mouth_curve)
    scene.collection.objects.link(smile_obj)
    mouth_curve.materials.append(ink)
    attach(smile_obj, head_control)

    bpy.ops.object.empty_add(location=(0.44, 0, 1.35))
    arm_control = attach(bpy.context.object, root)
    arm_control.name = "Anime arm control"
    # Keep the shoulder filled at every keyed angle so the animated sleeve reads as attached.
    attach(sphere("Anime shoulder joint", (0.44, 0, 1.35),
                  0.19, coat), root)
    attach(rod("SM_Anime_Raised_Arm", (0.44, 0, 1.35),
               (0.78, -0.03, 1.0), 0.13, coat), arm_control)
    attach(rod("Anime forearm", (0.78, -0.03, 1.0),
               (0.94, -0.1, 0.79), 0.11, coat), arm_control)
    attach(sphere("Anime raised hand", (0.94, -0.1, 0.78),
                  0.13, skin), arm_control)
    attach(rod("Anime resting arm", (-0.44, 0, 1.35),
               (-0.62, 0, 0.8), 0.13, coat), root)
    attach(sphere("Anime resting hand", (-0.62, 0, 0.77),
                  0.13, skin), root)
    for frame, arm_angle, tilt, ribbon in ((1, 0, -0.08, 0),
                                           (24, -1.3, 0.09, 0.28),
                                           (40, -1.65, -0.1, -0.2),
                                           (58, -1.55, 0.1, 0.24),
                                           (72, -1.55, 0.05, 0.12)):
        arm_control.rotation_euler.y = arm_angle
        arm_control.keyframe_insert(data_path="rotation_euler", frame=frame)
        head_control.rotation_euler.z = tilt
        head_control.keyframe_insert(data_path="rotation_euler", frame=frame)
        scarf_control.rotation_euler.y = ribbon
        scarf_control.keyframe_insert(data_path="rotation_euler", frame=frame)

    camera("Anime portrait camera", (0, -5.3, 1.8),
           (0, 0, 1.56), ortho=4.7)
    area_light("Anime graphic key", (-2, -3, 5), 850, 1.0,
               target=(0, 0, 1.8))
    scene.render.use_freestyle = True
    scene.view_layers[0].freestyle_settings.linesets[0].linestyle.thickness = 2.0
    return scene
