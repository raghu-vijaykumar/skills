"""Original underwater kelp biome with moving fish and rising bubbles."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Preserve the modeled world positions while making each organism movable.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def rock(name, location, scale, mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored kelp biome candidate")
    scene = reset_scene(spec, background=(0.015, 0.19, 0.27))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.72
    sand = material("Kelp pale silt bed", (0.37, 0.46, 0.38), roughness=0.99)
    rockmat = material("Kelp algae worn basalt", (0.13, 0.25, 0.24), roughness=0.94)
    kelp_dark = material("Kelp dark green blade", (0.065, 0.26, 0.15), roughness=0.85)
    kelp_light = material("Kelp sunlit olive blade", (0.19, 0.40, 0.18), roughness=0.82)
    orange = material("Kelp coral orange", (0.72, 0.27, 0.11), roughness=0.92,
                      emission=(0.65, 0.18, 0.05), emission_strength=0.25)
    fishmat = material("Kelp amber schooling fish", (0.85, 0.43, 0.09),
                       roughness=0.48, emission=(0.85, 0.30, 0.04),
                       emission_strength=0.48)
    eye = material("Kelp fish black eye", (0.012, 0.02, 0.023), roughness=0.35)
    bubblemat = material("Kelp pale bubble highlight", (0.55, 0.86, 0.91),
                         metallic=0.15, roughness=0.16,
                         emission=(0.16, 0.45, 0.52), emission_strength=0.45)

    cube("SM_Kelp_Silt_Bed", (0, 7, -0.25), (25, 34, 0.40), sand)
    for i in range(14):
        x = -6.5 + (i * 3 % 13)
        y = -1.0 + (i * 5 % 16)
        rock(f"Kelp algae rock {i}", (x, y, 0.15),
             (0.55 + (i % 3) * 0.2, 0.44 + (i % 2) * 0.28, 0.33), rockmat)
    for i in range(11):
        x = -5.7 + (i * 7 % 12)
        y = 2.0 + (i * 3 % 11)
        stem = cube(f"Kelp orange coral stalk {i}",
                    (x, y, 0.55), (0.12, 0.14, 1.0 + i % 3 * 0.15), orange)
        stem.rotation_euler[1] = (i % 3 - 1) * 0.19
        for branch in (-1, 1):
            twig = cube(f"Kelp coral branch {i} {branch}",
                        (x + branch * 0.18, y, 0.82), (0.07, 0.08, 0.54), orange)
            twig.rotation_euler[1] = branch * 0.55

    for i in range(24):
        x = -6.1 + (i * 7 % 13)
        y = -0.5 + (i * 11 % 17)
        height = 2.2 + (i % 5) * 0.42
        bpy.ops.object.empty_add(location=(x, y, 0.0))
        root = bpy.context.object
        root.name = f"SM_Kelp_Blades_Rig_{i}"
        root["kelp_stand"] = i
        for level in range(3):
            z = 0.45 + level * height / 3
            blade = cube(f"Kelp blade segment {i} {level}",
                         (x + 0.12 * level, y, z),
                         (0.23 - level * 0.04, 0.07, height / 3 + 0.12),
                         kelp_light if i % 4 == 0 else kelp_dark)
            blade.rotation_euler[1] = -0.11 * level
            attach(blade, root)
        if variant == 2:
            animate(root, "rotation_euler", ((1, (0, 0, -0.03)),
                    (36, (0.0, 0.08 + i % 3 * 0.015, 0.035)),
                    (72, (0.0, -0.06, -0.02))))

    bpy.ops.object.empty_add(location=(-3.8, 0.8, 2.3))
    school = bpy.context.object
    school.name = "SM_Kelp_Fish_School_Rig"
    school["school_count"] = 7
    for i in range(7):
        x = -3.8 + (i % 4) * 0.75
        y = 0.8 + (i // 4) * 0.55
        z = 2.22 + (i // 4) * 0.42 + (i % 2) * 0.08
        attach(sphere(f"Kelp amber fish body {i}", (x, y, z), 1,
                      fishmat, segments=16, rings=8,
                      scale=(0.33, 0.12, 0.15)), school)
        tail = cube(f"Kelp amber fish tail {i}",
                    (x - 0.38, y, z), (0.23, 0.035, 0.22), fishmat)
        tail.rotation_euler[1] = 0.30
        attach(tail, school)
        attach(sphere(f"Kelp fish eye {i}", (x + 0.19, y - 0.105, z + 0.04),
                      0.035, eye, segments=8, rings=6), school)
    if variant == 2:
        animate(school, "location", ((1, (-3.8, 0.8, 2.3)),
                 (24, (-2.35, 1.1, 2.48)),
                 (48, (-0.50, 1.3, 2.55)),
                 (72, (1.55, 1.5, 2.38))))
    else:
        animate(school, "location", ((1, (-3.8, 0.8, 2.3)),
                 (72, (-3.15, 0.95, 2.34))))
    bpy.ops.object.empty_add(location=(-2.5, 2.0, 0))
    bubbles = bpy.context.object
    bubbles.name = "SM_Kelp_Bubble_Rig"
    for i in range(17):
        x = -2.5 + (i % 4) * 0.16
        y = 2.0 + (i % 3) * 0.13
        z = 0.4 + i * 0.17
        attach(sphere(f"Kelp bubble {i}", (x, y, z),
                      0.045 + (i % 4) * 0.012, bubblemat,
                      segments=8, rings=6), bubbles)
    if variant == 2:
        animate(bubbles, "location", ((1, (-2.5, 2, 0)),
                 (72, (-2.25, 2, 1.15))))
    else:
        animate(bubbles, "location", ((1, (-2.5, 2, 0)),
                 (72, (-2.5, 2, 0.1))))

    # Blue fill and a narrow warm shaft suggest shallow, filtered sunlight.
    area_light("Kelp cyan shallow-water fill", (-5, -4, 9), 1600, 8,
               color=(0.25, 0.80, 1.0), target=(0, 4, 1.8))
    area_light("Kelp filtered-sun shaft", (4, 5, 11), 1200, 6,
               color=(0.70, 1.0, 0.72), target=(0, 4, 2.0))
    cam = camera("Kelp forest inspection camera", (4.2, -10.5, 3.4),
                 (0, 4.0, 2.0), lens=35)
    animate(cam, "location", ((1, (4.2, -10.5, 3.4)),
             (72, (3.7 if variant == 2 else 4.1,
                   -8.6 if variant == 2 else -10.3, 3.25))))
    scene["biome_recipe"] = "underwater kelp forest, blue filtered light, dense swaying blades, algae rocks, fish, rising bubbles"
    scene["biome_variant"] = variant
    return scene
