"""Original full-body chibi postal courier with a hop and letter offering."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def attach(obj, parent):
    """Keep a child's authored pose while adding an editable animation control."""
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def control(name, location, parent=None):
    bpy.ops.object.empty_add(location=location)
    obj = bpy.context.object
    obj.name = name
    return attach(obj, parent) if parent else obj


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.79, 0.77, 0.88))
    scene.unit_settings.system = "METRIC"
    skin = material("Chibi warm peach", (0.97, 0.66, 0.51), roughness=0.92)
    hair = material("Chibi dark plum hair", (0.21, 0.11, 0.24), roughness=0.88)
    coat = material("Chibi bright teal coat", (0.10, 0.56, 0.56), roughness=0.86)
    collar = material("Chibi cream collar", (0.95, 0.88, 0.65), roughness=0.92)
    boots = material("Chibi cherry boots", (0.73, 0.13, 0.19), roughness=0.83)
    eyes = material("Chibi midnight eye", (0.04, 0.07, 0.12), roughness=0.5)
    eye_light = material("Chibi eye glint", (1, 0.98, 0.87), roughness=0.45)
    blush = material("Chibi rose blush", (0.93, 0.31, 0.34), roughness=0.95)
    letter = material("Chibi ivory envelope", (0.97, 0.91, 0.74), roughness=0.97)
    seal = material("Chibi heart seal", (0.88, 0.17, 0.24), roughness=0.9)
    stage = material("Chibi lilac stage", (0.61, 0.64, 0.81), roughness=0.98)
    shadow_mat = material("Chibi soft contact shadow", (0.35, 0.36, 0.57), roughness=1)
    backdrop = material("Chibi pastel backdrop", (0.76, 0.73, 0.84), roughness=1)
    gold = material("Chibi postal gold", (0.98, 0.70, 0.31), roughness=0.92)
    ribbon = material("Chibi postal ribbon", (0.89, 0.40, 0.43), roughness=0.92)

    cube("Chibi matte floor", (0, 0, -0.10), (7, 5, 0.20), stage)
    cube("Chibi pastel wall", (0, 2.1, 1.9), (7, 0.1, 4.1), backdrop)
    # A lightweight postal roundel frames the character without making it an environment shot.
    bpy.ops.mesh.primitive_torus_add(major_radius=1.51, minor_radius=0.045,
                                    location=(0, 2.00, 1.55),
                                    rotation=(math.pi / 2, 0, 0))
    roundel = bpy.context.object
    roundel.name = "Chibi postal stage roundel"
    roundel.data.materials.append(gold)
    for x in (-2.15, 2.15):
        cube("Chibi postal stage accent", (x, 2.02, 1.24),
             (0.14, 0.08, 1.9), ribbon, edge=0.06)
    shadow = sphere("Chibi contact shadow", (0, 0.03, 0.015), 0.45,
                    shadow_mat, scale=(1.45, 0.62, 0.025))

    root = control("Chibi courier root", (0, 0, 0))
    head_control = control("Chibi head control", (0, 0, 1.42), root)
    # The 1.44 m head dominates a 2.42 m full figure; tiny limbs keep the SD silhouette.
    head = attach(sphere("SM_Chibi_Head", (0, -0.03, 1.71), 0.72, skin,
                         scale=(0.98, 0.80, 1.0)), head_control)
    head["design_head_m"] = 1.44
    hair_cap = attach(sphere("Chibi hair cap", (0, 0.03, 2.09), 0.72, hair,
                             scale=(1.04, 0.83, 0.49)), head_control)
    attach(sphere("Chibi courier cap visor", (0, -0.54, 2.13), 0.27,
                  hair, scale=(2.05, 0.70, 0.21)), head_control)
    attach(sphere("Chibi courier cap badge", (0, -0.58, 2.22), 0.09,
                  gold, scale=(1.1, 0.18, 1.0)), head_control)
    attach(sphere("Chibi left hair curl", (-0.61, -0.07, 1.78), 0.18, hair,
                  scale=(0.62, 0.75, 1.4)), head_control)
    attach(sphere("Chibi right hair curl", (0.61, -0.07, 1.78), 0.18, hair,
                  scale=(0.62, 0.75, 1.4)), head_control)
    for x, side in ((-0.29, "Left"), (0.29, "Right")):
        eye = attach(sphere(f"SM_Chibi_{side}_Eye", (x, -0.59, 1.73), 0.19,
                            eyes, scale=(0.84, 0.30, 1.17)), head_control)
        attach(sphere(f"Chibi {side.lower()} eye glint", (x - 0.055, -0.655, 1.81),
                      0.052, eye_light, scale=(0.8, 0.34, 1)), head_control)
        attach(sphere(f"Chibi {side.lower()} cheek", (x * 1.57, -0.51, 1.54),
                      0.12, blush, scale=(1.3, 0.23, 0.50)), head_control)
        for frame, height in ((1, 1), (20, 1), (23, 0.09), (26, 1),
                              (49, 1), (52, 0.09), (55, 1), (72, 1)):
            eye.scale.z = 1.17 * height
            eye.keyframe_insert(data_path="scale", frame=frame)
    attach(sphere("Chibi button nose", (0, -0.61, 1.50), 0.07, blush,
                  scale=(0.8, 0.33, 0.6)), head_control)
    attach(sphere("Chibi tiny smile", (0, -0.614, 1.39), 0.07, hair,
                  scale=(1.1, 0.18, 0.30)), head_control)

    torso = attach(sphere("SM_Chibi_Torso", (0, 0, 0.68), 0.42, coat,
                          scale=(0.94, 0.71, 0.76)), root)
    torso["design_short_body"] = True
    attach(sphere("Chibi cream collar", (0, -0.24, 0.91), 0.22, collar,
                  scale=(1.24, 0.58, 0.42)), root)
    # A diagonal strap and small side pouch supply a second postal cue at GIF size.
    strap = attach(cube("Chibi mail satchel strap", (-0.05, -0.29, 0.69),
                        (0.07, 0.035, 0.52), gold, edge=0.015), root)
    strap.rotation_euler.y = -0.52
    attach(cube("Chibi mail satchel", (-0.40, -0.13, 0.49),
                (0.31, 0.20, 0.28), ribbon, edge=0.05), root)
    for x, side in ((-0.18, "left"), (0.18, "right")):
        attach(cylinder(f"Chibi {side} short leg", (x, 0, 0.28), 0.095, 0.30,
                        coat, vertices=16), root)
        attach(sphere(f"Chibi {side} boot", (x, -0.11, 0.12), 0.19, boots,
                      scale=(0.70, 1.04, 0.58)), root)
    attach(sphere("Chibi left tiny sleeve", (-0.43, 0, 0.72), 0.19, coat,
                  scale=(0.78, 0.72, 1)), root)
    attach(sphere("Chibi left mitten", (-0.54, -0.04, 0.57), 0.13, skin), root)
    arm = control("Chibi offer arm control", (0.38, -0.02, 0.87), root)
    attach(sphere("Chibi right tiny sleeve", (0.47, -0.04, 0.74), 0.20,
                  coat, scale=(0.76, 0.72, 1.2)), arm)
    attach(sphere("Chibi right mitten", (0.60, -0.12, 0.60), 0.13, skin), arm)
    envelope = attach(cube("SM_Chibi_Envelope", (0.78, -0.27, 0.64),
                           (0.48, 0.045, 0.31), letter, edge=0.012), arm)
    envelope["story_prop"] = "delivered letter"
    attach(cube("Chibi envelope fold", (0.78, -0.299, 0.72),
                (0.38, 0.008, 0.012), collar), arm)
    attach(sphere("Chibi heart seal", (0.78, -0.31, 0.65), 0.055,
                  seal, scale=(1, 0.18, 0.9)), arm)

    for frame, height, tilt, offer, shadow_size in (
            (1, 0, -0.07, 0, 1.0), (13, -0.10, 0.05, 0.03, 1.08),
            (24, 0.56, -0.10, -0.60, 0.78),
            (36, 0.78, 0.12, -1.14, 0.65),
            (48, 0.43, 0.06, -1.00, 0.83),
            (60, -0.06, -0.04, -1.10, 1.05),
            (72, 0, 0.03, -0.96, 1.0)):
        root.location.z = height
        root.keyframe_insert(data_path="location", frame=frame)
        head_control.rotation_euler.z = tilt
        head_control.keyframe_insert(data_path="rotation_euler", frame=frame)
        arm.rotation_euler.y = offer
        arm.keyframe_insert(data_path="rotation_euler", frame=frame)
        shadow.scale.x = 1.45 * shadow_size
        shadow.scale.y = 0.62 * shadow_size
        shadow.keyframe_insert(data_path="scale", frame=frame)

    # The wide portrait framing preserves the huge head through the full hop.
    camera("Chibi portrait camera", (0, -7.0, 2.1), (0, 0, 1.57), ortho=6.5)
    area_light("Chibi broad key", (-2.5, -3, 5), 750, 2.8,
               color=(1, 0.86, 0.79), target=(0, 0, 1.2))
    area_light("Chibi cool bounce", (2.4, -1, 3.3), 250, 3.0,
               color=(0.72, 0.83, 1.0), target=(0, 0, 1.4))
    scene["chibi_ratio_rule"] = "head at least half of full figure height; short limbs"
    return scene
