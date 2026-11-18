"""Original richer-palette 16-bit fox crossing a dithered waterfall scene."""

from pathlib import Path

import bpy

from common import camera, reset_scene


PALETTE = (
    (0.04, 0.06, 0.15), (0.08, 0.12, 0.27), (0.16, 0.20, 0.38),
    (0.25, 0.32, 0.52), (0.53, 0.46, 0.60), (0.95, 0.73, 0.53),
    (0.13, 0.25, 0.35), (0.23, 0.40, 0.44), (0.06, 0.25, 0.26),
    (0.11, 0.39, 0.30), (0.35, 0.28, 0.28), (0.55, 0.40, 0.29),
    (0.25, 0.55, 0.65), (0.55, 0.80, 0.78), (0.95, 0.43, 0.21),
    (0.98, 0.83, 0.57),
)
CELL = 0.055
FOX = (
    ".................E......",
    "................EEE.....",
    "...............EEEEE....",
    "......EE.......EEEEEE...",
    ".....EEEE......EEEEEEE..",
    "....EEEEEE....EEEEEEEE..",
    "...EEEEEEEEEEEEEEEEEEEE.",
    "..EEEEEEEEEEEEEEEEE0EFF.",
    ".EEEEEEEEEEEEEEEEEEEFFF.",
    "..EEEEEEEEEEEEEEEEEEFF..",
    "...EEEEEEEEFFFFFFFF.....",
    "....EEEEEEEEFFFFFF......",
    "......EEEEEEEEEE........",
    ".......EEE..EEE.........",
    ".......EE....EE.........",
    ".......EE....EE.........",
)


def flat(name, color, index):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*color, 1)
    mat.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = (*color, 1)
    mat["16bit_palette_index"] = index
    return mat


