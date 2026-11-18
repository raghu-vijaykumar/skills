"""Original stealth lane with shadow cover, noisy metal, and a vertical route."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def rig(name):
    bpy.ops.object.empty_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    return obj


def attach(obj, parent):
    # Keep the readable silhouette assembled as the infiltrator climbs.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown stealth candidate")
    scene = reset_scene(spec, background=(0.025, 0.045, 0.075))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    floor = material("Stealth slate concrete", (0.14, 0.20, 0.25), roughness=0.93)
    shadow = material("Stealth blue quiet shadow", (0.025, 0.075, 0.13), roughness=0.98)
    steel = material("Stealth noisy steel plates", (0.42, 0.48, 0.52), metallic=0.58, roughness=0.52)
    edge = material("Stealth warning amber", (0.85, 0.37, 0.055),
                    emission=(0.85, 0.28, 0.015), emission_strength=1.1)
    cover = material("Stealth matte concealment crate", (0.10, 0.15, 0.16), roughness=0.89)
    hero_mat = material("Stealth infiltrator teal", (0.035, 0.43, 0.46), roughness=0.55)
    guard_mat = material("Stealth guard red", (0.72, 0.07, 0.09), roughness=0.60)
    light_mat = material("Stealth patrol search pool", (0.83, 0.54, 0.11),
                         emission=(0.90, 0.60, 0.12), emission_strength=0.55)
    goal_mat = material("Stealth secured terminal green", (0.05, 0.68, 0.23),
                        emission=(0.05, 0.70, 0.25), emission_strength=1.3)
    cube("SM_Stealth_Floor", (0, 0, -0.20), (11.5, 7.5, 0.38), floor)
    cube("SM_Stealth_Quiet_Shadow_Lane", (-2.65, 0, 0.015),
         (5.35, 6.8, 0.045), shadow)
    cube("Stealth lane edge", (0.06, 0, 0.04), (0.07, 6.8, 0.04), edge)
    # Repeated metal plates make the exposed path look and sound distinct from the quiet mat.
    for i in range(5):
        cube(f"SM_Stealth_Noisy_Plate_{i}", (1.23 + i * 0.72, -1.65, 0.045),
             (0.58, 2.4, 0.07), steel, edge=0.025)
        cube(f"Stealth plate amber stud {i}", (1.23 + i * 0.72, -2.75, 0.095),
             (0.13, 0.08, 0.035), edge)
    for i, (x, y, height) in enumerate(((-3.45, -1.6, 1.45),
                                         (-4.55, 0.1, 1.05),
                                         (-2.4, 0.15, 1.10))):
        cube(f"SM_Stealth_Concealment_Crate_{i}", (x, y, height / 2),
             (0.87, 0.91, height), cover, edge=0.045)
    # The elevated platform and ladder form a second readable infiltration route.
    cube("SM_Stealth_Upper_Catwalk", (0, 2.65, 2.22),
         (8.8, 1.35, 0.22), steel, edge=0.025)
    for x in (-3.65, 3.65):
        cube(f"Stealth catwalk support {x}", (x, 2.65, 1.10),
             (0.20, 0.25, 2.2), steel)
    cube("SM_Stealth_Ladder_Left_Rail", (-1.80, 1.63, 1.12),
         (0.10, 0.10, 2.25), edge)
    cube("SM_Stealth_Ladder_Right_Rail", (-1.10, 1.63, 1.12),
         (0.10, 0.10, 2.25), edge)
    for i in range(5):
        cube(f"Stealth ladder rung {i}", (-1.45, 1.55, 0.36 + i * 0.40),
             (0.77, 0.11, 0.07), steel)
    cube("Stealth upper rail", (0, 3.33, 2.85), (8.9, 0.10, 1.2), cover)
    terminal = cube("SM_Stealth_Objective_Terminal", (-3.30, 2.57, 2.86),
                    (0.56, 0.33, 1.05), cover, edge=0.035)
    terminal_screen = cube("SM_Stealth_Terminal_Screen", (-3.30, 2.37, 3.00),
                           (0.37, 0.045, 0.43), goal_mat)
    key(terminal_screen, "scale", ((1, (0.22, 0.22, 0.22)),
                                    (54, (0.22, 0.22, 0.22)),
                                    (72, (1, 1, 1)) if variant == 2 else
                                    (72, (0.22, 0.22, 0.22))))
    hero = rig("SM_Stealth_Infiltrator_Rig")
    attach(cylinder("SM_Stealth_Infiltrator_Body", (-3.90, -2.05, 0.72),
                    0.23, 1.03, hero_mat, vertices=12), hero)
    attach(sphere("Stealth infiltrator head", (-3.90, -2.05, 1.48),
                  0.25, hero_mat, segments=16, rings=8), hero)
    attach(cube("Stealth infiltrator visor", (-3.90, -2.27, 1.50),
                (0.36, 0.06, 0.11), goal_mat), hero)
    for side in (-1, 1):
        attach(cube(f"Stealth infiltrator leg {side}",
                    (-3.90 + side * 0.13, -2.05, 0.24),
                    (0.15, 0.16, 0.47), cover), hero)
    if variant == 2:
        key(hero, "location", ((1, (0, 0, 0)), (17, (0, 0, 0)),
                                (50, (2.38, 2.46, 0)),
                                (62, (2.38, 3.82, 1.36)),
                                (72, (0.66, 4.62, 2.30))))
    else:
        key(hero, "location", ((1, (0, 0, 0)), (72, (0.10, 0.05, 0))))
    guard = rig("SM_Stealth_Patrol_Guard_Rig")
    attach(cylinder("SM_Stealth_Guard_Body", (2.48, 2.60, 2.92),
                    0.30, 1.10, guard_mat, vertices=12), guard)
    attach(sphere("Stealth guard head", (2.48, 2.60, 3.65),
                  0.29, guard_mat, segments=16, rings=8), guard)
    attach(cube("Stealth guard visor", (2.48, 2.31, 3.67),
                (0.42, 0.07, 0.14), light_mat), guard)
    pool = cylinder("SM_Stealth_Guard_Light_Pool", (2.48, -1.10, 0.06),
                    1.36, 0.025, light_mat, vertices=32)
    if variant == 2:
        key(guard, "location", ((1, (0, 0, 0)), (32, (-0.75, 0, 0)),
                                 (72, (0.65, 0, 0))))
        key(pool, "location", ((1, (2.48, -1.10, 0.06)),
                                (32, (1.73, -1.10, 0.06)),
                                (72, (3.13, -1.10, 0.06))))
    else:
        key(guard, "location", ((1, (0, 0, 0)), (72, (-0.08, 0, 0))))
    area_light("Stealth shadow blue fill", (-5.0, -3.0, 7.5), 1350, 4.5,
               color=(0.25, 0.53, 1.0), target=(-2.7, 0, 0.7))
    area_light("Stealth warm patrol light", (3.6, -0.7, 6.0), 1850, 3.1,
               color=(1.0, 0.65, 0.25), target=(2.5, -1.2, 0.3))
    cam = camera("Stealth shadow-and-catwalk camera", (8.3, -11.8, 8.8),
                 (0, 0.55, 1.15), lens=35)
    key(cam, "location", ((1, (8.3, -11.8, 8.8)),
                          (72, (7.5 if variant == 2 else 8.25,
                                -10.9 if variant == 2 else -11.75,
                                8.4 if variant == 2 else 8.75))))
    scene["stealth_recipe"] = "quiet shadow cover, noisy exposed plates, patrolling guard, ladder to elevated objective"
    scene["stealth_variant"] = variant
    return scene
