"""Original ruined causeway with a bonfire, fog gate, and revealed adversary."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Keep weapons and armor in silhouette as the traveler or enemy rig moves.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def rig(name):
    bpy.ops.object.empty_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    return obj


def cone(name, location, radius, depth, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=radius,
                                    radius2=0, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown soulslike candidate")
    scene = reset_scene(spec, background=(0.055, 0.065, 0.085))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.32
    stone = material("Soulslike weathered ash stone", (0.11, 0.14, 0.17), roughness=0.94)
    pale = material("Soulslike worn edge stone", (0.22, 0.26, 0.28), roughness=0.92)
    dark = material("Soulslike charcoal chasm", (0.03, 0.045, 0.065), roughness=0.94)
    bone = material("Soulslike traveler pale armor", (0.53, 0.50, 0.43), roughness=0.68)
    red = material("Soulslike lethal red silhouette", (0.45, 0.025, 0.035),
                   emission=(0.62, 0.02, 0.035), emission_strength=0.9)
    ember = material("Soulslike bonfire ember", (0.85, 0.28, 0.03),
                     emission=(0.95, 0.25, 0.01), emission_strength=1.4)
    fog = material("Soulslike pale fog curtain", (0.52, 0.70, 0.75),
                   emission=(0.38, 0.65, 0.75), emission_strength=0.7)
    cube("Soulslike abyss plinth", (0, 0, -0.80), (11.6, 6.8, 0.25), dark)
    cube("SM_Soulslike_Ruined_Causeway", (0, 0, -0.19),
         (10.0, 3.65, 0.38), stone, edge=0.08)
    for i in range(6):
        x = -4.3 + i * 1.68
        cube(f"Soulslike path seam {i}", (x, -0.08, 0.025),
             (0.055, 3.42, 0.035), pale)
    for x in (-4.65, -1.2, 2.4, 4.55):
        for y in (-1.91, 1.91):
            cube(f"Soulslike parapet post {x} {y}", (x, y, 0.73),
                 (0.38, 0.42, 1.45), stone, edge=0.045)
    # Uneven heights and broken caps make the ruin monumental without hiding the route.
    for i, (x, y, height) in enumerate(((-3.60, 2.90, 3.45),
                                         (-0.60, 2.90, 4.15),
                                         (3.80, 2.90, 3.70))):
        cylinder(f"SM_Soulslike_Broken_Column_{i}", (x, y, height / 2 - 0.07),
                 0.43, height, stone, vertices=10)
        cube(f"Soulslike column broken cap {i}",
             (x, y, height - 0.13), (1.02, 1.02, 0.20), pale, edge=0.035)
    # The bonfire stays visible as the safe navigation landmark.
    cylinder("SM_Soulslike_Bonfire_Hearth", (-3.10, -0.86, 0.13),
             0.56, 0.23, dark, vertices=10)
    for i in range(3):
        cube(f"Soulslike bonfire wood {i}", (-3.10, -0.86, 0.31 + i * 0.07),
             (0.78, 0.13, 0.12), stone)
    flame = cone("SM_Soulslike_Bonfire_Flame", (-3.10, -0.86, 0.94),
                 0.37, 1.02, ember)
    if variant == 2:
        key(flame, "scale", ((1, (0.86, 0.86, 0.86)),
                              (22, (1.02, 1.02, 1.08)),
                              (47, (0.82, 0.82, 0.87)),
                              (72, (1.04, 1.04, 1.10))))
    # The gate's pale panels part later so the red threat can be read behind them.
    for y in (-1.48, 1.48):
        cube(f"Soulslike fog arch upright {y}", (2.15, y, 1.77),
             (0.65, 0.54, 3.55), pale, edge=0.05)
    cube("SM_Soulslike_Monumental_Fog_Arch", (2.15, 0, 3.72),
         (0.78, 3.60, 0.46), pale, edge=0.055)
    curtain_left = cube("SM_Soulslike_Fog_Gate_Left", (2.15, -0.71, 1.62),
                        (0.16, 1.38, 2.86), fog)
    curtain_right = cube("SM_Soulslike_Fog_Gate_Right", (2.15, 0.71, 1.62),
                         (0.16, 1.38, 2.86), fog)
    if variant == 2:
        key(curtain_left, "location", ((1, (2.15, -0.71, 1.62)),
                                       (40, (2.15, -0.71, 1.62)),
                                       (63, (2.15, -1.55, 1.62)),
                                       (72, (2.15, -1.55, 1.62))))
        key(curtain_right, "location", ((1, (2.15, 0.71, 1.62)),
                                        (40, (2.15, 0.71, 1.62)),
                                        (63, (2.15, 1.55, 1.62)),
                                        (72, (2.15, 1.55, 1.62))))
    hero = rig("SM_Soulslike_Traveler_Rig")
    attach(cylinder("SM_Soulslike_Traveler_Body", (-4.35, 0.67, 0.73),
                    0.20, 1.00, bone, vertices=12), hero)
    attach(sphere("Soulslike traveler head", (-4.35, 0.67, 1.45),
                  0.22, bone, segments=16, rings=8), hero)
    attach(cube("Soulslike traveler cloak", (-4.35, 0.93, 0.69),
                (0.44, 0.13, 1.03), dark), hero)
    attach(cube("Soulslike traveler sword", (-4.04, 0.67, 0.83),
                (0.10, 0.12, 1.25), pale), hero)
    if variant == 2:
        key(hero, "location", ((1, (0, 0, 0)), (24, (1.30, 0, 0)),
                                (42, (1.30, 0, 0)), (72, (4.63, 0, 0))))
    else:
        key(hero, "location", ((1, (0, 0, 0)), (72, (0.11, 0, 0))))
    enemy = rig("SM_Soulslike_Red_Enemy_Rig")
    attach(cylinder("SM_Soulslike_Red_Enemy_Torso", (2.67, -0.25, 1.25),
                    0.41, 1.62, red, vertices=12), enemy)
    attach(sphere("Soulslike enemy head", (2.67, -0.25, 2.37),
                  0.40, red, segments=16, rings=8), enemy)
    for side in (-1, 1):
        attach(cube(f"Soulslike enemy shoulder {side}",
                    (2.67 + side * 0.56, -0.25, 1.89),
                    (0.60, 0.30, 0.34), red), enemy)
    attach(cube("SM_Soulslike_Red_Enemy_Blade", (2.37, -0.76, 1.84),
                (0.13, 0.18, 2.35), red), enemy)
    if variant == 2:
        key(enemy, "scale", ((1, (0, 0, 0)), (45, (0, 0, 0)),
                              (65, (1, 1, 1)), (72, (1, 1, 1))))
        key(enemy, "location", ((1, (0, 0, -0.10)),
                                 (49, (0, 0, -0.10)),
                                 (72, (-0.28, 0, 0.15))))
    else:
        enemy.scale = (0, 0, 0)
    area_light("Soulslike cold ruin skylight", (0.2, -3.3, 8.7), 950, 5.8,
               color=(0.47, 0.68, 1.0), target=(0, 0, 1.3))
    area_light("Soulslike ember key", (-3.6, -2.4, 4.3), 820, 2.8,
               color=(1.0, 0.54, 0.19), target=(-3.0, -0.7, 1.1))
    cam = camera("Soulslike ruined-causeway camera", (-8.8, -11.5, 7.2),
                 (0, 0, 1.17), lens=37)
    key(cam, "location", ((1, (-8.8, -11.5, 7.2)),
                          (72, (-7.8 if variant == 2 else -8.75,
                                -10.7 if variant == 2 else -11.45,
                                6.9 if variant == 2 else 7.17))))
    scene["soulslike_recipe"] = "weathered monumental ruin, warm bonfire landmark, pale fog gate, clear crimson enemy silhouette"
    scene["soulslike_variant"] = variant
    return scene
