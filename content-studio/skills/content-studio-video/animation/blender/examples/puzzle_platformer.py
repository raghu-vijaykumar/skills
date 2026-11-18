"""Original three-platform jump puzzle with an activated bridge and red hazards."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Keep the player silhouette intact throughout the visible jump arc.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def cone(name, location, radius, depth, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=radius,
                                    radius2=0, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown puzzle-platformer candidate")
    scene = reset_scene(spec, background=(0.045, 0.07, 0.12))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.42
    stone = material("Puzzle cool stone platforms", (0.30, 0.39, 0.46), roughness=0.85)
    edge = material("Puzzle platform pale edge", (0.58, 0.68, 0.70), roughness=0.82)
    hazard = material("Puzzle triangular hazard red", (0.85, 0.07, 0.07),
                      emission=(0.78, 0.02, 0.015), emission_strength=1.3)
    blue = material("Puzzle interactable cyan", (0.045, 0.68, 0.84),
                    emission=(0.025, 0.52, 0.83), emission_strength=1.5)
    dim = material("Puzzle dormant pressure pad", (0.09, 0.21, 0.26), roughness=0.65)
    hero_mat = material("Puzzle little jumper blue", (0.05, 0.31, 0.72), roughness=0.55)
    gold = material("Puzzle goal gold", (0.88, 0.58, 0.075),
                    emission=(0.92, 0.55, 0.04), emission_strength=1.0)
    dark = material("Puzzle deep void plinth", (0.05, 0.08, 0.12), roughness=0.90)
    cube("Puzzle deep void base", (0, 0, -1.1), (10.7, 5.0, 0.17), dark)
    # Platform edges leave a 0.7 m first jump; the second gap stays open until its bridge extends.
    platforms = (("Start", -2.9, 2.4), ("Switch", 0, 2.0), ("Goal", 3.0, 2.0))
    for name, x, width in platforms:
        cube(f"SM_Puzzle_{name}_Platform", (x, 0, -0.20),
             (width, 3.0, 0.38), stone, edge=0.035)
        cube(f"Puzzle {name} front lip", (x, -1.48, 0.02),
             (width, 0.05, 0.06), edge)
    # These four-sided cones give falling hazards a silhouette unlike the cyan controls.
    for i, (x, y) in enumerate(((-1.35, -0.65), (-1.35, 0.65),
                                (1.50, -0.70), (1.50, 0.55), (1.50, 1.30))):
        cone(f"SM_Puzzle_Red_Spike_{i}", (x, y, -0.52), 0.24, 0.55, hazard)
    pad = cylinder("SM_Puzzle_Pressure_Pad", (0, -0.15, 0.065),
                   0.38, 0.10, dim, vertices=12)
    ring = cylinder("SM_Puzzle_Pad_Cyan_Ring", (0, -0.15, 0.11),
                    0.26, 0.025, blue, vertices=12)
    if variant == 2:
        key(ring, "scale", ((1, (0.16, 0.16, 0.16)),
                             (43, (0.16, 0.16, 0.16)),
                             (52, (1, 1, 1)), (72, (1, 1, 1))))
    else:
        ring.scale = (0.16, 0.16, 0.16)
    # The blue span occupies the actual 1 m gap only after the pressure pad is reached.
    bridge = cube("SM_Puzzle_Extending_Bridge", (1.5, 0, -0.14),
                  (1.06, 1.28, 0.22), blue, edge=0.018)
    if variant == 2:
        key(bridge, "scale", ((1, (0.03, 1, 1)), (51, (0.03, 1, 1)),
                              (62, (1, 1, 1)), (72, (1, 1, 1))))
    else:
        bridge.scale = (0.03, 1, 1)
    # A compact arch makes the destination legible from the opening camera.
    for x in (3.30, 4.05):
        cube(f"Puzzle goal arch leg {x}", (x, 0.38, 0.88),
             (0.18, 0.21, 1.76), gold)
    cube("SM_Puzzle_Goal_Arch", (3.675, 0.38, 1.78),
         (0.95, 0.23, 0.20), gold)
    goal_light = sphere("SM_Puzzle_Goal_Light", (3.675, 0.39, 1.08),
                        0.19, gold, segments=16, rings=8)
    if variant == 2:
        key(goal_light, "scale", ((1, (0.6, 0.6, 0.6)),
                                   (62, (0.6, 0.6, 0.6)),
                                   (72, (1.22, 1.22, 1.22))))
    bpy.ops.object.empty_add(location=(0, 0, 0))
    hero = bpy.context.object
    hero.name = "SM_Puzzle_Jumper_Rig"
    attach(cylinder("SM_Puzzle_Jumper_Body", (-3.20, -0.58, 0.50),
                    0.22, 0.72, hero_mat, vertices=12), hero)
    attach(sphere("Puzzle jumper head", (-3.20, -0.58, 1.04),
                  0.25, hero_mat, segments=16, rings=8), hero)
    attach(cube("Puzzle jumper face", (-3.20, -0.82, 1.04),
                (0.30, 0.05, 0.10), gold), hero)
    for side in (-1, 1):
        attach(cube(f"Puzzle jumper foot {side}",
                    (-3.20 + side * 0.12, -0.58, 0.12),
                    (0.14, 0.22, 0.22), hero_mat), hero)
    if variant == 2:
        key(hero, "location", ((1, (0, 0, 0)), (16, (0.95, 0, 0)),
                                (26, (1.64, 0, 0.68)),
                                (43, (3.20, 0, 0)),
                                (53, (3.20, 0, 0)),
                                (72, (6.80, 0.76, 0))))
    else:
        key(hero, "location", ((1, (0, 0, 0)), (72, (0.12, 0, 0))))
    area_light("Puzzle cool overhead key", (-3.8, -4.5, 7.0), 1500, 4.5,
               color=(0.53, 0.82, 1.0), target=(-1.6, 0, 0))
    area_light("Puzzle warm goal light", (4.0, -2.0, 6.5), 1200, 3.6,
               color=(1.0, 0.77, 0.42), target=(2.8, 0, 0.3))
    cam = camera("Puzzle three-platform overview camera", (7.8, -10.9, 7.2),
                 (0, 0.15, 0.15), lens=35)
    key(cam, "location", ((1, (7.8, -10.9, 7.2)),
                          (72, (7.2 if variant == 2 else 7.76,
                                -10.2 if variant == 2 else -10.86,
                                6.9 if variant == 2 else 7.17))))
    scene["puzzle_recipe"] = "readable cyan pad and bridge, red triangular hazards, 0.7m first jump, 1m second span, gold goal"
    scene["puzzle_variant"] = variant
    return scene
