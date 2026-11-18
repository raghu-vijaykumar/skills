"""Measured studio interior with a level walkthrough camera and window light."""

from pathlib import Path

import bpy
from mathutils import Vector

from common import area_light, camera, cube, cylinder, look_at, material, reset_scene, sphere


def collection(name):
    group = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(group)
    return group


def assign(obj, group):
    for prior in tuple(obj.users_collection):
        prior.objects.unlink(obj)
    group.objects.link(obj)
    return obj


def box(group, name, at, size, mat, bevel=0):
    return assign(cube(name, at, size, mat, edge=bevel), group)


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown archviz variant")
    scene = reset_scene(spec, background=(0.20, 0.26, 0.33))
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.32
    scene.view_settings.exposure = -0.45 if variant == 2 else 0.0
    architecture = collection("COL_Architecture")
    furniture = collection("COL_Furniture")
    lighting = collection("COL_Lighting")
    context = collection("COL_Context")

    clay = material("MAT_Archviz_Greybox", (0.48, 0.49, 0.48), roughness=0.82)
    plaster = material("MAT_Plaster_Warm", (0.50, 0.48, 0.44), roughness=0.88)
    ceiling = material("MAT_Ceiling_White", (0.62, 0.63, 0.59), roughness=0.90)
    oak = material("MAT_Oak_Floor", (0.24, 0.13, 0.065), roughness=0.57)
    oak_alt = material("MAT_Oak_Floor_Alt", (0.29, 0.17, 0.08), roughness=0.57)
    walnut = material("MAT_Walnut_Furniture", (0.19, 0.11, 0.055), roughness=0.46)
    linen = material("MAT_Linen_Sofa", (0.38, 0.35, 0.30), roughness=0.91)
    accent = material("MAT_Muted_Teal", (0.095, 0.25, 0.28), roughness=0.84)
    rug = material("MAT_Woven_Rug", (0.22, 0.30, 0.28), roughness=0.94)
    brass = material("MAT_Brushed_Brass", (0.53, 0.37, 0.16), metallic=0.78,
                     roughness=0.42)
    glass = material("MAT_Window_Sky", (0.25, 0.44, 0.57), roughness=0.18,
                     emission=(0.35, 0.57, 0.70), emission_strength=0.35)
    ink = material("MAT_Wall_Art", (0.13, 0.17, 0.20), roughness=0.80)
    art = material("MAT_Wall_Art_Terra", (0.42, 0.18, 0.10), roughness=0.91)
    distant = material("MAT_Exterior_Distant", (0.24, 0.39, 0.45), roughness=0.88,
                       emission=(0.25, 0.40, 0.46), emission_strength=0.14)
    warm = material("MAT_Pendant_Diffuser", (0.9, 0.62, 0.30), roughness=0.45,
                    emission=(1.0, 0.61, 0.25), emission_strength=0.65)
    finish = variant == 2
    wall_mat = plaster if finish else clay
    floor_mat = oak if finish else clay

    # Physical dimensions remain explicit so camera and asset reviews can audit scale.
    scene["archviz_room_m"] = [5.6, 5.6, 3.0]
    box(architecture, "SM_Studio_Floor", (0, 0, -0.06), (5.6, 5.6, 0.12), floor_mat)
    if finish:
        for i in range(14):
            x = -2.6 + i * 0.4
            box(architecture, f"SM_Oak_Plank_{i:02}", (x, 0, 0.006),
                (0.392, 5.58, 0.012), oak if i % 3 else oak_alt, 0.002)
    box(architecture, "SM_Left_Wall", (-2.74, 0, 1.50),
        (0.12, 5.6, 3.0), wall_mat)
    box(architecture, "SM_Right_Wall", (2.74, 0, 1.50),
        (0.12, 5.6, 3.0), wall_mat)
    # Four wall sections leave a real 2.10 m by 1.40 m window opening.
    box(architecture, "SM_Window_Wall_Left", (-1.225, 2.74, 1.50),
        (3.15, 0.12, 3.0), wall_mat)
    box(architecture, "SM_Window_Wall_Right", (2.625, 2.74, 1.50),
        (0.35, 0.12, 3.0), wall_mat)
    box(architecture, "SM_Window_Sill", (1.40, 2.74, 0.48),
        (2.10, 0.12, 0.96), wall_mat)
    box(architecture, "SM_Window_Header", (1.40, 2.74, 2.68),
        (2.10, 0.12, 0.64), wall_mat)
    box(context, "SM_Window_Exterior_Sky", (1.40, 3.20, 1.66),
        (2.12, 0.035, 1.41), glass if finish else clay)
    if finish:
        # Muted outside mass gives the window depth without pretending to be glass simulation.
        box(context, "SM_Exterior_Building_Left", (0.73, 3.07, 1.17),
            (0.45, 0.045, 0.43), distant)
        box(context, "SM_Exterior_Building_Right", (2.02, 3.05, 1.33),
            (0.37, 0.045, 0.75), distant)
    for x in (0.35, 1.40, 2.45):
        box(architecture, f"SM_Window_Frame_{x:.2f}", (x, 2.60, 1.65),
            (0.045, 0.10, 1.44), walnut if finish else clay)
    for z in (0.95, 2.35):
        box(architecture, f"SM_Window_Rail_{z:.2f}", (1.40, 2.60, z),
            (2.13, 0.10, 0.045), walnut if finish else clay)
    for y in (-2.56, 2.54):
        box(architecture, f"SM_Baseboard_{y:.2f}", (0, y, 0.10),
            (5.4, 0.065, 0.20), ceiling if finish else clay, 0.01)

    box(furniture, "SM_Sofa_Base", (-1.10, 0.72, 0.36),
        (2.23, 0.91, 0.40), linen if finish else clay, 0.08)
    box(furniture, "SM_Sofa_Back", (-1.10, 1.12, 0.80),
        (2.23, 0.19, 0.85), linen if finish else clay, 0.065)
    for x in (-2.09, -0.11):
        box(furniture, f"SM_Sofa_Arm_{x:.2f}", (x, 0.72, 0.68),
            (0.22, 0.92, 0.62), linen if finish else clay, 0.04)
    for x in (-1.63, -0.57):
        box(furniture, f"SM_Sofa_Seat_{x:.2f}", (x, 0.56, 0.62),
            (0.98, 0.60, 0.18), linen if finish else clay, 0.055)
        if finish:
            box(furniture, f"SM_Sofa_Back_Cushion_{x:.2f}",
                (x, 1.00, 0.95), (0.98, 0.12, 0.48), linen, 0.06)
    pillow = box(furniture, "SM_Teal_Pillow", (-1.75, 0.92, 0.93),
                 (0.42, 0.18, 0.43), accent if finish else clay, 0.055)
    pillow.rotation_euler.y = -0.18
    box(furniture, "SM_Rug", (0.0, -0.67, 0.018),
        (3.25, 1.84, 0.025), rug if finish else clay, 0.065)
    box(furniture, "SM_Coffee_Table_Top", (0.23, -0.62, 0.47),
        (1.35, 0.78, 0.07), walnut if finish else clay, 0.025)
    for x in (-0.33, 0.79):
        for y in (-0.93, -0.31):
            box(furniture, f"SM_Table_Leg_{x:.2f}_{y:.2f}", (x, y, 0.23),
                (0.065, 0.065, 0.45), walnut if finish else clay)
    for z in (0.38, 1.00, 1.62):
        box(furniture, f"SM_Shelf_{z:.2f}", (2.12, 0.58, z),
            (0.72, 1.24, 0.075), walnut if finish else clay, 0.012)
    for y in (0.02, 1.14):
        box(furniture, f"SM_Shelf_Upright_{y:.2f}", (2.12, y, 0.98),
            (0.065, 0.065, 1.35), walnut if finish else clay)
    if finish:
        for i in range(7):
            box(furniture, f"SM_Shelf_Book_{i:02}",
                (1.93 + (i % 3) * 0.17, 0.24 + (i // 3) * 0.26, 0.52),
                (0.11, 0.19, 0.24 + 0.04 * (i % 2)), accent if i % 2 else plaster)
        assign(sphere("SM_Shelf_Vase", (2.08, 0.73, 1.83),
                      0.16, brass, segments=24, rings=16, scale=(0.72, 0.72, 1.2)), furniture)
    box(context, "SM_Wall_Art_Frame", (-1.16, 2.56, 1.82),
        (0.92, 0.055, 0.72), walnut if finish else clay, 0.018)
    box(context, "SM_Wall_Art_Print", (-1.16, 2.515, 1.82),
        (0.80, 0.012, 0.61), plaster if finish else clay)
    if finish:
        box(context, "SM_Wall_Art_Field", (-1.30, 2.503, 1.78),
            (0.32, 0.004, 0.42), art)
        box(context, "SM_Wall_Art_Accent", (-0.94, 2.499, 1.71),
            (0.16, 0.004, 0.23), ink)

    assign(cylinder("SM_Pendant_Shade", (-1.87, -0.35, 2.40), 0.31, 0.24,
                    brass if finish else clay, vertices=48), lighting)
    assign(cylinder("SM_Pendant_Glow", (-1.87, -0.35, 2.25), 0.19, 0.04,
                    warm if finish else clay, vertices=48), lighting)
    box(lighting, "SM_Pendant_Cable", (-1.87, -0.35, 2.75),
        (0.014, 0.014, 0.52), brass if finish else clay)
    assign(area_light("LGT_Window_Daylight", (1.50, 2.35, 2.08),
                      570 if finish else 520, 2.1, color=(0.77, 0.88, 1.0),
                      target=(0.0, -0.30, 0.55)), lighting)
    assign(area_light("LGT_Pendant_Practical", (-1.87, -0.35, 2.20),
                      185 if finish else 0, 0.6, color=(1.0, 0.64, 0.34),
                      target=(-1.30, 0.55, 0.68)), lighting)
    assign(area_light("LGT_Fill_Soft", (-1.8, -2.4, 2.30), 105, 3.0,
                      color=(0.88, 0.91, 1.0), target=(0, 0.6, 0.8)), lighting)

    # A level 30 mm camera keeps verticals straight through the slow inspection push.
    cam = assign(camera("Archviz eye-level camera", (-1.05, -5.40, 1.60),
                        (0.05, 0.50, 1.60), lens=30), context)
    if finish:
        for frame, position in ((1, (-1.05, -5.40, 1.60)),
                                (36, (-0.58, -5.10, 1.60)),
                                (72, (-0.05, -4.80, 1.60))):
            cam.location = position
            look_at(cam, (0.05, 0.50, 1.60))
            cam.keyframe_insert(data_path="location", frame=frame)
            cam.keyframe_insert(data_path="rotation_euler", frame=frame)
    scene["archviz_variant"] = variant
    scene["archviz_window_m"] = [2.10, 1.40]
    return scene
