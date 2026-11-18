"""Original two-team circuit sprint with clear edges, stands, and finish marker."""

from pathlib import Path
from math import pi

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Parent each car part to the motion rig so the silhouette survives the pass.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def car(name, x, y, paint, glass, rubber):
    bpy.ops.object.empty_add(location=(0, 0, 0))
    rig = bpy.context.object
    rig.name = name
    attach(cube(name + " chassis", (x, y, 0.35),
                (1.30, 0.59, 0.24), paint, edge=0.075), rig)
    attach(cube(name + " canopy", (x - 0.04, y, 0.56),
                (0.62, 0.46, 0.25), glass, edge=0.045), rig)
    attach(cube(name + " spoiler", (x - 0.55, y, 0.56),
                (0.10, 0.78, 0.10), paint), rig)
    for front in (-1, 1):
        for side in (-1, 1):
            wheel = cylinder(f"{name} wheel {front} {side}",
                             (x + front * 0.39, y + side * 0.34, 0.22),
                             0.19, 0.12, rubber, vertices=16,
                             rotation=(pi / 2, 0, 0))
            attach(wheel, rig)
    return rig


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown circuit sprint candidate")
    scene = reset_scene(spec, background=(0.07, 0.11, 0.16))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    base = material("Circuit charcoal base", (0.07, 0.10, 0.13), roughness=0.92)
    asphalt = material("Circuit graphite asphalt", (0.16, 0.20, 0.23), roughness=0.78)
    white = material("Circuit finish white", (0.81, 0.85, 0.81), roughness=0.76)
    yellow = material("Circuit edge yellow", (0.92, 0.70, 0.12), roughness=0.70)
    rail = material("Circuit rail steel", (0.35, 0.47, 0.51), metallic=0.55,
                    roughness=0.42)
    stands = material("Circuit stand concrete", (0.28, 0.34, 0.39), roughness=0.87)
    cyan = material("Circuit cyan team", (0.04, 0.60, 0.79), metallic=0.27,
                    roughness=0.42)
    red = material("Circuit scarlet team", (0.82, 0.09, 0.11), metallic=0.26,
                   roughness=0.45)
    glass = material("Circuit tinted canopy", (0.08, 0.20, 0.24), metallic=0.30,
                     roughness=0.28)
    rubber = material("Circuit black tires", (0.025, 0.035, 0.04), roughness=0.9)
    cube("Circuit diorama plinth", (0, 0, -0.42), (11.6, 6.9, 0.36), base,
         edge=0.10)
    cube("SM_Circuit_Track", (0, -0.53, -0.10),
         (10.6, 3.76, 0.28), asphalt, edge=0.045)
    # Continuous rails and yellow edges let two fast silhouettes stay in lane.
    for y in (-2.43, 1.37):
        cube(f"Circuit yellow track edge {y}", (0, y, 0.08),
             (10.48, 0.10, 0.035), yellow)
        cube(f"Circuit outer safety rail {y}", (0, y + (0.22 if y > 0 else -0.22), 0.35),
             (10.35, 0.07, 0.42), rail)
    for i in range(7):
        cube(f"Circuit center dashed line {i}", (-4.5 + i * 1.48, -0.53, 0.06),
             (0.58, 0.055, 0.025), white)
    # A broad checkerboard and overhead sign are the legible race landmark.
    finish_x = 2.55
    for row in range(8):
        for col in range(2):
            if (row + col) % 2 == 0:
                cube(f"Circuit checker {row} {col}",
                     (finish_x + (col - 0.5) * 0.20,
                      -2.09 + row * 0.44, 0.075),
                     (0.20, 0.44, 0.02), white)
    cube("SM_Circuit_Finish_Marker", (finish_x, -0.53, 2.52),
         (0.22, 4.22, 0.30), white)
    for y in (-2.67, 1.61):
        cube(f"Circuit finish upright {y}", (finish_x, y, 1.29),
             (0.19, 0.18, 2.55), rail)
    # Repeated stand bays and alternating team blocks imply a modular stadium kit.
    cube("SM_Circuit_Grandstand", (0, 2.33, 0.22),
         (9.3, 1.14, 0.50), stands, edge=0.045)
    for i in range(7):
        x = -3.93 + i * 1.31
        cube(f"Circuit grandstand bay {i}", (x, 2.36, 0.62),
             (1.06, 0.96, 0.31), cyan if i % 2 == 0 else red)
        cube(f"Circuit grandstand riser {i}", (x, 2.70, 0.99),
             (1.04, 0.30, 0.43), stands)
    cube("SM_Circuit_Pit_Tower", (-4.36, 2.45, 1.05),
         (0.88, 0.86, 1.25), stands, edge=0.04)
    cube("Circuit pit control glass", (-4.36, 2.45, 1.80),
         (1.02, 1.0, 0.42), glass, edge=0.025)
    cube("Circuit pit cyan flag", (-4.06, 2.45, 2.17),
         (0.55, 0.06, 0.27), cyan)
    blue_car = car("SM_Circuit_Cyan_Car_Rig", -4.10, -1.45,
                   cyan, glass, rubber)
    red_car = car("SM_Circuit_Red_Car_Rig", -3.52, 0.26,
                  red, glass, rubber)
    if variant == 2:
        key(blue_car, "location", ((1, (0, 0, 0)),
                                    (26, (2.70, 0, 0)),
                                    (42, (4.95, 0, 0)),
                                    (72, (8.15, 0, 0))))
        key(red_car, "location", ((1, (0, 0, 0)),
                                   (26, (2.18, 0, 0)),
                                   (42, (4.05, 0, 0)),
                                   (72, (7.05, 0, 0))))
    else:
        key(blue_car, "location", ((1, (0, 0, 0)), (72, (0.16, 0, 0))))
        key(red_car, "location", ((1, (0, 0, 0)), (72, (0.15, 0, 0))))
    area_light("Circuit sunny track key", (-2.0, -4.2, 9.1), 1550, 6.8,
               color=(1.0, 0.83, 0.65), target=(0, 0, 0.3))
    area_light("Circuit stadium fill", (4.5, 2.7, 7.4), 950, 5,
               color=(0.55, 0.78, 1.0), target=(0, 0, 0.5))
    cam = camera("Circuit sprint overview camera", (7.8, -10.7, 8.2),
                 (0, 0, 0.35), ortho=14.2)
    if variant == 2:
        key(cam, "location", ((1, (7.8, -10.7, 8.2)),
                              (72, (7.6, -10.3, 7.9))))
    scene["circuit_recipe"] = "clear track edges, checker finish, seven modular stands, pit landmark, cyan and red teams"
    scene["circuit_variant"] = variant
    return scene
