"""Original SVG-like sprout icon with flat polygon fills and staged growth."""

from pathlib import Path
import math

import bpy

from common import camera, reset_scene


def flat(name, color):
    """Emission only keeps fills invariant under light and free of gradients."""
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*color, 1)
    mat.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    mat["flat_vector_fill"] = True
    return mat


def polygon(name, points, depth, mat):
    mesh = bpy.data.meshes.new(name + " flat path")
    mesh.from_pydata([(x, depth, z) for x, z in points], [],
                     [tuple(range(len(points)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    obj["vector_path_points"] = len(points)
    return obj


def disc(name, x, z, radius, depth, mat, segments=32, squash=(1, 1)):
    return polygon(name, [(x + radius * squash[0] * math.cos(2 * math.pi * i / segments),
                           z + radius * squash[1] * math.sin(2 * math.pi * i / segments))
                          for i in range(segments)], depth, mat)


def rect(name, x0, z0, x1, z1, depth, mat):
    return polygon(name, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], depth, mat)


def attach(obj, parent):
    """The mesh path is authored in local icon coordinates around its control."""
    obj.parent = parent
    return obj


def control(name, location):
    bpy.ops.object.empty_add(location=location)
    obj = bpy.context.object
    obj.name = name
    return obj


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.07, 0.17, 0.26))
    navy = flat("Vector navy contour", (0.035, 0.13, 0.22))
    cream = flat("Vector cream panel", (0.92, 0.91, 0.79))
    teal = flat("Vector leaf teal", (0.03, 0.63, 0.56))
    coral = flat("Vector flower coral", (0.95, 0.31, 0.31))
    gold = flat("Vector sun gold", (1.0, 0.67, 0.16))
    rect("Vector outer border", -2.48, -1.30, 2.48, 1.30, 1.05, navy)
    rect("SM_Vector_Icon_Panel", -2.40, -1.22, 2.40, 1.22, 1.0, cream)
    rect("Vector ground rule", -2.18, -0.92, 2.18, -0.885, 0.20, navy)
    disc("SM_Vector_Sun", 1.58, 0.53, 0.31, 0.17, gold)
    for index in range(8):
        angle = 2 * math.pi * index / 8
        radial = (math.cos(angle), math.sin(angle))
        tangent = (-radial[1], radial[0])
        ray_points = []
        for distance, width in ((0.39, -0.035), (0.53, -0.035),
                                (0.53, 0.035), (0.39, 0.035)):
            ray_points.append((1.58 + distance * radial[0] + width * tangent[0],
                               0.53 + distance * radial[1] + width * tangent[1]))
        polygon(f"Vector sun ray {index}", ray_points, 0.17, gold)

    # A fixed-origin rectangle grows upward from the seed line.
    stem_outline = rect("Vector stem outline", -0.54, -0.90, -0.35, 0.68, 0.08, navy)
    stem = rect("SM_Vector_Sprout_Stem", -0.51, -0.90, -0.38, 0.68, 0.04, teal)
    for obj in (stem_outline, stem):
        obj.data.transform(__import__("mathutils").Matrix.Translation((0, 0, 0.90)))
        obj.location.z = -0.90
        for frame, scale in ((1, 0.001), (12, 0.001), (36, 1), (72, 1)):
            obj.scale.z = scale
            obj.keyframe_insert(data_path="scale", frame=frame)
    disc("Vector seed", -0.445, -0.90, 0.11, -0.06, navy)

    for side, label in ((-1, "Left"), (1, "Right")):
        x = -0.445
        z = -0.12 if side < 0 else 0.13
        leaf_control = control(f"Vector {label.lower()} leaf control", (x, 0, z))
        edge = [(0, 0), (side * 0.24, 0.21), (side * 0.69, 0.28),
                (side * 0.85, 0.13), (side * 0.52, -0.04), (side * 0.13, -0.08)]
        inner = [(side * 0.07, 0.01), (side * 0.27, 0.17),
                 (side * 0.65, 0.20), (side * 0.74, 0.13),
                 (side * 0.48, 0.01), (side * 0.16, -0.02)]
        attach(polygon(f"Vector {label.lower()} contour", edge, 0.02, navy), leaf_control)
        attach(polygon(f"SM_Vector_{label}_Leaf", inner, -0.02, teal), leaf_control)
        for frame, scale in ((1, 0.001), (25, 0.001), (43, 1), (72, 1)):
            leaf_control.scale = (scale, scale, scale)
            leaf_control.keyframe_insert(data_path="scale", frame=frame)
        for frame, tilt in ((1, 0), (43, 0), (55, side * 0.09), (72, 0)):
            leaf_control.rotation_euler.y = tilt
            leaf_control.keyframe_insert(data_path="rotation_euler", frame=frame)

    bloom = control("Vector bloom control", (-0.445, 0, 0.51))
    for index in range(5):
        angle = 2 * math.pi * index / 5 + math.pi / 2
        x, z = 0.29 * math.cos(angle), 0.29 * math.sin(angle)
        petal = control(f"Vector petal {index} control", (x, 0, z))
        petal.parent = bloom
        petal.rotation_euler.y = math.pi / 2 - angle
        contour = attach(disc(f"Vector petal contour {index}", 0, 0, 0.23,
                              -0.02, navy, squash=(0.82, 1.08)), petal)
        fill = attach(disc(f"Vector coral petal {index}", 0, 0, 0.19,
                           -0.07, coral, squash=(0.82, 1.08)), petal)
        # Stagger the five flat paths so the bloom reads as a designed sequence.
        for frame, scale in ((1, 0.001), (42 + index * 2, 0.001),
                             (55 + index * 2, 1.07), (72, 1)):
            petal.scale = (scale, scale, scale)
            petal.keyframe_insert(data_path="scale", frame=frame)
        # Hide subpixel geometry until each petal is large enough to read as a shape.
        for obj in (contour, fill):
            for frame, hidden in ((1, True), (45 + index * 2, True),
                                  (46 + index * 2, False), (72, False)):
                obj.hide_render = hidden
                obj.keyframe_insert(data_path="hide_render", frame=frame)
    center = attach(disc("SM_Vector_Flower_Center", 0, 0, 0.18,
                         -0.12, gold), bloom)
    for frame, scale in ((1, 0.001), (40, 0.001), (59, 1.10), (72, 1)):
        bloom.scale = (scale, scale, scale)
        bloom.keyframe_insert(data_path="scale", frame=frame)

    camera("Vector front camera", (0, -5, 0), (0, 0, 0), ortho=5.55)
    scene["vector_recipe"] = "five emission-only flat fills, crisp 2D mesh paths, fixed front camera"
    return scene
