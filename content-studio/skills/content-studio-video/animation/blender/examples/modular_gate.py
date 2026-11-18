"""Original modular three-room run with a collected ability and opening gate."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # The runner's simple silhouette remains stable while it crosses room seams.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def cone(name, location, radius, depth, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=radius,
                                    radius2=0, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown modular run candidate")
    scene = reset_scene(spec, background=(0.035, 0.065, 0.08))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.44
    floor = material("Run charcoal plinth", (0.075, 0.09, 0.11), roughness=0.93)
    moss = material("Run moss room", (0.16, 0.32, 0.15), roughness=0.93)
    stone = material("Run stone chamber", (0.34, 0.36, 0.33), roughness=0.87)
    crystal = material("Run crystal room", (0.22, 0.13, 0.35), roughness=0.62)
    leaf = material("Run leaf green", (0.19, 0.52, 0.20), roughness=0.83)
    cyan = material("Run collected dash cyan", (0.03, 0.67, 0.83),
                    emission=(0.02, 0.64, 0.91), emission_strength=1.2)
    gate_mat = material("Run ability lock blue", (0.035, 0.35, 0.60),
                        emission=(0.04, 0.36, 0.68), emission_strength=1.0)
    violet = material("Run crystal violet", (0.58, 0.20, 0.82),
                      emission=(0.45, 0.13, 0.77), emission_strength=0.8)
    red = material("Run curse modifier red", (0.83, 0.07, 0.10),
                   emission=(0.75, 0.03, 0.05), emission_strength=0.8)
    gold = material("Run shield modifier gold", (0.96, 0.62, 0.07),
                    emission=(0.92, 0.54, 0.03), emission_strength=1.2)
    runner_mat = material("Run traveler warm ivory", (0.77, 0.68, 0.47), roughness=0.74)
    cube("Run dark shared base", (0, 0, -0.24), (10.8, 4.1, 0.28), floor)
    # The identical footprints expose the room-module seams beneath distinct biome materials.
    for name, x, mat in (("Moss", -3.25, moss), ("Stone", 0, stone),
                         ("Crystal", 3.25, crystal)):
        cube(f"SM_Run_{name}_Room_Module", (x, 0, 0.01),
             (3.05, 3.5, 0.19), mat, edge=0.028)
        for y in (-1.66, 1.66):
            cube(f"Run {name} side rail {y}", (x, y, 0.28),
                 (3.04, 0.08, 0.43), floor)
    for i, (x, y) in enumerate(((-4.25, 0.9), (-3.42, 1.0), (-2.36, -1.05))):
        cone(f"SM_Run_Moss_Tuft_{i}", (x, y, 0.42), 0.31, 0.72, leaf)
    for i, (x, y) in enumerate(((2.47, 0.85), (3.25, 1.18),
                                (4.24, -0.88))):
        cone(f"SM_Run_Crystal_Spire_{i}", (x, y, 0.62),
             0.32, 1.09, violet)
    # The ability pickup visually matches the gate it unlocks.
    ability = sphere("SM_Run_Dash_Ability_Orb", (-0.83, 0.38, 0.58),
                     0.28, cyan, segments=16, rings=8)
    cylinder("Run ability pedestal", (-0.83, 0.38, 0.19),
             0.42, 0.26, floor, vertices=12)
    if variant == 2:
        key(ability, "scale", ((1, (1, 1, 1)), (29, (1, 1, 1)),
                               (41, (0, 0, 0)), (72, (0, 0, 0))))
    gate_left = cube("SM_Run_Ability_Gate_Left", (1.64, -0.61, 0.77),
                     (0.18, 1.15, 1.32), gate_mat, edge=0.025)
    gate_right = cube("SM_Run_Ability_Gate_Right", (1.64, 0.61, 0.77),
                      (0.18, 1.15, 1.32), gate_mat, edge=0.025)
    cube("Run ability gate header", (1.64, 0, 1.51),
         (0.28, 2.6, 0.19), gate_mat)
    if variant == 2:
        key(gate_left, "location", ((1, (1.64, -0.61, 0.77)),
                                    (38, (1.64, -0.61, 0.77)),
                                    (53, (1.64, -1.70, 0.77)),
                                    (72, (1.64, -1.70, 0.77))))
        key(gate_right, "location", ((1, (1.64, 0.61, 0.77)),
                                     (38, (1.64, 0.61, 0.77)),
                                     (53, (1.64, 1.70, 0.77)),
                                     (72, (1.64, 1.70, 0.77))))
    # Two differently shaped modifier props remain legible from the run overview.
    cylinder("SM_Run_Curse_Modifier_Pedestal", (3.12, -0.98, 0.20),
             0.38, 0.25, floor, vertices=10)
    curse = cone("SM_Run_Curse_Modifier", (3.12, -0.98, 0.61),
                 0.26, 0.58, red)
    cylinder("SM_Run_Shield_Modifier_Pedestal", (4.05, 0.88, 0.20),
             0.38, 0.25, floor, vertices=10)
    shield = sphere("SM_Run_Shield_Modifier", (4.05, 0.88, 0.63),
                    0.27, gold, segments=16, rings=8)
    if variant == 2:
        key(shield, "scale", ((1, (0.55, 0.55, 0.55)),
                               (57, (0.55, 0.55, 0.55)),
                               (72, (1.15, 1.15, 1.15))))
    bpy.ops.object.empty_add(location=(0, 0, 0))
    runner = bpy.context.object
    runner.name = "SM_Run_Traveler_Rig"
    attach(cylinder("SM_Run_Traveler_Body", (-4.45, -0.45, 0.56),
                    0.23, 0.85, runner_mat, vertices=12), runner)
    attach(sphere("Run traveler head", (-4.45, -0.45, 1.14),
                  0.24, runner_mat, segments=16, rings=8), runner)
    attach(cube("Run traveler blue sash", (-4.45, -0.68, 0.62),
                (0.35, 0.07, 0.13), cyan), runner)
    if variant == 2:
        key(runner, "location", ((1, (0, 0, 0)), (29, (3.62, 0.83, 0)),
                                  (39, (3.62, 0.83, 0)),
                                  (53, (5.30, 0.45, 0)),
                                  (72, (8.38, 1.20, 0))))
    else:
        key(runner, "location", ((1, (0, 0, 0)), (72, (0.12, 0, 0))))
    area_light("Run moss green key", (-4.6, -3.2, 7), 1200, 3.8,
               color=(0.52, 1.0, 0.56), target=(-3.2, 0, 0.4))
    area_light("Run crystal magenta key", (4.6, -2.5, 7), 1300, 3.8,
               color=(0.75, 0.45, 1.0), target=(3.2, 0, 0.4))
    cam = camera("Run modular-room overview camera", (8.3, -11.7, 7.8),
                 (0, 0, 0.5), lens=35)
    key(cam, "location", ((1, (8.3, -11.7, 7.8)),
                          (72, (7.6 if variant == 2 else 8.25,
                                -10.9 if variant == 2 else -11.65,
                                7.4 if variant == 2 else 7.75))))
    scene["run_recipe"] = "three equal modules, moss and crystal biomes, cyan ability gate, red curse and gold shield modifiers"
    scene["run_variant"] = variant
    return scene
