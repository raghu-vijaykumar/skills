"""Original sunlit village rite with a wicker effigy and repeating field symbols."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def torus(name, location, major, minor, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored folk horror candidate")
    scene = reset_scene(spec, background=(0.36, 0.48, 0.40))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
    grass = material("Rite sunlit dry field", (0.29, 0.35, 0.16), roughness=1)
    path = material("Rite beaten earth", (0.43, 0.32, 0.20), roughness=1)
    wicker = material("Rite honey straw", (0.55, 0.35, 0.13), roughness=0.97)
    dark = material("Rite charred reed", (0.12, 0.10, 0.065), roughness=1)
    chalk = material("Rite chalk-painted wood", (0.68, 0.62, 0.42), roughness=0.92)
    crimson = material("Rite crimson offering cloth", (0.41, 0.035, 0.035), roughness=0.84)
    stone = material("Rite lichen standing stone", (0.34, 0.38, 0.28), roughness=1)
    sky = material("Rite far pale hills", (0.39, 0.43, 0.31), roughness=1)

    cube("SM_Rite_Field", (0, 0, -0.30), (80, 80, 0.5), grass)
    # A beautiful open field carries a handmade symbol that is too large for its village.
    cylinder("Rite beaten-earth circle", (0, 1.6, -0.035), 4.6, 0.035,
             path, vertices=64)
    for i in range(10):
        a = 2 * math.pi * i / 10
        x, y = 3.65 * math.sin(a), 1.6 + 3.65 * math.cos(a)
        ob = cylinder(f"SM_Rite_Standing_Stone_{i}", (x, y, 0.52), 0.27,
                      1.03 + (i % 3) * 0.16, stone, vertices=7,
                      rotation=(0.11 * (-1) ** i, 0.08, a))
        ob["symbol_index"] = i
        cube(f"Rite painted stone mark {i}", (x, y - 0.25, 0.70),
             (0.09, 0.018, 0.34), chalk)
    cylinder("SM_Rite_Wicker_Spine", (0, 1.58, 2.32), 0.18, 4.6,
             dark, vertices=9)
    cube("Rite woven torso", (0, 1.57, 2.25), (1.08, 0.43, 1.72), wicker,
         edge=0.06)
    for i in range(11):
        z = 1.47 + i * 0.15
        cube(f"Rite torso weave {i}", (0, 1.32, z),
             (1.2, 0.045, 0.045), dark)
    for side in (-1, 1):
        arm = cube(f"Rite outstretched reed arm {side}", (side * 0.96, 1.57, 2.82),
                   (1.35, 0.17, 0.15), dark)
        arm.rotation_euler[1] = side * -0.22
        cube(f"Rite forked twig {side}", (side * 1.60, 1.55, 3.13),
             (0.10, 0.13, 0.80), wicker)
    head = torus("SM_Rite_Wicker_Sun_Disk", (0, 1.52, 3.64), 0.68, 0.12,
                 wicker, rotation=(math.pi / 2, 0, 0))
    head["wicker_hero"] = True
    cylinder("Rite sun disk center", (0, 1.48, 3.64), 0.42, 0.08,
             dark, vertices=12, rotation=(math.pi / 2, 0, 0))
    for i in range(8):
        a = i * 2 * math.pi / 8
        ray = cube(f"Rite sun ray {i}", (0.93 * math.sin(a), 1.49,
                   3.64 + 0.93 * math.cos(a)), (0.11, 0.12, 0.47), wicker)
        ray.rotation_euler[1] = a
    for i in range(12):
        a = i * 2 * math.pi / 12
        fiber = cube(f"Rite uneven sun binding {i}",
                     (0.68 * math.sin(a), 1.37, 3.64 + 0.68 * math.cos(a)),
                     (0.045, 0.045, 0.27), dark)
        fiber.rotation_euler[1] = a + 0.55
    # The repeated red scraps become the animated cue, as if the field is breathing.
    ribbons = []
    for i in range(6):
        a = 2 * math.pi * i / 6
        x, y = 2.60 * math.sin(a), 1.6 + 2.60 * math.cos(a)
        stake = cylinder(f"Rite offering stake {i}", (x, y, 0.75), 0.07,
                         1.6, dark, vertices=7)
        stake["offering_index"] = i
        cloth = cube(f"SM_Rite_Red_Ribbon_{i}", (x + 0.25, y, 1.26),
                     (0.65, 0.055, 0.11), crimson)
        cloth.rotation_euler[2] = a
        ribbons.append(cloth)
        if variant == 2:
            animate(cloth, "rotation_euler", ((1, (0, 0, a - 0.16)),
                       (24, (0, 0, a + 0.24)), (48, (0, 0, a - 0.22)),
                       (72, (0, 0, a + 0.18))))
    for i in range(44):
        a = i * 2.39996
        r = 5.6 + (i % 8) * 0.6
        x, y = r * math.sin(a), 1.6 + r * math.cos(a)
        tuft = cube(f"Rite dry grass tuft {i}", (x, y, 0.17),
                    (0.045, 0.05, 0.34 + (i % 3) * 0.12), wicker)
        tuft.rotation_euler[1] = 0.17 * (-1) ** i
    for i, x in enumerate((-12, -7.4, 8.0, 12.3)):
        y = 11 + (i % 2) * 2.2
        cube(f"Rite shut village hut {i}", (x, y, 1.15),
             (3.2, 2.5, 2.4), chalk)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.65, radius2=0,
                                         depth=1.55, location=(x, y, 3.05),
                                         rotation=(0, 0, math.pi / 4))
        roof = bpy.context.object
        roof.name = f"Rite steep thatch roof {i}"
        roof.data.materials.append(dark)
        for j in range(5):
            stripe = cube(f"Rite roof straw strip {i} {j}",
                          (x - 1.45 + j * 0.72, y - 0.85, 2.56),
                          (0.045, 0.95, 0.045), wicker)
            stripe.rotation_euler[0] = -0.5
        cube(f"Rite hut closed door {i}", (x, y - 1.27, 0.8),
             (0.65, 0.04, 1.6), dark)
    for i in range(4):
        x = -19 + i * 13
        sphere(f"Rite distant round hill {i}", (x, 27, 0.6), 1, sky,
               segments=12, rings=8, scale=(9.0, 4.0, 3.8 + i % 2))
    for i, x in enumerate((-17, -14.5, 15.4, 18.0)):
        y = 5.0 + (i % 2) * 4.0
        cylinder(f"Rite field tree trunk {i}", (x, y, 1.8), 0.18,
                 3.6, dark, vertices=7)
        sphere(f"Rite field tree canopy {i}", (x, y, 3.75), 1, grass,
               segments=12, rings=8, scale=(1.55, 1.35, 1.75))
    area_light("Rite warm daylight", (-4.5, -3, 8), 1850, 8,
               color=(1.0, 0.78, 0.49), target=(0, 1.6, 1.5))
    area_light("Rite soft sky fill", (5, 4, 7), 650, 7,
               color=(0.75, 0.87, 0.94), target=(0, 1.6, 1.4))
    cam = camera("Folk horror field camera", (7.0, -12.5, 5.1),
                 (0, 1.6, 1.7), lens=42)
    if variant == 2:
        animate(cam, "location", ((1, (7.0, -12.5, 5.1)),
                  (36, (5.7, -10.4, 4.7)), (72, (4.25, -7.6, 4.15))))
    else:
        animate(cam, "location", ((1, (7.0, -12.5, 5.1)),
                  (72, (6.55, -11.8, 5.0))))
    scene["folk_recipe"] = "sunlit closed village, ritual stones, handmade wicker, repeated crimson offerings"
    scene["folk_variant"] = variant
    return scene
