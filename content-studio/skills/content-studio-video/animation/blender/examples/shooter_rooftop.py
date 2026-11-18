"""Original first-person rooftop shooter lane with cover, landmark, and loot."""

from pathlib import Path
import math

import bpy
from mathutils import Vector

from common import area_light, camera, cube, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def camera_prop(name, cam, location, dimensions, mat):
    # Camera-space props preserve a true FPS foreground during the peek and push.
    obj = cube(name, (0, 0, 0), dimensions, mat, edge=0.018)
    obj.parent = cam
    obj.location = location
    obj.rotation_euler = (0, 0, 0)
    return obj


def attach(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown shooter rooftop candidate")
    scene = reset_scene(spec, background=(0.28, 0.39, 0.53))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.78
    concrete = material("Shooter weathered concrete", (0.32, 0.36, 0.38), roughness=0.91)
    dark = material("Shooter charcoal cover", (0.065, 0.087, 0.10), roughness=0.78)
    white = material("Shooter bright sightline paint", (0.86, 0.86, 0.75), roughness=0.84)
    orange = material("Shooter orange landmark", (0.86, 0.24, 0.07), roughness=0.57)
    red = material("Shooter target red", (0.78, 0.11, 0.10), roughness=0.66)
    lime = material("Shooter readable loot lime", (0.38, 0.89, 0.13),
                    emission=(0.26, 0.79, 0.10), emission_strength=0.8)
    teal = material("Shooter reticle cyan", (0.15, 0.83, 0.89),
                    emission=(0.11, 0.77, 0.88), emission_strength=2.0)
    flash_mat = material("Shooter muzzle amber", (1.0, 0.55, 0.11),
                         emission=(1.0, 0.45, 0.06), emission_strength=4.0)
    cube("SM_Shooter_Rooftop_Floor", (0, 3.0, -0.21), (19, 27, 0.42), concrete)
    for side in (-1, 1):
        cube(f"Shooter parapet {side}", (side * 9.1, 3.0, 0.60),
             (0.42, 27, 1.2), dark)
        cube(f"Shooter outer stripe {side}", (side * 7.6, 3.0, 0.025),
             (0.07, 23, 0.015), white)
    for i in range(9):
        cube(f"Shooter broken lane dash {i}", (0.15, -6.0 + 2.25 * i, 0.024),
             (0.09, 0.90, 0.015), white)
    cube("Shooter back stop", (0, 16.25, 1.0), (18.7, 0.34, 2.0), dark)
    # Unequal cover silhouettes keep a readable safe lane and one flank gap.
    cube("SM_Shooter_Near_Chest_Cover", (-2.6, -0.50, 0.80),
         (3.3, 0.90, 1.60), dark, edge=0.075)
    cube("Shooter near cover paint band", (-2.6, -0.98, 1.18),
         (3.1, 0.018, 0.12), white)
    cube("SM_Shooter_Mid_Half_Cover", (2.8, 4.25, 0.62),
         (3.2, 1.0, 1.24), dark, edge=0.065)
    cube("Shooter mid cover paint band", (2.8, 3.73, 0.98),
         (2.95, 0.02, 0.11), white)
    cube("Shooter far cover", (-3.4, 8.6, 0.48), (2.3, 0.70, 0.96), dark)
    tower = cube("SM_Shooter_Orange_Landmark_Tower", (5.2, 11.2, 3.35),
                 (1.35, 1.35, 6.70), orange, edge=0.05)
    tower["purpose"] = "high-contrast rooftop navigation landmark"
    cube("Shooter tower beacon", (5.2, 11.2, 6.95),
         (1.68, 1.68, 0.23), flash_mat)
    for i in range(3):
        cube(f"Shooter tower rung {i}", (5.2, 10.49, 1.5 + i * 1.28),
             (0.72, 0.04, 0.09), dark)
    target_rig = bpy.data.objects.new("SM_Shooter_Target_Rig", None)
    scene.collection.objects.link(target_rig)
    target_rig.location = (0, 10.6, 0.16)
    # Separate head, arms, and boots make a distant target readable during the peek.
    attach(cube("SM_Shooter_Red_Target", (0, 10.6, 1.52),
                (0.79, 0.22, 1.26), red, edge=0.045), target_rig)
    attach(sphere("Shooter target head", (0, 10.6, 2.38),
                  0.30, red, segments=16, rings=8), target_rig)
    for side in (-1, 1):
        attach(cube(f"Shooter target arm {side}",
                    (side * 0.55, 10.6, 1.51), (0.27, 0.22, 0.92), red), target_rig)
        attach(cube(f"Shooter target leg {side}",
                    (side * 0.23, 10.6, 0.48), (0.25, 0.22, 0.95), red), target_rig)
    cube("Shooter target ground marker", (0, 10.6, 0.018),
         (1.6, 1.0, 0.025), white)
    loot = cube("SM_Shooter_Lime_Loot_Case", (1.20, 2.00, 0.39),
                (1.45, 0.93, 0.78), lime, edge=0.055)
    loot["purpose"] = "high-contrast pickup visible beyond cover"
    lid = cube("SM_Shooter_Loot_Case_Lid", (1.20, 2.00, 0.82),
               (1.48, 0.99, 0.16), dark, edge=0.025)
    if variant == 2:
        animate(lid, "location", ((1, (1.20, 2.00, 0.82)),
                                   (52, (1.20, 2.00, 0.82)),
                                   (72, (1.20, 2.38, 1.22))))
        animate(lid, "rotation_euler", ((1, (0, 0, 0)), (52, (0, 0, 0)),
                                         (72, (0.70, 0, 0))))
        animate(target_rig, "rotation_euler", ((1, (0, 0, 0)),
                                                (53, (0, 0, 0)),
                                                (72, (1.18, 0, 0))))
    area_light("Shooter open-sky hard key", (-4.0, -2.0, 12), 2600, 5.0,
               color=(0.94, 0.96, 1.0), target=(0, 5, 0))
    area_light("Shooter warm landmark bounce", (7.5, 7.0, 7.0), 800, 6.0,
               color=(1.0, 0.68, 0.39), target=(0, 6, 0))
    cam = camera("Shooter human-height first-person camera", (-2.35, -7.7, 1.68),
                 (0, 10.0, 1.35), lens=33)
    cam.data.clip_start = 0.05
    cam["eye_height_m"] = 1.68
    if variant == 2:
        original_aim = tuple(cam.rotation_euler)
        peek_direction = Vector((0, 10.6, 1.55)) - Vector((-1.10, -6.8, 1.68))
        peek_aim = tuple(peek_direction.to_track_quat("-Z", "Y").to_euler())
        animate(cam, "location", ((1, (-2.35, -7.7, 1.68)),
                                   (28, (-2.35, -7.7, 1.68)),
                                   (47, (-1.10, -6.8, 1.68)),
                                   (72, (-1.10, -5.3, 1.68))))
        animate(cam, "rotation_euler", ((1, original_aim), (28, original_aim),
                                         (47, peek_aim), (72, peek_aim)))
    else:
        animate(cam, "location", ((1, (-2.35, -7.7, 1.68)),
                                   (72, (-2.20, -7.6, 1.68))))
    camera_prop("SM_Shooter_Visible_Gun_Body", cam, (0.46, -0.30, -1.10),
                (0.22, 0.22, 0.69), dark)
    camera_prop("Shooter gun upper slide", cam, (0.46, -0.18, -1.25),
                (0.18, 0.11, 0.48), concrete)
    camera_prop("Shooter gun cyan rear sight", cam, (0.46, -0.10, -0.79),
                (0.20, 0.04, 0.04), teal)
    for axis in (-1, 1):
        camera_prop(f"Shooter reticle horizontal {axis}", cam,
                    (axis * 0.050, 0, -1.50), (0.042, 0.004, 0.003), teal)
        camera_prop(f"Shooter reticle vertical {axis}", cam,
                    (0, axis * 0.050, -1.50), (0.004, 0.042, 0.003), teal)
    muzzle = camera_prop("SM_Shooter_Muzzle_Flash", cam, (0.46, -0.18, -1.65),
                         (0.075, 0.09, 0.11), flash_mat)
    if variant == 2:
        animate(muzzle, "scale", ((1, (0, 0, 0)), (48, (0, 0, 0)),
                                  (51, (1, 1, 1)), (55, (0, 0, 0)),
                                  (72, (0, 0, 0))))
    else:
        muzzle.scale = (0, 0, 0)
    scene["shooter_recipe"] = "human-height first-person peek, asymmetrical cover, open sightline, orange landmark, lime loot"
    scene["shooter_variant"] = variant
    return scene
