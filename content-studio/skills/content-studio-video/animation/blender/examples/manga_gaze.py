"""Original monochrome manga eye panel with a sharp gaze shift and print cues."""

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


def ink_material(name, value):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (value, value, value, 1)
    mat.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    mat.diffuse_color = (value, value, value, 1)
    return mat


def screentone():
    """Pack sparse monochrome dots instead of importing a printed texture."""
    image = bpy.data.images.new("Manga packed screentone", 256, 256, alpha=True)
    pixels = []
    for y in range(256):
        for x in range(256):
            dx = (x + (y // 12) * 6) % 12 - 6
            dy = y % 12 - 6
            value = 0.30 if dx * dx + dy * dy < 5 else 0.90
            pixels.extend((value, value, value, 1))
    image.pixels[:] = pixels
    image.pack()
    mat = material("Manga screentone print", (0.9, 0.9, 0.9), roughness=1)
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    mat.node_tree.links.new(tex.outputs["Color"],
                            mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])
    mat["monochrome_print"] = True
    return mat


def stroke(name, points, radius, mat, parent=None):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    line = curve.splines.new("POLY")
    line.points.add(len(points) - 1)
    for point, loc in zip(line.points, points):
        point.co = (*loc, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.materials.append(mat)
    return attach(obj, parent) if parent else obj


def fringe(name, x, tip, mat, parent):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(x - 0.17, -0.49, 0.67),
                      (x + 0.17, -0.49, 0.67),
                      (x + 0.04, -0.49, tip)], [], [(0, 1, 2)])
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return attach(obj, parent)


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.93, 0.93, 0.93))
    paper = ink_material("Manga white paper", 0.94)
    ink = ink_material("Manga black ink", 0.015)
    gray = material("Manga face middle gray", (0.70, 0.70, 0.70), roughness=1)
    white = material("Manga eye white", (0.96, 0.96, 0.96), roughness=1)
    cube("Manga paper backdrop", (0, 1.6, 0), (5.1, 0.03, 2.85), paper)
    tone_mat = screentone()
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-1.64, 1.45, 0),
                                     rotation=(math.pi / 2, 0, 0))
    tone = bpy.context.object
    tone.name = "SM_Manga_Screentone"
    tone.scale = (1.65, 2.5, 1)
    tone.data.materials.append(tone_mat)

    # A close-up face makes the gaze change readable at the reduced GIF size.
    bpy.ops.object.empty_add(location=(0.62, 0, -0.03))
    face_control = bpy.context.object
    face_control.name = "Manga face control"
    face = attach(sphere("SM_Manga_Face", (0.62, 0, -0.03), 1.12,
                         gray, segments=36, rings=20,
                         scale=(0.91, 0.27, 1.05)), face_control)
    face["portrait_closeup"] = True
    attach(sphere("SM_Manga_Hair", (0.55, -0.08, 0.82), 0.96,
                  ink, segments=30, rings=14,
                  scale=(1.02, 0.30, 0.42)), face_control)
    for index, (x, tip) in enumerate(((0.00, 0.27), (0.35, 0.38),
                                      (0.70, 0.19), (1.05, 0.36))):
        fringe(f"Manga fringe {index}", x, tip, ink, face_control)
    eye = attach(sphere("SM_Manga_Eye_White", (0.49, -0.33, 0.10), 0.43,
                        white, segments=30, rings=14,
                        scale=(1.20, 0.18, 0.67)), face_control)
    eye["eye_width_m"] = eye.dimensions.x
    stroke("Manga upper lash", [(-0.04, -0.47, 0.28),
                                (0.25, -0.49, 0.39),
                                (0.54, -0.50, 0.40),
                                (0.89, -0.48, 0.29)], 0.026, ink, face_control)
    stroke("Manga lower lash", [(-0.02, -0.47, -0.08),
                                (0.25, -0.49, -0.20),
                                (0.58, -0.49, -0.19),
                                (0.88, -0.47, -0.05)], 0.012, ink, face_control)
    stroke("Manga lifted brow", [(0.04, -0.48, 0.54),
                                 (0.48, -0.50, 0.64),
                                 (0.90, -0.48, 0.52)], 0.038, ink, face_control)
    stroke("Manga nose cue", [(0.80, -0.42, -0.21),
                              (0.74, -0.46, -0.43),
                              (0.87, -0.44, -0.47)], 0.012, ink, face_control)
    stroke("Manga mouth cue", [(0.30, -0.43, -0.66),
                               (0.50, -0.46, -0.71),
                               (0.73, -0.42, -0.68)], 0.014, ink, face_control)

    bpy.ops.object.empty_add(location=(0.25, -0.47, 0.10))
    gaze = attach(bpy.context.object, face_control)
    gaze.name = "Manga gaze control"
    attach(sphere("SM_Manga_Iris", (0.25, -0.52, 0.10), 0.19,
                  ink, segments=24, rings=12,
                  scale=(0.78, 0.25, 1.10)), gaze)
    attach(sphere("Manga iris white glint", (0.20, -0.59, 0.18), 0.045,
                  white, segments=12, rings=8,
                  scale=(1, 0.35, 1)), gaze)
    for frame, x, size, tilt in ((1, 0.19, 0.83, -0.025),
                                 (24, 0.19, 0.83, -0.025),
                                 (36, 0.63, 1.30, 0.03),
                                 (52, 0.55, 1.18, 0.02),
                                 (72, 0.50, 1.0, 0.01)):
        gaze.location.x = x - 0.62
        gaze.scale = (size, size, size)
        face_control.rotation_euler.z = tilt
        gaze.keyframe_insert(data_path="location", frame=frame)
        gaze.keyframe_insert(data_path="scale", frame=frame)
        face_control.keyframe_insert(data_path="rotation_euler", frame=frame)

    # Sparse action strokes and one ink glyph appear only after the gaze snaps.
    for index in range(7):
        z = -0.93 + index * 0.30
        line = stroke(f"Manga emphasis line {index}",
                      [(-2.30, 0.85, z), (-0.48 + index * 0.03, 0.85, z + 0.12)],
                      0.011 if index % 2 else 0.018, ink)
        line.hide_render = True
        line.keyframe_insert(data_path="hide_render", frame=1)
        line.keyframe_insert(data_path="hide_render", frame=27)
        line.hide_render = False
        line.keyframe_insert(data_path="hide_render", frame=34)
    glyph = bpy.data.curves.new("Manga emphasis glyph", "FONT")
    glyph.body = "!"
    glyph.size = 0.77
    glyph.fill_mode = "BOTH"
    emphasis = bpy.data.objects.new("SM_Manga_Exclamation", glyph)
    scene.collection.objects.link(emphasis)
    emphasis.location = (-1.45, -0.8, 0.55)
    emphasis.rotation_euler = (math.pi / 2, 0, 0)
    glyph.materials.append(ink)
    emphasis.hide_render = True
    emphasis.keyframe_insert(data_path="hide_render", frame=1)
    emphasis.keyframe_insert(data_path="hide_render", frame=27)
    emphasis.hide_render = False
    emphasis.keyframe_insert(data_path="hide_render", frame=34)
    for x in (-2.38, 2.38):
        cube("Manga panel vertical border", (x, -0.9, 0),
             (0.045, 0.04, 2.56), ink)
    for z in (-1.27, 1.27):
        cube("Manga panel horizontal border", (0, -0.9, z),
             (4.80, 0.04, 0.045), ink)

    # Crop the face at the right panel edge so the single eye reads as a close-up.
    face_control.location.x = 1.50
    face_control.scale = (1.40, 1, 1.40)
    camera("Manga panel camera", (0, -5.5, 0.05),
           (0, 0, 0), ortho=5.05)
    area_light("Manga graphic key", (-2, -3, 4), 700, 2.3,
               target=(0, 0, 0))
    scene.render.use_freestyle = True
    scene.view_layers[0].freestyle_settings.linesets[0].linestyle.thickness = 2.1
    scene["manga_value_language"] = "grayscale, sparse screentone, black fringe, emphasis lines"
    return scene