def backdrop_image():
    """Pack a 160x120 palette image with a two-color checker dithered horizon."""
    image = bpy.data.images.new("16bit dithered landscape", width=160, height=120, alpha=False)
    pixels = []
    for y in range(120):
        for x in range(160):
            top = 119 - y
            if top < 22:
                color = 2 if (x + top) % 8 else 3
            elif top < 45:
                color = 3 if (x + top) % 3 else 4
            elif top < 60:
                color = 4 if (x + top) % 2 else 5
            else:
                color = 5 if (x + top) % 3 else 4
            # Hard stepped mountains, two tree-depth bands, and a near-earth ledge.
            ridge1 = 63 + abs((x % 72) - 36) // 3
            ridge2 = 70 + abs((x % 45) - 22) // 3
            if top >= ridge1:
                color = 7
            if top >= ridge2:
                color = 6
            if top >= 85:
                color = 8 if (x // 5 + top // 3) % 5 else 9
            if 120 <= x <= 135 and 54 <= top < 102:
                color = 13 if (x + top) % 5 < 2 else 12
            if top >= 103:
                color = 10 if (x // 4 + top // 2) % 4 else 11
            pixels.extend((*PALETTE[color], 1))
    image.pixels[:] = pixels
    image.pack()
    return image


def landscape(image):
    mat = bpy.data.materials.new("16bit packed nearest landscape")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    emit = nodes.new("ShaderNodeEmission")
    mat.node_tree.links.new(tex.outputs["Color"], emit.inputs["Color"])
    mat.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mat["16bit_packed_texels"] = 160 * 120
    mesh = bpy.data.meshes.new("16bit backdrop plane")
    mesh.from_pydata([(-2.5, 1, -1.875), (2.5, 1, -1.875),
                      (2.5, 1, 1.875), (-2.5, 1, 1.875)],
                     [], [(0, 1, 2, 3)])
    mesh.update()
    uv = mesh.uv_layers.new(name="16bit pixel UV")
    for loop, value in zip(mesh.polygons[0].loop_indices,
                           ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[loop].uv = value
    obj = bpy.data.objects.new("SM_16bit_Dithered_Backdrop", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def sprite(name, rows, mats):
    width, height = len(rows[0]), len(rows)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root["16bit_sprite_grid"] = f"{width}x{height}"
    for ink in sorted({char for row in rows for char in row} - {"."}):
        index = int(ink, 16)
        verts, faces = [], []
        for row, line in enumerate(rows):
            if len(line) != width:
                raise ValueError("16-bit sprite rows require one width")
            for col, char in enumerate(line):
                if char != ink:
                    continue
                x = (col - width / 2) * CELL
                z = (height / 2 - row) * CELL
                start = len(verts)
                verts.extend(((x, 0, z), (x + CELL, 0, z),
                              (x + CELL, 0, z - CELL), (x, 0, z - CELL)))
                faces.append((start, start + 1, start + 2, start + 3))
        mesh = bpy.data.meshes.new(f"{name} color {ink} texels")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(f"{name} color {ink}", mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = root
        obj.location.y = -0.01 * index
        mesh.materials.append(mats[index])
        obj["16bit_pixel_faces"] = len(faces)
    return root


def key_location(obj, points):
    for frame, x, z in points:
        obj.location = (x, 0, z)
        obj.keyframe_insert(data_path="location", frame=frame)
    action = obj.animation_data.action
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves
    else:
        curves = action.fcurves
    for curve in curves:
        if curve.data_path == "location":
            for key in curve.keyframe_points:
                key.interpolation = "CONSTANT"


def make_scene(spec, spec_dir=Path(".")):
    if (spec.get("width"), spec.get("height"), spec.get("fps")) != (320, 240, 12):
        raise ValueError("The authored 16-bit raster is 320x240 at 12 fps")
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored 16-bit candidate")
    scene = reset_scene(spec, background=PALETTE[0])
    scene.view_settings.view_transform = "Standard"
    scene.render.filter_size = 0.01
    scene.render.dither_intensity = 0
    mats = [flat(f"16bit palette {i}", color, i) for i, color in enumerate(PALETTE)]
    landscape(backdrop_image())
    # Two held fox poses produce a sprite walk without smoothing its texel silhouette.
    fox_control = bpy.data.objects.new("16bit fox control", None)
    bpy.context.scene.collection.objects.link(fox_control)
    fox = sprite("SM_16bit_Fox", FOX, mats)
    fox.parent = fox_control
    alternate = tuple("........EE..EE.........." if row in (14, 15) else line
                      for row, line in enumerate(FOX))
    fox_alt = sprite("16bit fox alternate pose", alternate, mats)
    fox_alt.parent = fox_control
    for frame, x in ((1, -1.60), (9, -1.20), (17, -0.80), (25, -0.40),
                     (33, 0.00), (41, 0.40), (48, 0.75)):
        fox_control.location = (x, -0.1, -0.86)
        fox_control.keyframe_insert(data_path="location", frame=frame)
    action = fox_control.animation_data.action
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, fox_control.animation_data.action_slot).fcurves
    else:
        curves = action.fcurves
    for curve in curves:
        if curve.data_path == "location":
            for key in curve.keyframe_points:
                key.interpolation = "CONSTANT"
    for root, inverse in ((fox, False), (fox_alt, True)):
        for obj in (root, *root.children_recursive):
            for frame in range(1, 49):
                hidden = inverse if variant == 1 else ((frame // 4) % 2 == 1) != inverse
                obj.hide_render = hidden
                obj.keyframe_insert(data_path="hide_render", frame=frame)
    # Water glints descend in grid steps over the packed backdrop waterfall.
    water_rows = ("DD", "DD") if variant == 1 else ("DDDD", "DDDD")
    water = sprite("SM_16bit_Water_Highlight", water_rows, mats)
    for frame, z in ((1, 0.18), (9, -0.10), (17, -0.38),
                     (25, -0.66), (33, -0.94), (41, -1.22), (48, -1.48)):
        water.location = (1.47, 0, z)
        water.keyframe_insert(data_path="location", frame=frame)
    action = water.animation_data.action
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, water.animation_data.action_slot).fcurves
    else:
        curves = action.fcurves
    for curve in curves:
        if curve.data_path == "location":
            for key in curve.keyframe_points:
                key.interpolation = "CONSTANT"
    if variant == 2:
        for i, x in enumerate((1.32, 1.62)):
            glint = sprite(f"16bit second water glint {i}", ("DDD",), mats)
            key_location(glint, [(1, x, 0.08 - i * 0.32),
                                 (17, x, -0.32 - i * 0.32),
                                 (33, x, -0.72 - i * 0.32),
                                 (48, x, -1.12 - i * 0.32)])
    camera("16bit locked camera", (0, -5, 0), (0, 0, 0), ortho=5.0)
    scene["retro16_recipe"] = "packed 160x120 dithered landscape, 16 colors, nearest texels, held sprite walk"
    scene["retro16_variant"] = variant
    return scene
