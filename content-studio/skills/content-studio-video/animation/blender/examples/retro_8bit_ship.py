"""Original four-color arcade ship shot with grid-aligned sprite motion."""

from pathlib import Path

import bpy

from common import camera, reset_scene


PALETTE = ((0.04, 0.06, 0.18), (0.96, 0.92, 0.72),
           (0.17, 0.79, 0.48), (1.00, 0.43, 0.25))
CELL = 0.07
SHIP = (
    "......11........",
    ".....1221.......",
    "111112222111....",
    "12222222222211..",
    "1222223333222211",
    "1222223333222211",
    "111112222111....",
    ".....1221.......",
    "......11........",
)
ASTEROID = (
    "...11111...",
    "..1333331..",
    ".133113331.",
    "13333333331",
    "13331133331",
    "13333333331",
    "13333333331",
    ".133331331.",
    "..1333331..",
    "...11111...",
)
FRAGMENT = ("11", "13", "33")


def flat(name, color, index):
    """A fixed emission palette has no gradient or lighting-dependent colors."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*color, 1)
    mat.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = (*color, 1)
    mat["8bit_palette_index"] = index
    return mat


def sprite(name, rows, mats):
    """Merge each color's square pixels into one editable planar mesh."""
    width, height = len(rows[0]), len(rows)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root["sprite_grid"] = f"{width}x{height}"
    root["pixel_cell"] = CELL
    for color in range(1, 4):
        verts, faces = [], []
        for row, line in enumerate(rows):
            if len(line) != width:
                raise ValueError("Every sprite row must use one grid width")
            for column, ink in enumerate(line):
                if ink != str(color):
                    continue
                x = (column - width / 2) * CELL
                z = (height / 2 - row) * CELL
                start = len(verts)
                verts.extend(((x, 0, z), (x + CELL, 0, z),
                              (x + CELL, 0, z - CELL), (x, 0, z - CELL)))
                faces.append((start, start + 1, start + 2, start + 3))
        if not faces:
            continue
        mesh = bpy.data.meshes.new(f"{name} color {color} square pixels")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        part = bpy.data.objects.new(f"{name} color {color}", mesh)
        bpy.context.scene.collection.objects.link(part)
        part.parent = root
        part.location.y = -0.01 * color
        part.data.materials.append(mats[color])
        part["sprite_pixel_count"] = len(faces)
    return root


def stepped(obj, data_path):
    """Held keyframes keep sprite travel on authored pixel positions."""
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


def key_location(obj, frames):
    for frame, x, z in frames:
        obj.location = (x, 0, z)
        obj.keyframe_insert(data_path="location", frame=frame)
    stepped(obj, "location")


def key_visibility(obj, frames):
    # Empty visibility does not hide child mesh pixels in Blender renders.
    for target in (obj, *obj.children_recursive):
        for frame, hidden in frames:
            target.hide_render = hidden
            target.keyframe_insert(data_path="hide_render", frame=frame)


def make_scene(spec, spec_dir=Path(".")):
    if (spec.get("width"), spec.get("height"), spec.get("fps")) != (320, 240, 12):
        raise ValueError("The 8-bit raster must stay at 320x240 and 12 fps")
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored 8-bit candidate")
    scene = reset_scene(spec, background=PALETTE[0])
    scene.view_settings.view_transform = "Standard"
    scene.render.filter_size = 0.01
    scene.render.dither_intensity = 0.0
    mats = [flat(f"8bit palette {i}", color, i)
            for i, color in enumerate(PALETTE)]
    # An emission plane makes the backdrop exactly one palette color in every pixel.
    mesh = bpy.data.meshes.new("8bit flat backdrop mesh")
    mesh.from_pydata([(-4, 1, -3), (4, 1, -3), (4, 1, 3), (-4, 1, 3)],
                     [], [(0, 1, 2, 3)])
    mesh.update()
    backdrop = bpy.data.objects.new("8bit flat backdrop", mesh)
    bpy.context.scene.collection.objects.link(backdrop)
    backdrop.data.materials.append(mats[0])
    ship = sprite("SM_8bit_Ship", SHIP, mats)
    ship.name = "SM_8bit_Ship"
    ship_ctrl = bpy.data.objects.new("8bit ship control", None)
    bpy.context.scene.collection.objects.link(ship_ctrl)
    ship.parent = ship_ctrl
    key_location(ship_ctrl, [(1, -1.82, -0.16), (9, -1.68, -0.16),
                             (17, -1.54, -0.16), (48, -1.54, -0.16)])
    asteroid = sprite("SM_8bit_Asteroid", ASTEROID, mats)
    asteroid.location = (1.40, 0, -0.05)
    key_visibility(asteroid, [(1, False), (30, False), (31, True), (48, True)])
    bullet = sprite("SM_8bit_Projectile", ("22", "22"), mats)
    key_location(bullet, [(1, -0.80, -0.16), (18, -0.80, -0.16),
                          (21, -0.38, -0.16), (24, 0.04, -0.16),
                          (27, 0.46, -0.16), (30, 0.88, -0.16),
                          (48, 0.88, -0.16)])
    key_visibility(bullet, [(1, True), (17, True), (18, False),
                            (30, False), (31, True), (48, True)])
    offsets = ((-0.34, 0.23), (0.34, 0.23),
               (-0.34, -0.23), (0.34, -0.23))
    for i, (dx, dz) in enumerate(offsets):
        part = sprite(f"SM_8bit_Fragment_{i}", FRAGMENT, mats)
        origin_x, origin_z = 1.40 + dx, -0.05 + dz
        movement = 0.18 if variant == 1 else 0.48
        key_location(part, [(1, origin_x, origin_z), (31, origin_x, origin_z),
                            (39, origin_x + (1 if dx > 0 else -1) * movement * 0.5,
                             origin_z + (1 if dz > 0 else -1) * movement * 0.5),
                            (48, origin_x + (1 if dx > 0 else -1) * movement,
                             origin_z + (1 if dz > 0 else -1) * movement)])
        key_visibility(part, [(1, True), (30, True), (31, False), (48, False)])
    # A sparse starfield and HUD ticks retain severe four-color arcade limits.
    for i, (x, z) in enumerate(((-2.8, 1.7), (-1.3, 1.1), (0.2, 1.65),
                                 (1.9, 1.3), (2.7, 0.65), (-2.4, -1.4),
                                 (0.25, -1.55), (2.3, -1.35))):
        star = sprite(f"8bit star {i}", ("1",), mats)
        star.location = (x, 0, z)
    camera("8bit locked camera", (0, -5, 0), (0, 0, 0), ortho=5.0)
    scene["retro_recipe"] = "four emission colors, grid square sprites, held motion, fixed low raster"
    scene["retro_variant"] = variant
    return scene
