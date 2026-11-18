"""Pixel lantern carrier crossing an original painted 3D bridge stage."""

from pathlib import Path
import math

import bpy
from mathutils import Vector

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


PIXEL = 0.052
SPRITE_COLORS = (
    (0.032, 0.048, 0.085),  # ink
    (0.88, 0.63, 0.43),     # face
    (0.11, 0.43, 0.46),     # cloak
    (0.35, 0.70, 0.65),     # cloak highlight
    (1.00, 0.72, 0.24),     # lantern gold
    (0.21, 0.14, 0.13),     # boots
)


def emission(name, color, strength=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    node = nodes.new("ShaderNodeEmission")
    node.inputs["Color"].default_value = (*color, 1)
    node.inputs["Strength"].default_value = strength
    mat.node_tree.links.new(node.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = (*color, 1)
    mat["hd2d_pixel_fill"] = True
    return mat


def sprite_pixels(pose, detailed=False):
    """The alternate boot cells form a held two-pose walk without smoothing texels."""
    data = {}
    def fill(x0, x1, y0, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                data[x, y] = color
    fill(7, 12, 2, 10, 0)
    fill(8, 11, 4, 9, 1)
    fill(6, 13, 2, 3, 0)
    fill(5, 14, 4, 4, 0)
    fill(6, 13, 10, 21, 0)
    fill(7, 12, 11, 20, 2)
    fill(8, 10, 12, 19, 3)
    fill(4, 6, 12, 18, 0)
    fill(5, 5, 13, 17, 2)
    fill(2, 5, 17, 22, 0)
    fill(3, 4, 18, 21, 4)
    fill(3, 4, 23, 23, 4)
    if detailed:
        # One eye, a hat band, and cloak hem are readable at the full-shot size.
        data[10, 6] = 0
        fill(7, 12, 3, 3, 4)
        fill(8, 11, 19, 19, 4)
        data[3, 17] = 4
    if pose == 0:
        fill(7, 9, 21, 25, 5)
        fill(11, 13, 21, 25, 5)
    else:
        fill(6, 8, 21, 24, 5)
        fill(12, 14, 21, 25, 5)
    return data


def pixel_actor(name, pose, mats, detailed=False):
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root["sprite_grid"] = "18x26"
    root["sprite_pose"] = pose
    pattern = sprite_pixels(pose, detailed)
    for color, mat in enumerate(mats):
        verts, faces = [], []
        for (x, row), ink in pattern.items():
            if ink != color:
                continue
            x0, z0 = (x - 9) * PIXEL, (26 - row) * PIXEL
            start = len(verts)
            verts.extend(((x0, 0, z0), (x0 + PIXEL, 0, z0),
                          (x0 + PIXEL, 0, z0 - PIXEL), (x0, 0, z0 - PIXEL)))
            faces.append((start, start + 1, start + 2, start + 3))
        if not faces:
            continue
        mesh = bpy.data.meshes.new(f"{name} pixel color {color}")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        child = bpy.data.objects.new(f"{name} color {color}", mesh)
        bpy.context.scene.collection.objects.link(child)
        child.parent = root
        child.location.y = -0.002 * color
        child.data.materials.append(mat)
        child["sprite_pixel_faces"] = len(faces)
    return root


def painted_deck():
    """Pack a mottled albedo rather than depending on an external texture file."""
    image = bpy.data.images.new("HD2D hand-painted bridge albedo", 128, 64, alpha=True)
    pixels = []
    for y in range(64):
        for x in range(128):
            brush = math.sin(x * 0.11) * math.cos(y * 0.14)
            grain = math.sin((x * 17 + y * 31) * 0.19)
            moss = max(0, brush * 0.5 + grain * 0.24)
            pixels.extend((0.23 + moss * 0.11, 0.30 + moss * 0.18,
                           0.27 + moss * 0.08, 1))
    image.pixels[:] = pixels
    image.pack()
    mat = bpy.data.materials.new("HD2D painted stone deck")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.95
    mat["packed_painted_deck"] = True
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0.39))
    obj = bpy.context.object
    obj.name = "SM_HD2D_Painted_Deck"
    obj.scale = (2.55, 0.67, 1)
    obj.data.materials.append(mat)
    return obj


def set_held(obj):
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
    variant = spec.get("variant", 2)
    if variant not in (1, 2, 3):
        raise ValueError("Unknown HD-2D candidate")
    scene = reset_scene(spec, background=(0.11, 0.18, 0.22))
    scene.view_settings.view_transform = "AgX"
    scene.render.film_transparent = False
    stone = material("HD2D softened slate", (0.25, 0.35, 0.34), roughness=0.87)
    edge = material("HD2D stone rim", (0.37, 0.39, 0.30), roughness=0.86)
    moss = material("HD2D moss bank", (0.17, 0.32, 0.25), roughness=0.98)
    water_mat = material("HD2D teal stream", (0.10, 0.42, 0.47), metallic=0.1,
                         roughness=0.31)
    bark = material("HD2D pine bark", (0.17, 0.23, 0.19), roughness=0.95)
    leaves = material("HD2D painted foliage", (0.18, 0.36, 0.29), roughness=0.97)
    warm = material("HD2D lantern glass", (1.0, 0.61, 0.16), roughness=0.3,
                    emission=(1.0, 0.51, 0.12), emission_strength=3.0)
    cube("SM_HD2D_Stream", (0, 0, -0.64), (3.35, 11, 0.10), water_mat)
    for side in (-1, 1):
        cube(f"HD2D bank {side}", (side * 2.43, 0, -0.56),
             (1.9, 11, 0.24), moss)
        for index, y in enumerate((1.5, 3.0, 4.2)):
            x = side * (2.0 + 0.25 * (index % 2))
            cylinder(f"HD2D pine trunk {side} {index}", (x, y, 0.28),
                     0.11, 1.75, bark, vertices=10)
            sphere(f"HD2D pine crown {side} {index}", (x, y, 1.34),
                   0.67, leaves, segments=10, rings=6, scale=(0.70, 0.70, 1.28))
    bridge = cube("SM_HD2D_Stone_Bridge", (0, 0, 0.20),
                  (5.15, 1.36, 0.36), stone, edge=0.07)
    bridge["bridge_span_m"] = 5.15
    painted_deck()
    for i in range(8):
        x = -2.21 + i * 0.63
        cube(f"HD2D stone joint {i}", (x, -0.69, 0.21),
             (0.045, 0.08, 0.31), edge)
        cube(f"HD2D parapet block {i}", (x, 0.68, 0.44),
             (0.56, 0.18, 0.42), stone, edge=0.028)
    for side in (-1, 1):
        x = side * 2.30
        post = cube(f"HD2D lantern post {side}", (x, -0.59, 0.95),
                    (0.19, 0.19, 1.24), edge, edge=0.025)
        lamp = cube("SM_HD2D_Bridge_Lantern" if side > 0 else "HD2D far lantern",
                    (x, -0.59, 1.64), (0.30, 0.30, 0.35), warm, edge=0.04)
        lamp["lantern_side"] = side
        area_light(f"HD2D warm key {side}", (x, -0.2, 2.55),
                   (390 if side > 0 else 260) if variant == 3 else
                   (300 if side > 0 else 210), 2.8,
                   color=(1.0, 0.53, 0.23) if variant == 3 else (1.0, 0.63, 0.31),
                   target=(x * 0.55, 0, 0.4))
    area_light("HD2D cool forest fill", (0, 2.9, 4.7), 280, 5.4,
               color=(0.45, 0.76, 1.0), target=(0, 0, 0.4))
    # The sprite billboard and the physically shaded bridge remain separate assets.
    sprite_mats = [emission(f"HD2D sprite ink {i}", color,
                            1.8 if variant == 3 and i == 4 else 1.0)
                   for i, color in enumerate(SPRITE_COLORS)]
    control = bpy.data.objects.new("HD2D traveler control", None)
    bpy.context.scene.collection.objects.link(control)
    actors = (pixel_actor("SM_HD2D_Pixel_Traveler", 0, sprite_mats,
                          detailed=variant == 3),
              pixel_actor("HD2D traveler alternate", 1, sprite_mats,
                          detailed=variant == 3))
    for actor in actors:
        actor.parent = control
    for frame, x in ((1, -1.90), (13, -1.35), (25, -0.75),
                     (37, -0.15), (49, 0.40), (61, 0.75), (72, 1.00)):
        control.location = (x, -0.10, 0.39)
        control.keyframe_insert(data_path="location", frame=frame)
    set_held(control)
    for actor, inverse in ((actors[0], False), (actors[1], True)):
        for obj in (actor, *actor.children_recursive):
            for frame in range(1, 73):
                hidden = inverse if variant == 1 else ((frame // 6) % 2 == 1) != inverse
                obj.hide_render = hidden
                obj.keyframe_insert(data_path="hide_render", frame=frame)
    cam = camera("HD2D tilted camera", (5.5, -8.0, 5.0), (0, 0.4, 0.65), ortho=7.8)
    facing = (cam.location - Vector((0, 0, 0.5))).normalized()
    for actor in actors:
        actor.rotation_euler = facing.to_track_quat("-Y", "Z").to_euler()
    focus = bpy.data.objects.new("HD2D stage focus", None)
    bpy.context.scene.collection.objects.link(focus)
    focus.location = (0, 0, 0.85)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = focus
    cam.data.dof.aperture_fstop = 3.2
    if variant >= 2:
        # A few foreground reeds and ripples add depth while leaving the hero clear.
        reed = material("HD2D near reed", (0.18, 0.40, 0.27), roughness=0.9)
        for i, x in enumerate((-2.8, -2.5, 2.45, 2.78)):
            cylinder(f"HD2D near reed {i}", (x, -2.20, -0.12), 0.045,
                     0.75 + (i % 2) * 0.18, reed, vertices=6,
                     rotation=(0, 0.12 * (-1 if i % 2 else 1), 0))
        ripple_mat = material("HD2D soft water glint", (0.38, 0.70, 0.70),
                              roughness=0.4, emission=(0.14, 0.38, 0.40),
                              emission_strength=0.35)
        for i, y in enumerate((-1.60, 1.95)):
            ring = bpy.data.curves.new(f"HD2D ripple curve {i}", "CURVE")
            ring.dimensions = "3D"
            ring.bevel_depth = 0.012
            ring.bevel_resolution = 1
            spline = ring.splines.new("POLY")
            spline.points.add(15)
            for j, point in enumerate(spline.points):
                angle = 2 * math.pi * j / 16
                point.co = (0.31 * math.cos(angle), 0.16 * math.sin(angle), 0, 1)
            spline.use_cyclic_u = True
            obj = bpy.data.objects.new(f"HD2D water ripple {i}", ring)
            bpy.context.scene.collection.objects.link(obj)
            obj.location = (0.1 if i else -0.35, y, -0.57)
            ring.materials.append(ripple_mat)
            for frame, scale in ((1, 0.55), (38, 1.0), (72, 1.32)):
                obj.scale = (scale, scale, 1)
                obj.keyframe_insert(data_path="scale", frame=frame)
    scene["hd2d_recipe"] = "pixel billboard on painted 3D bridge, tilted orthographic camera, warm keys, depth of field"
    scene["hd2d_variant"] = variant
    return scene
