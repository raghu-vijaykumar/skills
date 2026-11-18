"""Original low-distraction card table with one selected card and reward."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Keep card borders and raised icons together when a choice card lifts.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def card(name, x, frame_mat, icon_mat, ink, kind):
    bpy.ops.object.empty_add(location=(0, 0, 0))
    rig = bpy.context.object
    rig.name = name
    attach(cube(name + " border", (x, -0.33, 0.12),
                (1.50, 2.12, 0.10), frame_mat, edge=0.055), rig)
    attach(cube(name + " face", (x, -0.33, 0.181),
                (1.32, 1.94, 0.025), ink, edge=0.035), rig)
    # Small pips are shape cues for a card game, never pretend to be a full UI.
    for y in (-1.10, 0.43):
        attach(sphere(name + f" pip {y}", (x - 0.48, y, 0.218),
                      0.08, icon_mat, segments=12, rings=8), rig)
    if kind == "sword":
        attach(cube(name + " sword blade", (x, -0.34, 0.23),
                    (0.14, 0.87, 0.045), icon_mat), rig)
        attach(cube(name + " sword guard", (x, -0.65, 0.24),
                    (0.61, 0.12, 0.05), icon_mat), rig)
        attach(sphere(name + " sword pommel", (x, -0.94, 0.24),
                      0.13, icon_mat, segments=12, rings=8), rig)
    elif kind == "shield":
        attach(cylinder(name + " shield face", (x, -0.33, 0.24),
                        0.43, 0.055, icon_mat, vertices=6), rig)
        attach(cube(name + " shield crest", (x, -0.33, 0.281),
                    (0.12, 0.52, 0.025), ink), rig)
        attach(cube(name + " shield crossbar", (x, -0.33, 0.285),
                    (0.43, 0.12, 0.025), ink), rig)
    elif kind == "coin":
        attach(cylinder(name + " coin crest", (x, -0.33, 0.24),
                        0.37, 0.06, icon_mat, vertices=24), rig)
        attach(cylinder(name + " coin core", (x, -0.33, 0.28),
                        0.19, 0.03, ink, vertices=18), rig)
    else:
        raise ValueError("Unknown card icon")
    return rig


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown card table candidate")
    scene = reset_scene(spec, background=(0.035, 0.035, 0.055))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.42
    stage = material("Card quiet walnut stage", (0.13, 0.08, 0.10), roughness=0.80)
    felt = material("Card muted aubergine felt", (0.20, 0.13, 0.22), roughness=0.91)
    edge = material("Card edge brass", (0.68, 0.44, 0.18), metallic=0.47,
                    roughness=0.40)
    face = material("Card ink face", (0.055, 0.09, 0.15), roughness=0.72)
    red = material("Card scarlet sword", (0.78, 0.14, 0.20), roughness=0.60)
    cyan = material("Card cyan shield", (0.07, 0.72, 0.87),
                    emission=(0.02, 0.56, 0.72), emission_strength=0.53)
    gold = material("Card golden coin", (0.94, 0.62, 0.14), metallic=0.37,
                    roughness=0.40)
    cube("SM_Card_Table_Stage", (0, 0, -0.26),
         (9.5, 5.6, 0.52), stage, edge=0.13)
    cube("Card quiet felt inset", (0, 0, 0.018),
         (8.82, 4.96, 0.035), felt, edge=0.055)
    # Three differently colored icons read as one hand from the fixed table camera.
    sword = card("SM_Card_Sword_Rig", -2.15, red, red, face, "sword")
    shield = card("SM_Card_Shield_Rig", 0, cyan, cyan, face, "shield")
    coin = card("SM_Card_Coin_Rig", 2.15, gold, gold, face, "coin")
    cube("Card deck stack lower", (-3.70, 1.59, 0.09),
         (1.03, 1.39, 0.15), edge, edge=0.035)
    cube("Card deck stack top", (-3.70, 1.59, 0.19),
         (1.03, 1.39, 0.08), face, edge=0.025)
    for i in range(5):
        reward = cylinder(f"SM_Card_Reward_Coin_{i}",
                          (3.54, 1.35, 0.13 + i * 0.12),
                          0.38, 0.10, gold, vertices=24)
        if i >= 2:
            reward.scale = (0.01, 0.01, 0.01)
            if variant == 2:
                key(reward, "scale", ((1, (0.01, 0.01, 0.01)),
                                       (42 + (i - 2) * 5, (0.01, 0.01, 0.01)),
                                       (54 + (i - 2) * 5, (1, 1, 1)),
                                       (72, (1, 1, 1))))
    if variant == 2:
        # One selected card rises without covering the two remaining choices.
        key(shield, "location", ((1, (0, 0, 0)),
                                  (28, (0, 0, 0)),
                                  (47, (0, 0.56, 0.62)),
                                  (72, (0, 0.56, 0.62))))
        key(shield, "scale", ((1, (1, 1, 1)),
                               (47, (1.10, 1.10, 1.10)),
                               (72, (1.10, 1.10, 1.10))))
    area_light("Card warm left key", (-3.3, -3.1, 6.8), 1050, 4.8,
               color=(1.0, 0.72, 0.48), target=(0, 0, 0))
    area_light("Card cyan right fill", (3.3, 1.9, 5.8), 630, 4.4,
               color=(0.47, 0.76, 1.0), target=(0, 0, 0))
    cam = camera("Card table overview camera", (0, -6.9, 7.4),
                 (0, 0, 0.05), ortho=9.8)
    scene["card_recipe"] = "three readable 3D icons on quiet table, one lifted choice, reward coin stack"
    scene["card_variant"] = variant
    return scene
