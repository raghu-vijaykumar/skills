"""Original storybook windmill island with exaggerated forms and painted albedo."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


PALETTE = {
    "sage": (0.28, 0.49, 0.32),
    "cream": (0.87, 0.76, 0.56),
    "terracotta": (0.68, 0.25, 0.16),
    "warm": (0.94, 0.58, 0.20),
}


def painted_roof():
    """Pack broad hand-authored color patches so the roof has no external texture."""
    image = bpy.data.images.new("Stylized painted roof albedo", 64, 64, alpha=True)
    pixels = []
    for y in range(64):
        for x in range(64):
            # Three broad brush-like bands vary the albedo without tiny surface geometry.
            band = int((y + 4 * math.sin(x * 0.18)) / 17)
            value = (0.84, 1.0, 0.91, 1.08)[max(0, min(3, band))]
            edge = 0.045 if x % 23 in (0, 1, 2) and y % 19 < 13 else 0
            pixels.extend((min(1, PALETTE["terracotta"][0] * value + edge),
                           PALETTE["terracotta"][1] * value + edge * 0.5,
                           PALETTE["terracotta"][2] * value, 1))
    image.pixels[:] = pixels
    image.pack()
    mat = material("Stylized painted terracotta", PALETTE["terracotta"], roughness=0.93)
    nodes = mat.node_tree.nodes
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    mat.node_tree.links.new(tex.outputs["Color"], nodes.get("Principled BSDF").inputs["Base Color"])
    mat["painted_albedo"] = True
    return mat


def keep_world_parent(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.70, 0.76, 0.70))
    scene["shape_language"] = "circle-friendly, square-stable, triangle-roof"
    scene["core_palette"] = "sage,cream,terracotta,warm"
    sage = material("Stylized sage grass", PALETTE["sage"], roughness=0.96)
    dark_sage = material("Stylized deep green", (0.14, 0.29, 0.20), roughness=0.94)
    cream = material("Stylized cream plaster", PALETTE["cream"], roughness=0.94)
    red = painted_roof()
    clay = material("Stylized clay island", (0.39, 0.27, 0.21), roughness=0.98)
    ink = material("Stylized doorway ink", (0.09, 0.17, 0.16), roughness=1)
    gold = material("Stylized warm window", PALETTE["warm"], roughness=0.9,
                    emission=PALETTE["warm"], emission_strength=0.1)
    window_mat = material("Stylized animated window", (0.09, 0.20, 0.18),
                          roughness=0.95, emission=PALETTE["warm"], emission_strength=0)
    wood = material("Stylized windmill timber", (0.65, 0.43, 0.25), roughness=0.96)

    # The floating island and overlarge roof define the silhouette before decoration.
    cylinder("SM_Stylized_Island", (0, 0, 0.05), 1.43, 0.32, clay,
             vertices=12, edge=0.10)
    cylinder("Stylized grass top", (0, 0, 0.22), 1.37, 0.10, sage,
             vertices=12, edge=0.04)
    body = cylinder("SM_Stylized_Cottage", (-0.32, 0.08, 0.72),
                    0.52, 0.9, cream, vertices=10, edge=0.07)
    body["body_radius_m"] = 0.52
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.94, radius2=0.09,
                                    depth=0.55, location=(-0.32, 0.08, 1.45))
    roof = bpy.context.object
    roof.name = "SM_Stylized_Painted_Roof"
    roof.data.materials.append(red)
    roof["roof_radius_m"] = 0.94
    cube("Stylized door", (-0.39, -0.49, 0.53),
         (0.29, 0.045, 0.47), ink, edge=0.10)
    sphere("Stylized door knob", (-0.29, -0.54, 0.52), 0.028, gold,
           segments=16, rings=8)
    window = sphere("SM_Stylized_Glow_Window", (-0.01, -0.52, 0.87),
                    0.12, window_mat, segments=24, rings=12, scale=(1, 0.25, 1))
    window["story_accent"] = True
    cylinder("Stylized window rim", (-0.01, -0.48, 0.87), 0.135, 0.03,
             wood, vertices=24, rotation=(math.pi / 2, 0, 0))

    # One front-mounted windmill gives the 72-frame shot a large readable action.
    bpy.ops.object.empty_add(location=(-0.32, -0.66, 1.09))
    pivot = bpy.context.object
    pivot.name = "Stylized windmill control"
    for index in range(4):
        angle = index * math.pi / 2
        blade = cube("SM_Stylized_Windmill" if index == 0 else
                     f"Stylized windmill blade {index}",
                     (-0.32 + 0.30 * math.sin(angle), -0.73,
                      1.09 + 0.30 * math.cos(angle)),
                     (0.13, 0.055, 0.60), gold if index == 0 else wood,
                     edge=0.045)
        # Offset each blade from the hub before parenting it to the spinning control.
        blade.rotation_euler.y = angle
        keep_world_parent(blade, pivot)
    keep_world_parent(sphere("Stylized windmill hub", (-0.32, -0.78, 1.09),
                             0.12, red, segments=16, rings=8), pivot)
    for frame, angle in ((1, 0), (36, 2.0), (72, 3.95)):
        pivot.rotation_euler.y = angle
        pivot.keyframe_insert(data_path="rotation_euler", frame=frame)
    window_bsdf = window_mat.node_tree.nodes.get("Principled BSDF")
    glow = window_bsdf.inputs["Emission Strength"]
    base = window_bsdf.inputs["Base Color"]
    for frame, value, color in ((1, 0, (0.09, 0.20, 0.18)),
                                (36, 1.5, PALETTE["warm"]),
                                (72, 2.5, PALETTE["warm"])):
        glow.default_value = value
        glow.keyframe_insert(data_path="default_value", frame=frame)
        base.default_value = (*color, 1)
        base.keyframe_insert(data_path="default_value", frame=frame)

    # Puffy foliage and a thin trunk deliberately exaggerate tree proportions.
    cylinder("Stylized tree trunk", (0.82, 0.35, 0.72), 0.07, 0.85,
             wood, vertices=8)
    canopy = sphere("SM_Stylized_Tree_Canopy", (0.82, 0.35, 1.30),
                    0.40, dark_sage, segments=20, rings=12,
                    scale=(1.10, 0.86, 0.96))
    canopy["trunk_radius_m"] = 0.07
    for location, radius in (((0.54, 0.36, 1.29), 0.28),
                             ((1.05, 0.39, 1.43), 0.30)):
        sphere("Stylized foliage puff", location, radius, sage,
               segments=20, rings=12)
    for x, y, r in ((-0.20, -0.91, 0.09), (0.02, -1.04, 0.08),
                    (0.22, -1.13, 0.07)):
        sphere("Stylized path stone", (x, y, 0.29), r, cream,
               segments=12, rings=8, scale=(1, 0.65, 0.25))

    camera("Stylized island camera", (2.9, -5.0, 2.7),
           (0, 0, 0.86), ortho=4.80)
    area_light("Stylized warm key", (-3, -4, 5), 900, 3,
               color=(1.0, 0.84, 0.69), target=(0, 0, 0.8))
    area_light("Stylized cool fill", (3, 1, 3), 320, 3,
               color=(0.65, 0.82, 1.0), target=(0, 0, 0.8))
    scene.render.use_freestyle = True
    scene.view_layers[0].freestyle_settings.linesets[0].linestyle.thickness = 1.5
    return scene
