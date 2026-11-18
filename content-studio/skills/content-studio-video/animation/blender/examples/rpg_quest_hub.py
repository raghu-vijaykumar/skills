"""Original RPG quest hub with two regions, class gear, and rarity-coded loot."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Preserve the designed quest-marker and chest positions under animated pivots.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def empty(name, location=(0, 0, 0)):
    bpy.ops.object.empty_add(location=location)
    obj = bpy.context.object
    obj.name = name
    return obj


def cone(name, location, radius, depth, mat, vertices=8):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                    radius2=0, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def figure(name, x, y, coat, dark, face):
    cube(f"SM_RPG_{name}_Body", (x, y, 1.12),
         (0.66, 0.42, 1.10), coat, edge=0.04)
    sphere(f"RPG {name} head", (x, y, 1.92), 0.29, face,
           segments=16, rings=8)
    for side in (-1, 1):
        cube(f"RPG {name} boot {side}", (x + side * 0.18, y, 0.32),
             (0.20, 0.26, 0.64), dark)
        cube(f"RPG {name} arm {side}", (x + side * 0.45, y, 1.14),
             (0.18, 0.25, 0.74), coat)


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown RPG quest hub candidate")
    scene = reset_scene(spec, background=(0.12, 0.19, 0.25))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    stone = material("RPG warm hub stone", (0.42, 0.36, 0.29), roughness=0.88)
    green = material("RPG moss-green forest region", (0.15, 0.38, 0.23), roughness=0.96)
    ochre = material("RPG ochre highland region", (0.58, 0.27, 0.16), roughness=0.93)
    wood = material("RPG dark quest-board timber", (0.15, 0.095, 0.075), roughness=0.78)
    gold = material("RPG quest gold", (0.96, 0.63, 0.14),
                    emission=(0.93, 0.43, 0.06), emission_strength=0.95)
    steel = material("RPG common steel", (0.46, 0.51, 0.54), metallic=0.43,
                     roughness=0.55)
    blue = material("RPG rare cobalt", (0.10, 0.38, 0.88),
                    emission=(0.05, 0.23, 0.69), emission_strength=0.65)
    violet = material("RPG epic violet", (0.59, 0.22, 0.82),
                      emission=(0.54, 0.13, 0.88), emission_strength=1.75)
    dark = material("RPG charcoal leather", (0.05, 0.06, 0.09), roughness=0.75)
    face = material("RPG stylized skin", (0.72, 0.49, 0.32), roughness=0.9)
    # Split terrain and landmarks establish two regions without copying a game world.
    cylinder("SM_RPG_Quest_Hub_Base", (0, 0, -0.25), 7.4, 0.54,
             stone, vertices=12)
    cube("SM_RPG_Forest_Region", (-3.72, 0.25, 0.055),
         (6.3, 8.5, 0.08), green)
    cube("SM_RPG_Highland_Region", (3.72, 0.25, 0.055),
         (6.3, 8.5, 0.08), ochre)
    cube("RPG central guild path", (0, -0.15, 0.12),
         (2.15, 9.5, 0.16), stone)
    for i, (x, y) in enumerate(((-5.5, 1.6), (-4.8, 3.0), (-3.8, 2.1))):
        cylinder(f"RPG forest trunk {i}", (x, y, 0.62), 0.12, 1.1,
                 wood, vertices=8)
        cone(f"RPG forest pine {i}", (x, y, 1.58), 0.65, 1.72, green)
    for i, (x, y) in enumerate(((4.3, 2.8), (5.6, 1.4), (4.8, -0.2))):
        cube(f"RPG highland standing stone {i}", (x, y, 0.83),
             (0.36, 0.42, 1.66), stone, edge=0.025)
        cube(f"RPG highland ochre rune {i}", (x, y - 0.223, 1.2),
             (0.10, 0.016, 0.35), gold)
    cube("SM_RPG_Guild_Quest_Board", (0, 2.35, 1.65),
         (2.58, 0.32, 2.55), wood, edge=0.045)
    cube("RPG board parchment panel", (0, 2.16, 1.70),
         (1.88, 0.025, 1.62), stone)
    for side in (-1, 1):
        cube(f"RPG board notice pin {side}", (side * 0.65, 2.137, 2.20),
             (0.11, 0.02, 0.11), gold)
    cube("RPG guild roof", (0, 2.35, 3.15),
         (3.15, 0.90, 0.34), wood, edge=0.035)
    marker = empty("SM_RPG_Quest_Marker_Rig")
    attach(cube("SM_RPG_Quest_Exclamation", (0, 2.02, 3.95),
                (0.19, 0.14, 0.75), gold, edge=0.04), marker)
    attach(sphere("RPG quest exclamation dot", (0, 2.02, 3.43),
                  0.11, gold, segments=12, rings=6), marker)
    if variant == 2:
        animate(marker, "location", ((1, (0, 0, 0)), (28, (0, 0, 0)),
                                     (45, (0, 0, 0.38)),
                                     (72, (0, 0, 0.26))))
    else:
        animate(marker, "location", ((1, (0, 0, 0)),
                                     (72, (0, 0, 0.03))))
    figure("Warrior", -3.15, -0.35, blue, dark, face)
    cube("SM_RPG_Warrior_Sword", (-2.52, -0.35, 1.75),
         (0.13, 0.14, 2.0), steel, edge=0.018)
    cube("RPG warrior sword crossguard", (-2.52, -0.35, 1.10),
         (0.51, 0.18, 0.12), gold)
    cylinder("SM_RPG_Warrior_Shield", (-3.92, -0.65, 1.12),
             0.54, 0.13, steel, vertices=8, rotation=(1.57, 0, 0))
    figure("Mage", 3.10, -0.35, violet, dark, face)
    cone("SM_RPG_Mage_Hat", (3.10, -0.35, 2.36),
         0.55, 0.83, violet, vertices=12)
    cylinder("SM_RPG_Mage_Staff", (3.76, -0.35, 1.55),
             0.065, 2.65, wood, vertices=8)
    sphere("RPG mage staff gem", (3.76, -0.35, 2.96),
           0.17, violet, segments=12, rings=6)
    # Three isolated loot colors form the common / rare / epic rarity read.
    cube("SM_RPG_Common_Loot_Pedestal", (-2.0, -2.55, 0.29),
         (0.90, 0.82, 0.55), steel, edge=0.025)
    cube("SM_RPG_Epic_Loot_Pedestal", (2.0, -2.55, 0.29),
         (0.90, 0.82, 0.55), violet, edge=0.025)
    cube("SM_RPG_Rare_Chest", (0, -2.55, 0.48),
         (1.43, 1.03, 0.91), blue, edge=0.06)
    cube("RPG rare chest clasp", (0, -3.085, 0.62),
         (0.24, 0.022, 0.28), gold)
    lid_rig = empty("SM_RPG_Rare_Chest_Lid_Rig", (0, -2.08, 0.92))
    attach(cube("SM_RPG_Rare_Chest_Lid", (0, -2.55, 0.97),
                (1.47, 1.08, 0.20), blue, edge=0.035), lid_rig)
    attach(cube("RPG rare lid gold band", (0, -2.55, 1.082),
                (0.16, 1.08, 0.024), gold), lid_rig)
    gem = sphere("SM_RPG_Rare_Loot_Gem", (0, -2.55, 1.22),
                 0.31, violet, segments=12, rings=6)
    gem.scale = (0, 0, 0)
    if variant == 2:
        animate(lid_rig, "rotation_euler", ((1, (0, 0, 0)),
                                            (39, (0, 0, 0)),
                                            (59, (-1.15, 0, 0)),
                                            (72, (-1.15, 0, 0))))
        animate(gem, "scale", ((1, (0, 0, 0)), (54, (0, 0, 0)),
                                (72, (1, 1, 1))))
        animate(gem, "location", ((1, (0, -2.55, 1.22)),
                                   (54, (0, -2.55, 1.22)),
                                   (72, (0, -2.55, 1.90))))
    else:
        animate(lid_rig, "rotation_euler", ((1, (0, 0, 0)),
                                            (72, (-0.08, 0, 0))))
    area_light("RPG warm guild key", (-5.5, -4.0, 10), 2300, 5,
               color=(1.0, 0.82, 0.62), target=(0, 0, 1))
    area_light("RPG cool rarity fill", (5.5, -3.0, 7), 900, 5,
               color=(0.61, 0.75, 1.0), target=(0, -1, 1))
    cam = camera("RPG quest hub camera", (8.4, -12.0, 8.3),
                 (0, 0.05, 1.55), lens=38)
    animate(cam, "location", ((1, (8.4, -12.0, 8.3)),
             (72, (7.4 if variant == 2 else 8.35,
                   -10.8 if variant == 2 else -11.95,
                   7.7 if variant == 2 else 8.25))))
    scene["rpg_recipe"] = "split-region quest hub, class-readable warrior and mage gear, common rare epic loot colors, rising quest marker"
    scene["rpg_variant"] = variant
    return scene
