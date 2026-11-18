"""Original 3D treasure chest with a locked pixel-art camera and palette."""

from pathlib import Path
import math

import bpy

from common import camera, cube, reset_scene


PALETTE = (
    (0.055, 0.050, 0.110),  # ink
    (0.165, 0.110, 0.200),  # deep violet
    (0.300, 0.155, 0.215),  # brown shadow
    (0.490, 0.225, 0.245),  # chest wood
    (0.675, 0.350, 0.240),  # wood light
    (0.825, 0.510, 0.245),  # gold shadow
    (0.950, 0.720, 0.370),  # gold
    (1.000, 0.895, 0.595),  # gold highlight
)


def flat_material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*color, 1)
    mat.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    mat.diffuse_color = (*color, 1)
    mat["palette_index"] = PALETTE.index(color)
    # Texture-only palette colors still belong to the editable color contract.
    mat.use_fake_user = True
    return mat


def packed_face(name, image_name, pattern):
    """Keep the complete 16×16 print inside the editable Blender file."""
    image = bpy.data.images.new(image_name, 16, 16, alpha=True)
    pixels = []
    for y in range(16):
        for x in range(16):
            pixels.extend((*PALETTE[pattern(x, y)], 1))
    image.pixels[:] = pixels
    image.pack()
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    mat.node_tree.links.new(tex.outputs["Color"], out.inputs["Surface"])
    mat["texel_size_px"] = 16
    return mat


def front_pattern(x, y):
    if x in (0, 15) or y in (0, 15):
        return 1
    if y in (3, 12) or x in (2, 13):
        return 5 if (x + y) % 4 else 6
    if 6 <= x <= 9 and 6 <= y <= 10:
        return 0 if y in (7, 8) else 6
    return 4 if (x // 3 + y // 2) % 3 == 0 else 3


def lid_pattern(x, y):
    if x in (0, 15) or y in (0, 15):
        return 1
    if y in (3, 11) or x in (2, 13):
        return 6
    return 4 if (x // 4 + y // 3) % 2 else 3


def vertical_plane(name, location, dimensions, mat):
    bpy.ops.mesh.primitive_plane_add(size=1, location=location,
                                     rotation=(math.pi / 2, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (dimensions[0], dimensions[1], 1)
    obj.data.materials.append(mat)
    return obj


def attach(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def stepped_keys(obj, data_path):
    """Hold positions between authored poses so motion follows the pixel grid."""
    action = obj.animation_data.action
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves
    else:
        curves = action.fcurves
    for curve in curves:
        if curve.data_path == data_path:
            for key in curve.keyframe_points:
                key.interpolation = "CONSTANT"


def make_scene(spec, spec_dir=Path(".")):
    if (spec.get("width"), spec.get("height"), spec.get("fps")) != (320, 240, 12):
        raise ValueError("The authored pixel shot uses a locked 320×240, 12 fps raster")
    scene = reset_scene(spec, background=PALETTE[1])
    scene.view_settings.view_transform = "Standard"
    scene.render.filter_size = 0.01
    scene.render.film_transparent = False
    mats = [flat_material(f"Pixel palette {i}", color)
            for i, color in enumerate(PALETTE)]
    wood = packed_face("Pixel chest front 16x16", "Pixel chest front print", front_pattern)
    lid_print = packed_face("Pixel lid face 16x16", "Pixel lid print", lid_pattern)

    # Flat geometric planes and a tiny fixed palette keep the blocky print legible.
    cube("Pixel distant stage", (0, 0.8, -0.18), (6.5, 4.0, 0.16), mats[1])
    cube("Pixel ground stripe", (0, -0.8, -0.10), (6.5, 0.22, 0.08), mats[2])
    cube("Pixel cast shadow", (0.08, -0.02, -0.085), (2.3, 1.25, 0.025), mats[0])
    for index, x in enumerate((-2.50, -1.97, 2.00, 2.55)):
        cube(f"Pixel floor tile {index}", (x, -0.73, -0.055),
             (0.40, 0.32, 0.025), mats[2])

    body = cube("SM_Pixel_Chest_Body", (0, 0, 0.41), (1.85, 0.85, 0.85), mats[2])
    body["closed_box_m"] = [1.85, 0.85, 0.85]
    vertical_plane("SM_Pixel_Chest_Front", (0, -0.431, 0.41),
                   (1.82, 0.82), wood)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0.935, 0, 0.41),
                                     rotation=(math.pi / 2, 0, math.pi / 2))
    side = bpy.context.object
    side.name = "Pixel printed chest side"
    side.scale = (0.82, 0.82, 1)
    side.data.materials.append(wood)
    cube("Pixel chest dark interior", (0, -0.01, 0.852),
         (1.68, 0.72, 0.03), mats[0])
    bpy.ops.object.empty_add(location=(0, 0.43, 0.84))
    hinge = bpy.context.object
    hinge.name = "Pixel lid hinge"
    lid = attach(cube("SM_Pixel_Chest_Lid", (0, 0, 0.95),
                      (1.93, 0.97, 0.25), mats[3]), hinge)
    attach(vertical_plane("Pixel printed lid front", (0, -0.49, 0.95),
                          (1.90, 0.23), lid_print), hinge)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 1.078))
    top = bpy.context.object
    top.name = "Pixel printed lid top"
    top.scale = (1.90, 0.94, 1)
    top.data.materials.append(lid_print)
    attach(top, hinge)
    # The underside enters frame as the lid opens, so print it at the same texel scale.
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.824))
    underside = bpy.context.object
    underside.name = "Pixel printed lid underside"
    underside.scale = (1.90, 0.94, 1)
    underside.data.materials.append(lid_print)
    attach(underside, hinge)
    # A lid lift and a revealed treasure square are the action, not a camera move.
    for frame, angle in ((1, 0), (12, 0), (24, -0.76), (34, -1.12), (48, -1.12)):
        hinge.rotation_euler.x = angle
        hinge.keyframe_insert(data_path="rotation_euler", frame=frame)
    treasure = cube("SM_Pixel_Treasure", (0, -0.01, 0.99),
                    (0.43, 0.10, 0.43), mats[6])
    attach(cube("Pixel treasure glint", (-0.08, -0.073, 1.09),
                (0.13, 0.025, 0.13), mats[7]), treasure)
    for frame, z in ((1, 0.72), (18, 0.72), (25, 1.05), (33, 1.30), (48, 1.35)):
        treasure.location.z = z
        treasure.keyframe_insert(data_path="location", frame=frame)
    stepped_keys(treasure, "location")
    for index, x in enumerate((-0.60, -0.35, 0.48, 0.68)):
        spark = cube(f"SM_Pixel_Spark_{index}", (x, -0.51, 0.94),
                     (0.10, 0.03, 0.10), mats[7 if index % 2 else 6])
        for frame, z in ((1, 0.84), (23, 0.84),
                         (30 + index * 2, 1.12 + index * 0.10),
                         (48, 1.43 + index * 0.10)):
            spark.location.z = z
            spark.keyframe_insert(data_path="location", frame=frame)
        stepped_keys(spark, "location")

    camera("Pixel locked camera", (1.8, -5.2, 2.5), (0, 0, 0.65), ortho=4.1)
    scene["pixel_palette_size"] = len(PALETTE)
    scene["pixel_raster_px"] = [320, 240]
    scene["pixel_style_rule"] = "16x16 packed nearest print, 8-color flat palette, fixed orthographic camera"
    return scene
