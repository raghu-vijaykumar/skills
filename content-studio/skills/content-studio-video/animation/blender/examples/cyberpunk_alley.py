"""Original cyberpunk alley with a luminous courier drone and wet street."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Keep world positions stable when attaching modeled pieces to the flying rig.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored cyberpunk alley candidate")
    scene = reset_scene(spec, background=(0.020, 0.026, 0.055))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.38
    asphalt = material("Alley wet charcoal asphalt", (0.045, 0.055, 0.075),
                       metallic=0.25, roughness=0.23)
    concrete = material("Alley dark concrete", (0.08, 0.105, 0.15), roughness=0.86)
    steel = material("Alley brushed gunmetal", (0.11, 0.14, 0.21), metallic=0.7,
                     roughness=0.45)
    glass = material("Alley cobalt window glass", (0.025, 0.10, 0.21),
                     metallic=0.3, roughness=0.26)
    cyan = material("Alley cyan neon", (0.02, 0.7, 0.9),
                    emission=(0.02, 0.76, 1.0), emission_strength=4.0)
    magenta = material("Alley magenta neon", (0.75, 0.025, 0.55),
                       emission=(1.0, 0.025, 0.56), emission_strength=3.5)
    amber = material("Alley amber parcel beacon", (0.9, 0.28, 0.04),
                     emission=(1, 0.33, 0.02), emission_strength=2.2)

    cube("SM_Cyber_Street", (0, 9, -0.15), (7.5, 45, 0.3), asphalt)
    for side in (-1, 1):
        cube(f"Cyber sidewalk {side}", (side * 4.45, 9, 0.06),
             (1.38, 45, 0.3), concrete)
        for bay in range(6):
            y = -4.0 + 5.0 * bay
            height = 6.8 + ((bay + side) % 3) * 1.45
            building = cube(f"SM_Cyber_Tower_{side}_{bay}",
                            (side * 7.0, y, height / 2),
                            (4.1, 4.6, height), concrete)
            building["cyber_bay"] = bay
            cube(f"Cyber tower glass {side} {bay}",
                 (side * 4.92, y, height * 0.55),
                 (0.04, 3.25, height * 0.55), glass)
            for level in range(3):
                z = 1.5 + level * 1.6
                cube(f"Cyber window rail {side} {bay} {level}",
                     (side * 4.87, y, z), (0.08, 3.5, 0.09),
                     cyan if (bay + level) % 2 == 0 else magenta)
            cube(f"Cyber facade neon spine {side} {bay}",
                 (side * 4.81, y + 1.8, height * 0.57),
                 (0.10, 0.10, height * 0.76),
                 cyan if side == -1 else magenta)
    # A clear pair of railings and a suspended sign identify the transit alley.
    for side in (-1, 1):
        cube(f"Cyber sidewalk edge {side}",
             (side * 3.67, 9, 0.18), (0.10, 45, 0.16), cyan)
    cube("SM_Cyber_Suspended_Sign", (0, 9.7, 5.25),
         (5.8, 0.20, 1.18), steel)
    for i in range(5):
        cube(f"Cyber sign glyph {i}", (-1.75 + i * 0.87, 9.53, 5.25),
             (0.15 + 0.05 * (i % 2), 0.035, 0.58),
             cyan if i % 2 == 0 else magenta)
    for i in range(12):
        cube(f"Cyber wet lane stroke {i}",
             ((i % 3 - 1) * 1.8, -1.5 + i * 2.1, 0.008),
             (0.06, 0.9, 0.012),
             cyan if i % 2 == 0 else magenta)

    bpy.ops.object.empty_add(location=(-3.0, 3.5, 2.8))
    drone = bpy.context.object
    drone.name = "SM_Cyber_Courier_Drone_Rig"
    drone["courier_lane"] = "cyberpunk"
    attach(cube("SM_Cyber_Courier_Drone", (-3.0, 3.5, 2.8),
                (1.45, 0.84, 0.40), steel, edge=0.12), drone)
    attach(cube("Cyber courier parcel", (-3.0, 3.5, 2.35),
                (0.82, 0.70, 0.43), amber, edge=0.04), drone)
    for side in (-1, 1):
        for fore in (-1, 1):
            x = -3.0 + side * 1.10
            y = 3.5 + fore * 0.58
            attach(cube(f"Cyber drone arm {side} {fore}",
                        (x, y, 2.80), (0.93, 0.09, 0.09), steel), drone)
            attach(cylinder(f"Cyber drone rotor {side} {fore}",
                            (x + side * 0.47, y, 2.86), 0.35, 0.035,
                            cyan, vertices=16), drone)
    attach(cube("Cyber drone nose beacon", (-3.0, 3.03, 2.83),
                (0.54, 0.08, 0.10), magenta), drone)
    if variant == 2:
        animate(drone, "location", ((1, (-3.0, 3.5, 2.8)),
                 (24, (-1.8, 3.6, 3.15)), (48, (0.35, 3.8, 3.38)),
                 (72, (2.25, 4.0, 2.95))))
        animate(drone, "rotation_euler", ((1, (0, 0, -0.07)),
                 (48, (0, 0, 0.09)), (72, (0, 0, -0.04))))
    else:
        animate(drone, "location", ((1, (-3.0, 3.5, 2.8)),
                 (72, (-2.35, 3.6, 2.9))))
    area_light("Cyber cyan street wash", (-4.4, 0.5, 7.0), 1450, 7,
               color=(0.16, 0.78, 1.0), target=(0, 6, 1.2))
    area_light("Cyber magenta roof wash", (5.0, 7.0, 8.0), 1250, 7,
               color=(1.0, 0.18, 0.65), target=(0, 6, 2.2))
    area_light("Cyber front drone fill", (0, -5, 5.5), 500, 6,
               color=(0.75, 0.85, 1.0), target=(0, 3.5, 2.8))
    cam = camera("Cyberpunk alley inspection camera", (0.0, -11.4, 4.0),
                 (0, 6.4, 2.4), lens=35)
    animate(cam, "location", ((1, (0.0, -11.4, 4.0)),
             (72, (0.30 if variant == 2 else 0.05,
                   -9.7 if variant == 2 else -11.2, 3.9))))
    scene["cyberpunk_recipe"] = "single cyberpunk lane, wet charcoal street, cyan and magenta neon, courier drone"
    scene["cyberpunk_variant"] = variant
    return scene
