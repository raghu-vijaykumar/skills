"""Original survival shelter with readable resources and an unsafe salvage lane."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # The salvage load stays assembled while its cart crosses the safety line.
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
        raise ValueError("Unknown survival shelter candidate")
    scene = reset_scene(spec, background=(0.055, 0.09, 0.13))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.43
    ground = material("Survival shelter earth", (0.31, 0.28, 0.23), roughness=0.96)
    safe = material("Survival warm refuge circle", (0.50, 0.34, 0.19), roughness=0.92)
    unsafe = material("Survival cold hazard stone", (0.11, 0.19, 0.24), roughness=0.92)
    wood = material("Survival gathered wood", (0.43, 0.20, 0.095), roughness=0.85)
    steel = material("Survival salvage steel", (0.39, 0.48, 0.52),
                     metallic=0.44, roughness=0.60)
    water = material("Survival clean water blue", (0.06, 0.53, 0.82),
                     roughness=0.27)
    ember = material("Survival crafted amber beacon", (0.90, 0.33, 0.04),
                     emission=(0.95, 0.23, 0.02), emission_strength=1.25)
    hazard = material("Survival unsafe red signal", (0.79, 0.075, 0.07),
                      emission=(0.92, 0.025, 0.02), emission_strength=2.4)
    dark = material("Survival dark shelter leather", (0.05, 0.07, 0.07),
                    roughness=0.82)
    cylinder("SM_Survival_Refuge_Base", (0, 0, -0.30), 7.35,
             0.55, ground, vertices=12)
    cube("SM_Survival_Safe_Zone", (-3.28, 0, 0.015),
         (6.48, 10.6, 0.07), safe)
    cube("SM_Survival_Unsafe_Zone", (3.28, 0, 0.015),
         (6.48, 10.6, 0.07), unsafe)
    cube("SM_Survival_Safety_Boundary", (0, 0, 0.06),
         (0.09, 10.6, 0.05), ember)
    for y in (-3.8, 3.8):
        cube(f"Survival boundary post {y}", (0, y, 0.64),
             (0.21, 0.24, 1.27), steel)
        cube(f"Survival boundary stripe {y}", (0, y - 0.13, 1.0),
             (0.22, 0.02, 0.19), ember)
    # A large work surface makes the crafting location unmistakable.
    cube("SM_Survival_Iconic_Crafting_Bench", (-2.75, 1.22, 1.10),
         (3.45, 1.28, 0.22), wood, edge=0.055)
    for x in (-4.17, -1.33):
        for y in (0.77, 1.67):
            cube(f"Survival bench leg {x} {y}", (x, y, 0.52),
                 (0.23, 0.23, 1.04), wood)
    cube("Survival bench back rail", (-2.75, 1.86, 1.40),
         (3.43, 0.15, 0.45), wood)
    cube("Survival bench hammer handle", (-1.50, 1.03, 1.35),
         (0.11, 0.65, 0.11), wood)
    cube("Survival bench hammer head", (-1.50, 0.72, 1.39),
         (0.51, 0.12, 0.18), steel)
    for i in range(3):
        cylinder(f"SM_Survival_Wood_Log_{i}",
                 (-3.74 + i * 0.30, 0.93, 1.35), 0.10, 0.74,
                 wood, vertices=10, rotation=(math.pi / 2, 0, 0))
    cylinder("SM_Survival_Water_Canteen", (-2.74, 0.92, 1.51),
             0.22, 0.63, water, vertices=12)
    cylinder("Survival canteen cap", (-2.74, 0.92, 1.85),
             0.12, 0.10, steel, vertices=12)
    for i in range(2):
        cube(f"SM_Survival_Steel_Scrap_{i}",
             (-2.12 + i * 0.27, 1.01, 1.35),
             (0.24, 0.55, 0.18), steel)
    # A parked cart returns salvage from the cold side before a beacon ignites.
    cart = empty("SM_Survival_Salvage_Cart_Rig")
    attach(cube("SM_Survival_Salvage_Cart", (3.16, -1.82, 0.37),
                (1.75, 1.28, 0.32), steel, edge=0.04), cart)
    attach(cube("Survival cart resource crate", (3.16, -1.82, 0.93),
                (1.20, 0.94, 0.78), wood, edge=0.045), cart)
    for x in (2.46, 3.86):
        for y in (-2.28, -1.36):
            attach(cylinder(f"Survival cart wheel {x} {y}",
                            (x, y, 0.20), 0.24, 0.13, dark,
                            vertices=12, rotation=(math.pi / 2, 0, 0)), cart)
    if variant == 2:
        animate(cart, "location", ((1, (0, 0, 0)), (18, (0, 0, 0)),
                                   (52, (-3.40, 0, 0)), (72, (-3.40, 0, 0))))
    else:
        animate(cart, "location", ((1, (0, 0, 0)), (72, (-0.12, 0, 0))))
    cylinder("SM_Survival_Campfire_Hearth", (-4.10, -1.92, 0.16),
             0.75, 0.25, dark, vertices=10)
    for i in range(4):
        cube(f"Survival campfire gathered stick {i}",
             (-4.10, -1.92, 0.36 + i * 0.06),
             (1.02, 0.12, 0.12), wood)
    flame = cone("SM_Survival_Crafted_Fire", (-4.10, -1.92, 0.86),
                 0.43, 1.05, ember)
    if variant == 2:
        animate(flame, "scale", ((1, (0, 0, 0)), (50, (0, 0, 0)),
                                 (64, (1, 1, 1)),
                                 (72, (0.88, 0.88, 0.92))))
    else:
        flame.scale = (0, 0, 0)
    for i, (x, y) in enumerate(((3.2, 2.7), (5.3, 1.0), (4.35, -3.4))):
        cube(f"Survival unsafe spike {i}", (x, y, 0.83),
             (0.31, 0.32, 1.65), dark)
        cube(f"Survival spike red tip {i}", (x, y, 1.70),
             (0.33, 0.34, 0.14), hazard)
    watcher = empty("SM_Survival_Hazard_Watcher_Rig")
    attach(sphere("SM_Survival_Hazard_Eye", (4.50, 2.05, 1.57),
                  0.30, hazard, segments=16, rings=8), watcher)
    if variant == 2:
        animate(watcher, "location", ((1, (0, 0, 0)), (52, (0, 0, 0)),
                                      (72, (0.85, 0.50, 0.12))))
    else:
        animate(watcher, "location", ((1, (0, 0, 0)), (72, (0.05, 0, 0))))
    area_light("Survival warm refuge key", (-5.0, -4.5, 8.0), 2000, 4.5,
               color=(1.0, 0.69, 0.39), target=(-2.5, 0, 1))
    area_light("Survival cold hazard fill", (5.5, -1.0, 7.5), 1050, 5.5,
               color=(0.42, 0.68, 1.0), target=(2.5, 0, 1))
    cam = camera("Survival safe-unsafe overview camera", (9.0, -11.8, 8.7),
                 (0, 0, 1.0), lens=35)
    animate(cam, "location", ((1, (9.0, -11.8, 8.7)),
             (72, (8.0 if variant == 2 else 8.95,
                   -10.7 if variant == 2 else -11.75,
                   8.2 if variant == 2 else 8.65))))
    scene["survival_recipe"] = "warm safe refuge, cold unsafe salvage, iconic crafting bench, wood water steel, returning cart and crafted fire"
    scene["survival_variant"] = variant
    return scene
