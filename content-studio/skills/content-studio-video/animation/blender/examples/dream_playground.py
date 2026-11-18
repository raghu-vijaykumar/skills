"""Original pastel dream playground with a floating alphabet block and sky doorway."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, material, reset_scene, sphere


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


def label(name, body, location, size, mat, parent=None):
    curve = bpy.data.curves.new(name, "FONT")
    curve.body = body
    curve.size = size
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (math.pi / 2, 0, 0)
    curve.materials.append(mat)
    if parent:
        attach(obj, parent)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored dream playground candidate")
    scene = reset_scene(spec, background=(0.64, 0.64, 0.80))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.78
    scene.view_settings.view_transform = "AgX"
    lavender = material("Dream hazy lavender field", (0.47, 0.39, 0.59), roughness=1)
    mist = material("Dream pale haze wall", (0.69, 0.67, 0.79), roughness=1)
    peach = material("Dream pastel peach block", (0.96, 0.56, 0.48), roughness=0.91)
    butter = material("Dream faded yellow block", (0.96, 0.79, 0.46), roughness=0.91)
    mint = material("Dream chalk mint block", (0.45, 0.74, 0.69), roughness=0.91)
    cream = material("Dream paper cream symbols", (0.94, 0.88, 0.72), roughness=1)
    blue = material("Dream faded sky blue", (0.24, 0.39, 0.58), roughness=0.90)
    red = material("Dream wrong coral door", (0.75, 0.19, 0.23), roughness=0.77)
    void = material("Dream blank behind door", (0.045, 0.035, 0.095), roughness=1)
    glow = material("Dream soft star glow", (0.86, 0.75, 0.95),
                    emission=(0.92, 0.80, 1), emission_strength=1.25)

    cube("SM_Dream_Empty_Playground", (0, 1.8, -0.25), (70, 70, 0.45), lavender)
    # Receding disconnected playroom walls suggest a geography with no clear path.
    for i in range(4):
        x = (-1) ** i * (8.5 + i * 2.0)
        y = 7 + i * 6.2
        cube(f"Dream isolated nursery wall {i}", (x, y, 2.0 + i * 0.25),
             (4.0, 0.14, 4.0), mist)
        cube(f"Dream disconnected floor tile {i}", (x, y - 1.2, 0.004),
             (3.3, 2.3, 0.012), cream)
    bpy.ops.object.empty_add(location=(-2.8, 0.4, 1.15))
    block_control = bpy.context.object
    block_control.name = "Dream alphabet block float control"
    block = attach(cube("SM_Dream_Giant_Alphabet_Block", (-2.8, 0.4, 1.15),
                        (2.25, 2.25, 2.25), peach, edge=0.16), block_control)
    block["childhood_scale_exaggerated"] = True
    attach(label("SM_Dream_Block_Letter_A", "A", (-2.8, -0.76, 1.22),
                 1.66, cream), block_control)
    for i, (x, y, color, letter) in enumerate(((-5.2, 3.0, butter, "B"),
                                               (2.65, -0.5, mint, "C"),
                                               (4.65, 4.0, butter, "D"))):
        cube(f"Dream forgotten cube {i}", (x, y, 0.45),
             (0.92, 0.92, 0.92), color, edge=0.06)
        label(f"Dream forgotten letter {letter}", letter, (x, y - 0.48, 0.47),
              0.56, blue)
    # The toy chair has no child; its empty seat remains visible through the push.
    cube("SM_Dream_Empty_Chair_Seat", (3.1, 1.95, 0.76),
         (1.08, 0.92, 0.11), mint, edge=0.05)
    cube("Dream empty chair back", (3.1, 2.38, 1.36),
         (1.08, 0.12, 1.23), mint, edge=0.05)
    for x in (2.68, 3.52):
        for y in (1.57, 2.30):
            cube(f"Dream chair leg {x} {y}", (x, y, 0.36),
                 (0.10, 0.10, 0.72), blue)
    cube("SM_Dream_Sky_Door_Void", (0.95, 6.1, 2.73),
         (2.05, 0.10, 3.95), void)
    for side in (-1, 1):
        cube(f"Dream sky frame post {side}", (0.95 + side * 1.13, 5.96, 2.76),
             (0.20, 0.20, 4.18), cream)
    cube("Dream sky frame header", (0.95, 5.96, 4.86),
         (2.45, 0.22, 0.22), cream)
    bpy.ops.object.empty_add(location=(-0.04, 5.79, 2.75))
    hinge = bpy.context.object
    hinge.name = "Dream sky door hinge"
    door = attach(cube("SM_Dream_Impossible_Door", (0.95, 5.79, 2.74),
                       (1.98, 0.14, 3.92), red, edge=0.05), hinge)
    door["unsupported_sky_door"] = True
    attach(sphere("Dream door round knob", (1.70, 5.63, 2.68),
                  0.10, butter, segments=16, rings=10), hinge)
    for i in range(8):
        x = -6.9 + i * 1.9
        y = 8.3 + (i % 2) * 1.8
        star = sphere(f"Dream impossible hanging star {i}",
                      (x, y, 4.5 + (i % 3) * 0.65), 0.13, glow,
                      segments=12, rings=8)
        star.scale = (1.25, 0.35, 1.25)
    if variant == 2:
        # The block levitates as the sky door swings open, creating two readable actions.
        animate(block_control, "location", ((1, (-2.8, 0.4, 1.15)),
                (26, (-2.8, 0.4, 1.15)), (52, (-2.8, 0.4, 1.82)),
                (72, (-2.8, 0.4, 2.11))))
        animate(block_control, "rotation_euler", ((1, (0, 0, 0)),
                (26, (0, 0, 0)), (72, (0, -0.11, 0.19))))
        animate(hinge, "rotation_euler", ((1, (0, 0, 0)),
                (24, (0, 0, 0)), (50, (0, 0, 0.73)),
                (72, (0, 0, 1.04))))
    else:
        animate(block_control, "location", ((1, (-2.8, 0.4, 1.15)),
                (72, (-2.8, 0.4, 1.27))))
        animate(hinge, "rotation_euler", ((1, (0, 0, 0)),
                (72, (0, 0, 0.14))))
    area_light("Dream large soft sky", (-4, -4, 8), 1150, 8,
               color=(0.88, 0.81, 1.0), target=(0, 2, 1.5))
    area_light("Dream portal pink light", (2.2, 4.0, 4.4), 520, 4,
               color=(1.0, 0.49, 0.65), target=(0.95, 5.8, 2.5))
    cam = camera("Dream playground camera", (6.2, -10.6, 4.25),
                 (0.10, 3.55, 2.04), lens=35)
    animate(cam, "location", ((1, (6.2, -10.6, 4.25)),
             (72, (5.4 if variant == 2 else 6.0,
                   -9.0 if variant == 2 else -10.2, 4.0))))
    scene["dream_recipe"] = "pastel childhood block, empty toy chair, disconnected nursery, unsupported sky door"
    scene["dream_variant"] = variant
    return scene
