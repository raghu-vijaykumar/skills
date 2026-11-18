"""Original traversable biome diorama with a bridge, landmark, and discovery cue."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, rig):
    # Keep the traveler's silhouette together while it crosses a biome border.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.matrix_world = world


def pine(name, x, y, trunk, needles):
    cylinder(name + " trunk", (x, y, 0.29), 0.09, 0.55, trunk, vertices=8)
    bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=0.36,
                                    radius2=0, depth=0.91,
                                    location=(x, y, 0.83))
    obj = bpy.context.object
    obj.name = name + " crown"
    obj.data.materials.append(needles)


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown open-world crossing candidate")
    scene = reset_scene(spec, background=(0.055, 0.08, 0.10))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.62
    bedrock = material("Crossing basalt plinth", (0.10, 0.12, 0.14), roughness=0.93)
    meadow = material("Crossing green meadow", (0.20, 0.43, 0.26), roughness=0.91)
    sand = material("Crossing ochre badlands", (0.59, 0.37, 0.20), roughness=0.94)
    path = material("Crossing pale footpath", (0.62, 0.57, 0.39), roughness=0.97)
    water = material("Crossing cobalt river", (0.07, 0.36, 0.65), roughness=0.42)
    timber = material("Crossing bridge timber", (0.33, 0.20, 0.11), roughness=0.86)
    fir = material("Crossing deep fir", (0.07, 0.29, 0.17), roughness=0.82)
    stone = material("Crossing warm ruin stone", (0.43, 0.40, 0.35), roughness=0.94)
    cyan = material("Crossing guide beacon", (0.07, 0.77, 0.95),
                    emission=(0.04, 0.67, 0.88), emission_strength=1.4)
    gold = material("Crossing discovery gold", (0.95, 0.59, 0.14), metallic=0.34)
    traveler_mat = material("Crossing blue traveler", (0.12, 0.42, 0.86), roughness=0.66)
    cube("SM_Crossing_World_Stage", (0, 0, -0.30),
         (12.7, 7.8, 0.58), bedrock, edge=0.11)
    # The hard color border and water channel identify the two biomes at overview scale.
    cube("SM_Crossing_Meadow_Biome", (-3.13, 0, 0.01),
         (6.05, 7.31, 0.07), meadow)
    cube("SM_Crossing_Badlands_Biome", (3.13, 0, 0.01),
         (6.05, 7.31, 0.07), sand)
    cube("SM_Crossing_River", (0, 0, 0.005),
         (0.69, 7.31, 0.05), water)
    cube("Crossing meadow path", (-3.16, -1.30, 0.065),
         (5.77, 0.62, 0.045), path)
    cube("Crossing badlands path", (3.16, -1.30, 0.065),
         (5.77, 0.62, 0.045), path)
    bridge = cube("SM_Crossing_Bridge_Deck", (0, -1.30, 0.16),
                  (1.28, 0.78, 0.14), timber, edge=0.02)
    for x in (-0.55, 0.55):
        for y in (-1.72, -0.88):
            cube(f"Crossing bridge post {x} {y}", (x, y, 0.45),
                 (0.11, 0.11, 0.63), timber)
        cube(f"Crossing bridge rail {x}", (x, -1.30, 0.65),
             (0.08, 1.10, 0.08), timber)
    for i, (x, y) in enumerate(((-4.70, 2.15), (-3.52, 2.52),
                                 (-2.13, 1.81), (-4.74, -2.43),
                                 (-2.20, -2.71))):
        pine(f"Crossing pine {i}", x, y, timber, fir)
    for i, (x, y) in enumerate(((2.30, 2.04), (4.85, 2.36),
                                 (3.86, -2.57), (1.65, -2.48))):
        sphere(f"Crossing red rock {i}", (x, y, 0.15), 0.27 + i * 0.025,
               stone, segments=8, rings=6, scale=(1.4, 0.8, 0.7))
    # A tower above the destination remains the navigation landmark throughout the shot.
    tower = cylinder("SM_Crossing_Landmark_Tower", (4.05, 1.12, 1.16),
                     0.52, 2.24, stone, vertices=8)
    cube("Crossing tower crown", (4.05, 1.12, 2.33),
         (1.30, 1.30, 0.23), bedrock, edge=0.04)
    beacon = sphere("SM_Crossing_Landmark_Beacon", (4.05, 1.12, 2.62),
                    0.25, cyan, segments=16, rings=10)
    if variant == 2:
        key(beacon, "scale", ((1, (0.55, 0.55, 0.55)),
                               (49, (0.55, 0.55, 0.55)),
                               (65, (1.35, 1.35, 1.35)),
                               (72, (1.35, 1.35, 1.35))))
    # Three spaced finds suggest exploration without obscuring the travel corridor.
    for i, (x, y) in enumerate(((1.41, -0.18), (2.59, 0.39), (3.18, 1.08))):
        sphere(f"SM_Crossing_Discovery_Crumb_{i}", (x, y, 0.19),
               0.15, gold, segments=12, rings=8)
    cube("SM_Crossing_Discovery_Cache", (2.75, -2.27, 0.20),
         (0.75, 0.55, 0.37), timber, edge=0.045)
    cube("Crossing cache lid", (2.75, -2.27, 0.43),
         (0.83, 0.63, 0.09), gold, edge=0.025)
    bpy.ops.object.empty_add(location=(-4.65, -1.30, 0))
    traveler = bpy.context.object
    traveler.name = "SM_Crossing_Traveler_Rig"
    for part in (
        cylinder("Crossing traveler body", (-4.65, -1.30, 0.39),
                 0.17, 0.52, traveler_mat, vertices=10),
        sphere("Crossing traveler head", (-4.65, -1.30, 0.76),
               0.19, gold, segments=12, rings=8),
        cube("Crossing traveler pack", (-4.65, -1.07, 0.40),
             (0.43, 0.18, 0.40), timber, edge=0.04),
    ):
        attach(part, traveler)
    if variant == 2:
        key(traveler, "location", ((1, (-4.65, -1.30, 0)),
                                    (22, (-2.00, -1.30, 0)),
                                    (40, (0.09, -1.30, 0)),
                                    (63, (2.53, -1.30, 0)),
                                    (72, (2.53, -1.30, 0))))
    area_light("Crossing warm exploration key", (-4.5, -4.5, 8), 1450, 6,
               color=(1.0, 0.82, 0.62), target=(0, 0, 0.4))
    area_light("Crossing cool landmark fill", (5.0, 3.0, 7), 840, 5,
               color=(0.58, 0.82, 1.0), target=(3.5, 1.0, 1.0))
    camera("Crossing overview camera", (0, -9.8, 10.6),
           (0, 0, 0.34), ortho=13.55)
    scene["crossing_recipe"] = "two biomes, bridged river, tall landmark, traversing explorer, sparse discovery"
    scene["crossing_variant"] = variant
    return scene
