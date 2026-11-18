"""Original readable sparring arena with a shield clash and breakable crates."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Keep the posed fighter and prop silhouettes when their control rigs move.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def rig(name, location):
    bpy.ops.object.empty_add(location=location)
    obj = bpy.context.object
    obj.name = name
    return obj


def fighter(name, origin, armor, dark, visor, sword=False, shield=False):
    x, y, _ = origin
    body = rig(f"SM_Arena_{name}_Rig", (0, 0, 0))
    attach(cube(f"SM_Arena_{name}_Torso", (x, y, 1.27),
                (0.82, 0.49, 1.0), armor, edge=0.08), body)
    attach(cube(f"Arena {name} chest inset", (x, y - 0.252, 1.33),
                (0.47, 0.022, 0.34), dark), body)
    attach(sphere(f"Arena {name} helmet", (x, y, 2.04),
                  0.34, armor, segments=20, rings=10), body)
    attach(cube(f"Arena {name} visor", (x, y - 0.30, 2.07),
                (0.38, 0.055, 0.13), visor), body)
    for side in (-1, 1):
        attach(cube(f"Arena {name} boot {side}", (x + side * 0.23, y, 0.42),
                    (0.24, 0.32, 0.83), dark, edge=0.035), body)
        attach(cube(f"Arena {name} arm {side}", (x + side * 0.55, y, 1.31),
                    (0.23, 0.30, 0.78), armor, edge=0.035), body)
    if sword:
        pivot = rig("SM_Arena_Sword_Pivot", (x + 0.70, y - 0.10, 1.44))
        attach(pivot, body)
        attach(cube("SM_Arena_Hero_Blade", (x + 0.75, y - 0.10, 2.30),
                    (0.15, 0.13, 1.65), visor, edge=0.035), pivot)
        attach(cube("Arena sword crossguard", (x + 0.75, y - 0.10, 1.51),
                    (0.55, 0.17, 0.12), dark), pivot)
    if shield:
        pivot = rig("SM_Arena_Shield_Pivot", (x - 0.60, y - 0.20, 1.36))
        attach(pivot, body)
        attach(cube("SM_Arena_Rival_Shield", (x - 0.70, y - 0.32, 1.43),
                    (0.18, 0.52, 1.35), dark, edge=0.05), pivot)
        attach(cube("Arena shield bronze stripe", (x - 0.80, y - 0.32, 1.42),
                    (0.025, 0.55, 0.15), armor), pivot)
    return body


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown action arena candidate")
    scene = reset_scene(spec, background=(0.07, 0.10, 0.15))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    floor = material("Arena dark slate", (0.115, 0.13, 0.17), roughness=0.88)
    ring = material("Arena warm sand stone", (0.40, 0.31, 0.22), roughness=0.93)
    trim = material("Arena legibility gold", (0.95, 0.56, 0.14),
                    emission=(0.85, 0.34, 0.04), emission_strength=0.5)
    blue = material("Arena cobalt fighter", (0.05, 0.37, 0.80), roughness=0.54)
    red = material("Arena coral rival", (0.75, 0.16, 0.16), roughness=0.58)
    dark = material("Arena graphite gear", (0.035, 0.05, 0.065), roughness=0.67)
    cyan = material("Arena cyan blade", (0.20, 0.87, 0.93),
                    emission=(0.12, 0.78, 0.95), emission_strength=1.4)
    clay = material("Arena breakable clay", (0.65, 0.39, 0.20), roughness=0.94)
    flash = material("Arena impact gold", (1.0, 0.80, 0.23),
                     emission=(1.0, 0.55, 0.10), emission_strength=3.2)
    cube("SM_Arena_Outer_Floor", (0, 0, -0.34), (22, 19, 0.5), floor)
    cylinder("SM_Arena_Readable_Octagonal_Ring", (0, 0, -0.03),
             6.2, 0.42, ring, vertices=8, rotation=(0, 0, math.pi / 8))
    cylinder("Arena gold ring outline", (0, 0, 0.20),
             5.45, 0.025, trim, vertices=8, rotation=(0, 0, math.pi / 8))
    cylinder("Arena clear central fight plane", (0, 0, 0.224),
             5.32, 0.03, ring, vertices=8, rotation=(0, 0, math.pi / 8))
    for x in (-5.65, 5.65):
        for y in (-4.0, 4.0):
            cylinder(f"Arena low corner marker {x} {y}", (x, y, 0.44),
                     0.33, 0.8, trim, vertices=8)
    hero = fighter("Hero", (-2.6, -0.8, 0), blue, dark, cyan, sword=True)
    rival = fighter("Rival", (1.6, 0.5, 0), red, dark, trim, shield=True)
    if variant == 2:
        animate(hero, "location", ((1, (0, 0, 0)), (22, (0, 0, 0)),
                                   (44, (1.45, 0.55, 0)), (72, (1.45, 0.55, 0))))
        animate(bpy.data.objects["SM_Arena_Sword_Pivot"], "rotation_euler",
                ((1, (0, -0.60, 0)), (38, (0, -0.60, 0)),
                 (53, (0, 1.15, 0)), (72, (0, 0.55, 0))))
        animate(bpy.data.objects["SM_Arena_Shield_Pivot"], "rotation_euler",
                ((1, (0, -0.20, 0)), (38, (0, -0.20, 0)),
                 (53, (0, -0.88, 0)), (72, (0, -0.88, 0))))
        animate(rival, "location", ((1, (0, 0, 0)), (53, (0, 0, 0)),
                                    (72, (0.65, 0.25, 0))))
    else:
        animate(hero, "location", ((1, (0, 0, 0)), (72, (0.12, 0, 0))))
        animate(bpy.data.objects["SM_Arena_Sword_Pivot"], "rotation_euler",
                ((1, (0, -0.60, 0)), (72, (0, -0.50, 0))))
        animate(bpy.data.objects["SM_Arena_Shield_Pivot"], "rotation_euler",
                ((1, (0, -0.20, 0)), (72, (0, -0.20, 0))))
    for i in range(4):
        x = 3.55 + (i % 2) * 0.65
        y = 1.45 + (i // 2) * 0.67
        chunk = cube(f"SM_Arena_Breakable_Clay_Chunk_{i}", (x, y, 0.60),
                     (0.56, 0.56, 0.62), clay, edge=0.035)
        if variant == 2:
            animate(chunk, "location", ((1, (x, y, 0.60)), (51, (x, y, 0.60)),
                                        (72, (x + (i % 2 * 2 - 1) * 0.75,
                                              y + (i // 2 * 2 - 1) * 0.85,
                                              0.50 + (i % 2) * 0.45))))
            animate(chunk, "rotation_euler", ((1, (0, 0, 0)), (51, (0, 0, 0)),
                                              (72, (0.35 * (i + 1), -0.24 * i, 0.40 * i))))
    burst = rig("SM_Arena_Impact_Burst_Rig", (2.5, -0.20, 1.37))
    for i in range(6):
        spoke = cube(f"Arena impact spoke {i}", (2.5, -0.20, 1.95),
                     (0.075, 0.08, 1.0), flash)
        attach(spoke, burst)
        spoke.rotation_euler[1] = i * math.pi / 3
    if variant == 2:
        animate(burst, "scale", ((1, (0, 0, 0)), (47, (0, 0, 0)),
                                 (54, (0.95, 0.95, 0.95)), (67, (0, 0, 0)),
                                 (72, (0, 0, 0))))
    else:
        burst.scale = (0, 0, 0)
    area_light("Arena strong action key", (-4.0, -5.5, 10), 2300, 5.0,
               color=(0.90, 0.94, 1.0), target=(0, 0, 0))
    area_light("Arena warm rival rim", (6.0, 3.0, 7), 1000, 4.0,
               color=(1.0, 0.63, 0.36), target=(1.6, 0.5, 1))
    cam = camera("Arena unobstructed combat camera", (9.0, -13.5, 10.5),
                 (0.3, 0.2, 1.0), lens=40)
    animate(cam, "location", ((1, (9.0, -13.5, 10.5)),
             (72, (8.5 if variant == 2 else 8.95,
                   -12.9 if variant == 2 else -13.45, 10.2))))
    scene["arena_recipe"] = "clear octagonal arena, blue blade versus coral shield, readable breakable clay, unobstructed camera"
    scene["arena_variant"] = variant
    return scene
