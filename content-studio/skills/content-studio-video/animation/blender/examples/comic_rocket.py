"""Original comic-book rocket panel with halftone, contours and speed cues."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def attach(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def halftone_material():
    """Pack coarse Ben-Day-inspired dots so the scene has no external image file."""
    image = bpy.data.images.new("Comic blue halftone print", 256, 256, alpha=True)
    pixels = []
    for y in range(256):
        for x in range(256):
            dx = (x + (y // 14) * 7) % 14 - 7
            dy = y % 14 - 7
            dot = dx * dx + dy * dy < 6
            color = (0.40, 0.62, 0.68) if dot else (0.71, 0.84, 0.84)
            pixels.extend((*color, 1))
    image.pixels[:] = pixels
    image.pack()
    mat = material("Comic packed halftone", (0.71, 0.84, 0.84), roughness=1)
    nodes = mat.node_tree.nodes
    image_node = nodes.new("ShaderNodeTexImage")
    image_node.image = image
    image_node.interpolation = "Closest"
    mat.node_tree.links.new(image_node.outputs["Color"],
                            nodes.get("Principled BSDF").inputs["Base Color"])
    mat["print_dots"] = 256
    return mat


def stroke(name, start, end, radius, ink):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (*start, 1)
    spline.points[1].co = (*end, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.materials.append(ink)
    return obj


def burst_mesh(mat):
    vertices = [(0, 0.8, 0.08)]
    for index in range(24):
        angle = 2 * math.pi * index / 24
        radius = 0.55 if index % 2 else 1.04
        vertices.append((radius * math.cos(angle), 0.8,
                         0.08 + radius * math.sin(angle)))
    faces = [(0, index + 1, (index + 1) % 24 + 1) for index in range(24)]
    mesh = bpy.data.meshes.new("Comic impact burst triangles")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new("SM_Comic_Impact_Burst", mesh)
    bpy.context.scene.collection.objects.link(obj)
    # Hide the tiny anticipation scale so no stray ink dot appears before impact.
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=1)
    obj.keyframe_insert(data_path="hide_render", frame=28)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=32)
    obj.keyframe_insert(data_path="hide_render", frame=72)
    obj.scale = (0.01, 0.01, 0.01)
    obj.keyframe_insert(data_path="scale", frame=1)
    obj.keyframe_insert(data_path="scale", frame=28)
    obj.scale = (1, 1, 1)
    obj.keyframe_insert(data_path="scale", frame=40)
    obj.scale = (0.76, 0.76, 0.76)
    obj.keyframe_insert(data_path="scale", frame=72)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.60, 0.75, 0.77))
    cream = material("Comic rocket cream", (0.93, 0.85, 0.60), roughness=0.91)
    red = material("Comic punch red", (0.80, 0.12, 0.08), roughness=0.92)
    blue = material("Comic ink blue", (0.025, 0.11, 0.19), roughness=0.97,
                    emission=(0.025, 0.11, 0.19), emission_strength=0.35)
    glass = material("Comic window cyan", (0.20, 0.67, 0.73), roughness=0.9)
    yellow = material("Comic impact yellow", (1.0, 0.68, 0.08), roughness=1)
    flame_mat = material("Comic flame yellow", (1.0, 0.51, 0.04), roughness=1,
                         emission=(1, 0.36, 0.02), emission_strength=0.8)
    print_mat = halftone_material()
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 1.5, 0),
                                     rotation=(math.pi / 2, 0, 0))
    print_plane = bpy.context.object
    print_plane.name = "SM_Comic_Halftone_Backdrop"
    print_plane.scale = (5.0, 2.8, 1)
    print_plane.data.materials.append(print_mat)
    burst_mesh(yellow)

    # The rocket is one editable moving hero; the print and border stay fixed.
    bpy.ops.object.empty_add(location=(-1.28, 0, -0.24))
    root = bpy.context.object
    root.name = "Comic rocket control"
    body = cylinder("SM_Comic_Rocket_Body", (-1.28, 0, -0.24),
                    0.22, 0.98, cream, vertices=16, edge=0.03)
    attach(body, root)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.23, radius2=0.015,
                                    depth=0.42, location=(-1.28, 0, 0.45))
    nose = bpy.context.object
    nose.name = "SM_Comic_Rocket_Nose"
    nose.data.materials.append(red)
    attach(nose, root)
    window = sphere("SM_Comic_Rocket_Window", (-1.28, -0.225, -0.01),
                    0.125, glass, segments=24, rings=12,
                    scale=(1, 0.24, 1))
    attach(window, root)
    for side in (-1, 1):
        fin = cube(f"Comic rocket fin {side}",
                   (-1.28 + side * 0.24, 0, -0.54),
                   (0.24, 0.07, 0.28), red, edge=0.025)
        fin.rotation_euler.y = side * 0.23
        attach(fin, root)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.145, radius2=0.01,
                                    depth=0.43, location=(-1.28, 0, -0.93),
                                    rotation=(math.pi, 0, 0))
    flame = bpy.context.object
    flame.name = "SM_Comic_Flame"
    flame.data.materials.append(flame_mat)
    attach(flame, root)
    for frame, x, z, flame_z in ((1, -1.28, -0.24, 0.55),
                                 (24, -0.52, -0.12, 1.0),
                                 (36, 0.10, 0.02, 1.30),
                                 (52, 0.82, 0.20, 1.10),
                                 (72, 1.18, 0.27, 0.62)):
        root.location = (x, 0, z)
        root.rotation_euler.y = 0.22
        root.keyframe_insert(data_path="location", frame=frame)
        root.keyframe_insert(data_path="rotation_euler", frame=frame)
        flame.scale.z = flame_z
        flame.keyframe_insert(data_path="scale", frame=frame)

    # Static converging strokes retain a printed-panel read behind the moving rocket.
    for index in range(6):
        z = -0.92 + index * 0.22
        stroke(f"Comic speed line {index}", (-2.25, 0.68, z),
               (-0.85 + index * 0.08, 0.68, z + 0.12),
               0.012 if index % 2 else 0.019, blue)
    text_curve = bpy.data.curves.new("Comic WHOOSH letters", "FONT")
    text_curve.body = "WHOOSH!"
    text_curve.size = 0.31
    text_curve.shear = 0.20
    text_curve.fill_mode = "BOTH"
    text_curve.extrude = 0.016
    lettering = bpy.data.objects.new("SM_Comic_Whoosh_Lettering", text_curve)
    scene.collection.objects.link(lettering)
    lettering.location = (-0.95, -0.55, -0.88)
    lettering.rotation_euler = (math.pi / 2, 0, 0)
    # Emissive ink keeps the printed letters dark regardless of the key light.
    letter_ink = bpy.data.materials.new("Comic pure ink lettering")
    letter_ink.use_nodes = True
    nodes = letter_ink.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.008, 0.03, 0.05, 1)
    letter_ink.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    text_curve.materials.append(letter_ink)
    lettering.hide_render = True
    lettering.keyframe_insert(data_path="hide_render", frame=1)
    lettering.keyframe_insert(data_path="hide_render", frame=31)
    lettering.hide_render = False
    lettering.keyframe_insert(data_path="hide_render", frame=36)
    lettering.keyframe_insert(data_path="hide_render", frame=72)
    for x in (-2.34, 2.34):
        cube("Comic panel vertical ink", (x, -0.85, 0),
             (0.06, 0.06, 2.48), blue)
    for z in (-1.24, 1.24):
        cube("Comic panel horizontal ink", (0, -0.85, z),
             (4.72, 0.06, 0.06), blue)

    camera("Comic panel camera", (0, -6.2, 0.18),
           (0, 0, 0.12), ortho=5.05)
    area_light("Comic hard key", (-2, -3, 4), 850, 0.7,
               target=(0, 0, 0))
    scene.render.use_freestyle = True
    scene.view_layers[0].freestyle_settings.linesets[0].linestyle.thickness = 2.4
    scene["comic_print_language"] = "ink contour, packed halftone, speed lines, impact burst"
    return scene
