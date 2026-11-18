"""Original monumental concrete archive gateway and tiny approaching witness."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Preserve world-space blockout coordinates for the moving gate and witness.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown brutalist archive candidate")
    scene = reset_scene(spec, background=(0.32, 0.34, 0.36))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    concrete = material("Archive raw gray board-formed concrete", (0.31, 0.32, 0.31),
                        roughness=0.96)
    pale = material("Archive pale concrete cut face", (0.48, 0.49, 0.47),
                    roughness=0.94)
    shadow = material("Archive deep aperture shadow", (0.035, 0.045, 0.049),
                      roughness=1.0)
    metal = material("Archive worn dark gate track", (0.12, 0.14, 0.14),
                     metallic=0.45, roughness=0.77)
    witness = material("Archive lone amber witness", (0.59, 0.37, 0.13),
                       roughness=0.87)

    cube("SM_Archive_Empty_Plaza", (0, 4.8, -0.15),
         (42, 50, 0.30), concrete)
    for i in range(11):
        # Large slab joints provide scale without decorative clutter.
        cube(f"Archive plaza control joint {i}",
             (0, -11.0 + i * 2.0, 0.009),
             (32.0, 0.025, 0.013), shadow)
    for side in (-1, 1):
        cube(f"Archive plaza long joint {side}",
             (side * 6.2, 3.0, 0.012),
             (0.025, 31.0, 0.013), shadow)
    left = cube("SM_Archive_Left_Monolith", (-4.0, 7.5, 5.35),
                (4.0, 5.8, 10.7), concrete, edge=0.035)
    right = cube("SM_Archive_Right_Monolith", (4.0, 7.5, 5.35),
                 (4.0, 5.8, 10.7), concrete, edge=0.035)
    for block in (left, right):
        block["form"] = "monumental solid"
    cube("SM_Archive_Cantilever_Crown", (0, 6.8, 11.13),
         (13.0, 7.3, 1.48), concrete, edge=0.035)
    cube("Archive offset upper cantilever", (-3.0, 5.4, 11.95),
         (11.0, 8.5, 0.55), pale, edge=0.022)
    for side in (-1, 1):
        for i in range(7):
            cube(f"Archive board-form seam {side} {i}",
                 (side * 4.0, 4.575, 1.22 + i * 1.30),
                 (3.96, 0.014, 0.024), shadow)
        for i in range(4):
            cube(f"Archive concrete tie hole {side} {i}",
                 (side * (3.13 + 0.55 * (i % 2)), 4.558,
                  2.05 + i * 1.83),
                 (0.075, 0.018, 0.075), shadow)
    cube("SM_Archive_Recessed_Dark_Void", (0, 10.34, 4.54),
         (3.97, 0.06, 9.08), shadow)
    for level in (0, 1):
        cube(f"Archive heavy gate track {level}",
             (2.0, 4.48, 0.36 + level * 8.82),
             (9.8, 0.16, 0.13), metal)

    bpy.ops.object.empty_add(location=(0, 0, 0))
    gate = bpy.context.object
    gate.name = "SM_Archive_Sliding_Gate_Rig"
    gate["mechanism"] = "concrete shutter slides laterally on visible tracks"
    attach(cube("SM_Archive_Concrete_Shutter", (0, 4.33, 4.55),
                (3.89, 0.52, 8.85), pale, edge=0.035), gate)
    for i in range(6):
        attach(cube(f"Archive shutter board seam {i}",
                    (0, 4.058, 1.25 + i * 1.27),
                    (3.84, 0.013, 0.024), concrete), gate)
    attach(cube("Archive shutter recessed pull", (1.37, 4.055, 4.25),
                (0.13, 0.018, 0.90), metal), gate)
    if variant == 2:
        animate(gate, "location", ((1, (0, 0, 0)),
                (24, (0, 0, 0)), (60, (4.20, 0, 0)),
                (72, (4.20, 0, 0))))
    else:
        animate(gate, "location", ((1, (0, 0, 0)),
                (72, (0.15, 0, 0))))

    bpy.ops.object.empty_add(location=(0, 0, 0))
    person = bpy.context.object
    person.name = "SM_Archive_Tiny_Witness_Rig"
    person["height_m"] = 1.76
    attach(cylinder("SM_Archive_Witness_Coat", (0.0, -2.0, 0.94),
                    0.22, 1.08, witness, vertices=16), person)
    attach(sphere("Archive witness head", (0.0, -2.0, 1.60),
                  0.19, witness, segments=16, rings=8), person)
    for side in (-1, 1):
        attach(cube(f"Archive witness leg {side}",
                    (side * 0.105, -2.0, 0.24),
                    (0.11, 0.16, 0.49), shadow), person)
        attach(cube(f"Archive witness arm {side}",
                    (side * 0.27, -2.0, 0.96),
                    (0.10, 0.13, 0.63), witness), person)
    if variant == 2:
        animate(person, "location", ((1, (0, 0, 0)),
                (36, (0.40, 2.0, 0)), (72, (0.75, 4.05, 0))))
    else:
        animate(person, "location", ((1, (0, 0, 0)),
                (72, (0.03, 0.12, 0))))

    area_light("Archive hard high concrete key", (-7.5, -1.5, 15.0),
               2250, 3.2, color=(0.91, 0.94, 1.0),
               target=(0, 6.0, 5.3))
    area_light("Archive restrained stone fill", (8.0, -3.0, 7.0),
               420, 7.0, color=(0.79, 0.85, 0.91),
               target=(0, 7.0, 3.0))
    cam = camera("Archive low witness camera", (7.8, -15.0, 3.25),
                 (0, 6.9, 5.55), lens=28)
    animate(cam, "location", ((1, (7.8, -15.0, 3.25)),
             (72, (6.9 if variant == 2 else 7.76,
                   -12.9 if variant == 2 else -14.9, 3.20))))
    scene["brutalist_recipe"] = "monumental raw concrete, board-form seams, one tiny witness, deep gate shadow, austere low camera"
    scene["brutalist_variant"] = variant
    return scene
