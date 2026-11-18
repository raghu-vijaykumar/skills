"""Measured steel clamp lamp with restrained PBR materials and product lighting."""

from pathlib import Path
from math import cos, pi, sin

import bpy
from mathutils import Vector

from common import area_light, camera, cube, cylinder, material, reset_scene


SHADE_DIAMETER_M = 0.17


def to_collection(obj, collection):
    for previous in list(obj.users_collection):
        previous.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def parent_keep_world(obj, pivot):
    bpy.context.view_layer.update()
    matrix = obj.matrix_world.copy()
    obj.parent = pivot
    obj.matrix_world = matrix


def steel_rod(name, start, end, radius, mat, collection):
    axis = Vector(end) - Vector(start)
    midpoint = (Vector(start) + Vector(end)) / 2
    obj = cylinder(name, midpoint, radius, axis.length, mat, vertices=32, edge=0.002)
    obj.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()
    return to_collection(obj, collection)


def wood_material():
    """Add subdued grain and roughness variation without photographic texture reuse."""
    wood = material("PBR natural desk wood", (0.34, 0.19, 0.09), roughness=0.72)
    nodes = wood.node_tree.nodes
    links = wood.node_tree.links
    shader = nodes.get("Principled BSDF")
    tex = nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 3
    tex.inputs["Detail"].default_value = 2
    stretch = nodes.new("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (3, 20, 4)
    coordinate = nodes.new("ShaderNodeTexCoord")
    links.new(coordinate.outputs["Generated"], stretch.inputs[0])
    links.new(stretch.outputs[0], tex.inputs["Vector"])
    grain = nodes.new("ShaderNodeValToRGB")
    grain.color_ramp.elements[0].position = 0.3
    grain.color_ramp.elements[0].color = (0.085, 0.038, 0.012, 1)
    grain.color_ramp.elements[1].position = 0.7
    grain.color_ramp.elements[1].color = (0.23, 0.105, 0.035, 1)
    links.new(tex.outputs["Fac"], grain.inputs[0])
    links.new(grain.outputs[0], shader.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.003
    links.new(tex.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return wood


def cable(name, points, mat, collection):
    curve = bpy.data.curves.new(name + " path", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.004
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, location in zip(spline.points, points):
        point.co = (*location, 1)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    curve.materials.append(mat)
    return obj


def tension_spring(name, start, end, radius, turns, mat, collection):
    """Give the adjustable arm a visible tension mechanism at real scale."""
    origin = Vector(start)
    axis = Vector(end) - origin
    tangent = axis.normalized()
    across = tangent.cross(Vector((0, 1, 0))).normalized()
    around = tangent.cross(across).normalized()
    points = []
    for index in range(turns * 10 + 1):
        fraction = index / (turns * 10)
        angle = 2 * pi * turns * fraction
        center = origin + axis * fraction
        points.append(center + radius * (across * cos(angle) + around * sin(angle)))
    spring = cable(name, points, mat, collection)
    spring.data.bevel_depth = 0.0016
    return spring


def make_scene(spec, spec_dir=Path(".")):
    if abs(float(spec.get("shade_diameter_m", SHADE_DIAMETER_M)) - SHADE_DIAMETER_M) > 1e-8:
        raise ValueError("This photo-referenced shade is 0.17 m wide")
    scene = reset_scene(spec, background=(0.07, 0.085, 0.105))
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1
    parts = bpy.data.collections.new("COL_Realistic_Lamp")
    scene.collection.children.link(parts)
    paint = material("PBR warm white powder-coated steel", (0.68, 0.67, 0.64),
                     metallic=0.45, roughness=0.38)
    hinge = material("PBR brushed steel hardware", (0.48, 0.5, 0.52),
                     metallic=0.92, roughness=0.32)
    abs_black = material("PBR black ABS clamp", (0.045, 0.047, 0.05),
                         metallic=0, roughness=0.65)
    paper = material("PBR warm paper", (0.78, 0.72, 0.62), metallic=0, roughness=0.9)
    rubber = material("PBR rubber power cord", (0.027, 0.03, 0.035),
                      metallic=0, roughness=0.82)
    spring_steel = material("PBR dark tension spring", (0.2, 0.22, 0.23),
                            metallic=0.88, roughness=0.44)
    glass = material("PBR frosted diffuser", (0.92, 0.85, 0.67),
                     metallic=0, roughness=0.65,
                     emission=(1, 0.73, 0.4), emission_strength=0.08)
    wood = wood_material()
    back = material("Matte studio backdrop", (0.095, 0.115, 0.13), roughness=1)
    to_collection(cube("SM_Real_Desk", (0, 0, -0.035),
                       (1.15, 0.86, 0.07), wood, edge=0.007), parts)
    cube("SM_Real_Backdrop", (0, 0, -0.23), (3, 3, 0.3), back)
    to_collection(cube("SM_Real_Notebook", (-0.23, -0.13, 0.012),
                       (0.27, 0.2, 0.024), paper, edge=0.003), parts)
    to_collection(cube("SM_Real_Notebook_Spine", (-0.362, -0.13, 0.025),
                       (0.008, 0.2, 0.004), abs_black), parts)
    for row in range(3):
        to_collection(cube(f"SM_Real_Page_Rule_{row}",
                           (-0.24, -0.18 + 0.035 * row, 0.025),
                           (0.1, 0.001, 0.001), hinge), parts)

    # The clamp straddles the 70 mm desk edge; its ABS pads and screw are separate.
    to_collection(cube("SM_Real_Clamp_Top", (0.38, -0.388, 0.022),
                       (0.115, 0.075, 0.025), abs_black, edge=0.004), parts)
    to_collection(cube("SM_Real_Clamp_Back", (0.38, -0.445, -0.04),
                       (0.115, 0.024, 0.15), hinge, edge=0.003), parts)
    to_collection(cube("SM_Real_Clamp_Bottom", (0.38, -0.387, -0.094),
                       (0.115, 0.076, 0.017), abs_black, edge=0.003), parts)
    to_collection(cylinder("SM_Real_Clamp_Screw", (0.38, -0.386, -0.11),
                           0.009, 0.085, hinge, edge=0.001), parts)
    to_collection(cylinder("SM_Real_Socket", (0.38, -0.36, 0.062),
                           0.032, 0.065, abs_black, edge=0.003), parts)
    base = (0.38, -0.36, 0.09)
    elbow = (0.17, -0.25, 0.42)
    head = (-0.22, -0.13, 0.55)
    for side, offset in (("A", -0.014), ("B", 0.014)):
        steel_rod(f"SM_Real_Lower_Arm_{side}",
                  (base[0], base[1] + offset, base[2]),
                  (elbow[0], elbow[1] + offset, elbow[2]), 0.008, paint, parts)
    to_collection(cylinder("SM_Real_Elbow", elbow, 0.026, 0.055,
                           hinge, rotation=(1.5708, 0, 0), edge=0.002), parts)
    for side, offset in (("Left", -0.032), ("Right", 0.032)):
        to_collection(cylinder(f"SM_Real_Elbow_Bolt_{side}",
                               (elbow[0], elbow[1] + offset, elbow[2]),
                               0.014, 0.004, hinge,
                               rotation=(1.5708, 0, 0), edge=0.001), parts)
    tension_spring("SM_Real_Lower_Tension", (0.35, -0.36, 0.13),
                   (0.2, -0.26, 0.39), 0.012, 17, spring_steel, parts)
    bpy.ops.object.empty_add(location=elbow)
    pivot = to_collection(bpy.context.object, parts)
    pivot.name = "Real lamp upper hinge"
    for side, offset in (("A", -0.014), ("B", 0.014)):
        arm = steel_rod(f"SM_Real_Upper_Arm_{side}",
                        (elbow[0], elbow[1] + offset, elbow[2]),
                        (head[0], head[1] + offset, head[2]), 0.007, paint, parts)
        parent_keep_world(arm, pivot)
    upper_spring = tension_spring("SM_Real_Upper_Tension",
                                  (0.125, -0.245, 0.44),
                                  (-0.16, -0.16, 0.55),
                                  0.012, 20, spring_steel, parts)
    parent_keep_world(upper_spring, pivot)
    lead = cable("SM_Real_Cord", [(0.15, -0.25, 0.44),
                                   (0.03, -0.245, 0.53),
                                   (-0.17, -0.155, 0.58),
                                   (-0.22, -0.13, 0.54)], rubber, parts)
    parent_keep_world(lead, pivot)
    bpy.ops.mesh.primitive_cone_add(vertices=64,
                                    radius1=SHADE_DIAMETER_M / 2,
                                    radius2=0.034, depth=0.145,
                                    location=(-0.22, -0.13, 0.455))
    shade = to_collection(bpy.context.object, parts)
    shade.name = "SM_Real_Shade"
    shade.data.materials.append(paint)
    shade["shade_diameter_m"] = SHADE_DIAMETER_M
    bevel = shade.modifiers.new("Rolled steel rim", "BEVEL")
    bevel.width = 0.003
    bevel.segments = 3
    parent_keep_world(shade, pivot)
    diffuser = to_collection(cylinder("SM_Real_Diffuser", (-0.22, -0.13, 0.382),
                                     0.072, 0.008, glass, edge=0.001), parts)
    parent_keep_world(diffuser, pivot)
    bpy.ops.object.light_add(type="SPOT", location=(-0.22, -0.13, 0.38))
    task = to_collection(bpy.context.object, parts)
    task.name = "Real task light"
    task.data.color = (1, 0.79, 0.55)
    task.data.spot_size = 1.18
    task.data.spot_blend = 0.65
    parent_keep_world(task, pivot)

    pivot.rotation_euler.y = 0.12
    pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    pivot.rotation_euler.y = -0.25
    pivot.keyframe_insert(data_path="rotation_euler", frame=56)
    pivot.keyframe_insert(data_path="rotation_euler", frame=72)
    emission = glass.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    emission.default_value = 0.08
    emission.keyframe_insert(data_path="default_value", frame=1)
    emission.default_value = 2.3
    emission.keyframe_insert(data_path="default_value", frame=38)
    task.data.energy = 0
    task.data.keyframe_insert(data_path="energy", frame=1)
    task.data.energy = 190
    task.data.keyframe_insert(data_path="energy", frame=38)
    task.data.keyframe_insert(data_path="energy", frame=72)
    camera("Realistic product camera", (1.08, -1.48, 0.98),
           (0.06, -0.15, 0.12), lens=32)
    area_light("Real product softbox", (0.1, -0.7, 1.35), 195, 1.1,
               target=(0, -0.12, 0.3))
    area_light("Real cool rim", (-0.75, 0.4, 1.15), 70, 0.7,
               color=(0.68, 0.82, 1), target=(-0.1, -0.1, 0.3))
    return scene
