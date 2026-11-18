"""Original low-magic stone keep with a timber drawbridge lowering over a moat."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored fantasy gate candidate")
    scene = reset_scene(spec, background=(0.30, 0.43, 0.57))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
    stone = material("Keep limestone ashlar", (0.54, 0.53, 0.45), roughness=0.96)
    joint = material("Keep dark mortar", (0.32, 0.34, 0.31), roughness=1)
    wood = material("Keep oak drawbridge", (0.24, 0.12, 0.065), roughness=0.82)
    iron = material("Keep forged iron", (0.12, 0.13, 0.13), metallic=0.74,
                    roughness=0.62)
    red = material("Keep heraldic red wool", (0.48, 0.035, 0.052), roughness=0.91)
    gold = material("Keep heraldic ochre wool", (0.69, 0.43, 0.11), roughness=0.91)
    water = material("Keep dark moat water", (0.065, 0.17, 0.20), roughness=0.24)
    grass = material("Keep muted bank grass", (0.18, 0.29, 0.15), roughness=1)
    dark = material("Keep black gateway", (0.035, 0.045, 0.045), roughness=1)

    cube("SM_Keep_Bank", (0, -4.7, -0.22), (30, 12.7, 0.42), grass)
    cube("SM_Keep_Moat", (0, 2.9, -0.14), (15.0, 8.7, 0.22), water)
    cube("Keep castle ground", (0, 10.6, -0.20), (32, 15, 0.4), grass)
    for side in (-1, 1):
        # Split wall piers preserve a real gate opening beneath the lintel.
        cube(f"SM_Keep_Wall_Pier_{side}", (side * 3.20, 7.0, 2.70),
             (3.65, 1.35, 5.4), stone)
        cube(f"Keep gate reveal {side}", (side * 1.23, 6.25, 2.20),
             (0.18, 0.22, 4.4), joint)
        tower = cylinder(f"SM_Keep_Tower_{side}",
                         (side * 5.05, 7.30, 3.30), 1.55, 6.60,
                         stone, vertices=16)
        tower["masonry_tower"] = side
        cylinder(f"Keep tower coping {side}", (side * 5.05, 7.30, 6.71),
                 1.68, 0.22, joint, vertices=16)
        for i in range(8):
            a = i * 2 * math.pi / 8
            block = cube(f"Keep tower merlon {side} {i}",
                         (side * 5.05 + 1.30 * math.sin(a),
                          7.30 + 1.30 * math.cos(a), 7.02),
                         (0.65, 0.64, 0.66), stone)
            block.rotation_euler[2] = a
        cube(f"Keep arrow slit {side}", (side * 5.05, 5.72, 4.05),
             (0.12, 0.035, 0.70), dark)
        cube(f"Keep banner wool {side}", (side * 4.15, 5.69, 3.15),
             (0.74, 0.07, 1.45), red)
        cube(f"Keep banner heraldic bar {side}",
             (side * 4.15, 5.64, 3.15), (0.14, 0.015, 1.10), gold)
    cube("SM_Keep_Gate_Lintel", (0, 7.0, 4.90), (2.85, 1.40, 1.10), stone)
    cube("Keep deep gateway shadow", (0, 7.78, 2.10),
         (2.65, 0.07, 4.25), dark)
    for row in range(3):
        for col in range(11):
            x = -3.82 + col * 0.76
            z = 1.05 + row * 1.35
            cube(f"Keep ashlar joint {row} {col}",
                 (x, 6.27, z), (0.52, 0.045, 0.025), joint)
    for i in range(8):
        cube(f"Keep parapet merlon {i}",
             (-3.35 + i * 0.95, 7.0, 5.72),
             (0.52, 1.50, 0.72), stone)

    bpy.ops.object.empty_add(location=(0, 5.89, 0.28))
    hinge = bpy.context.object
    hinge.name = "Keep drawbridge hinge control"
    # Build in the lowered pose, then rotate the hinge up for the first beat.
    bridge = attach(cube("SM_Keep_Oak_Drawbridge", (0, 3.67, 0.28),
                         (2.47, 4.44, 0.20), wood, edge=0.035), hinge)
    bridge["hinged_bridge"] = True
    for i in range(9):
        y = 1.69 + i * 0.49
        attach(cube(f"Keep oak plank seam {i}",
                    (0, y, 0.392), (2.30, 0.045, 0.02), iron), hinge)
    for side in (-1, 1):
        attach(cube(f"Keep drawbridge iron rail {side}",
                    (side * 1.04, 3.67, 0.39),
                    (0.08, 4.30, 0.035), iron), hinge)
        cylinder(f"Keep gate winding drum {side}",
                 (side * 1.65, 6.02, 4.55), 0.22, 0.60,
                 wood, vertices=12, rotation=(0, math.pi / 2, 0))
    if variant == 2:
        animate(hinge, "rotation_euler", ((1, (-1.44, 0, 0)),
                (20, (-1.44, 0, 0)), (48, (-0.68, 0, 0)),
                (72, (0, 0, 0))))
    else:
        animate(hinge, "rotation_euler", ((1, (-1.44, 0, 0)),
                (72, (-1.30, 0, 0))))
    for i in range(13):
        x = -5.8 + i * 0.94
        y = 2.4 + (i % 3) * 1.2
        cube(f"Keep moat ripple {i}", (x, y, 0.002),
             (0.45 + (i % 4) * 0.16, 0.035, 0.01), gold)
    area_light("Keep warm sunset key", (-5.5, -5, 9.0), 1600, 7,
               color=(1.0, 0.75, 0.49), target=(0, 6.5, 2.4))
    area_light("Keep cool sky fill", (6.0, 4.0, 8.0), 650, 7,
               color=(0.68, 0.81, 1.0), target=(0, 6.5, 3.0))
    cam = camera("Fantasy gate inspection camera", (6.5, -8.8, 4.0),
                 (0, 5.3, 2.7), lens=36)
    animate(cam, "location", ((1, (6.5, -8.8, 4.0)),
             (72, (5.6 if variant == 2 else 6.3,
                   -7.1 if variant == 2 else -8.4, 3.80))))
    scene["fantasy_recipe"] = "medieval low-magic stone keep, wool heraldry, oak drawbridge, iron fittings"
    scene["fantasy_variant"] = variant
    return scene
