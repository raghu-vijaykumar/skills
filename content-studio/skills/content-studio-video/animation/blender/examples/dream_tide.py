"""Original surreal tide with an unsupported doorway and floating stairs."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Door and boat parts follow authored pivots without losing their world poses.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown dream-tide candidate")
    scene = reset_scene(spec, background=(0.26, 0.22, 0.36))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.55
    sea = material("Dream mirror lavender tide", (0.23, 0.20, 0.34),
                   metallic=0.33, roughness=0.26)
    mauve = material("Dream distant mauve horizon", (0.30, 0.22, 0.38), roughness=1)
    cream = material("Dream warm ivory stairs", (0.72, 0.62, 0.55), roughness=0.65)
    rose = material("Dream rose door paint", (0.59, 0.28, 0.36), roughness=0.76)
    gold = material("Dream oversized symbolic brass key", (0.68, 0.43, 0.16),
                    metallic=0.65, roughness=0.4)
    portal = material("Dream luminous portal depth", (0.25, 0.16, 0.42),
                      emission=(0.28, 0.20, 0.58), emission_strength=1.2)
    glint = material("Dream pale keyhole glint", (0.88, 0.73, 0.54),
                     emission=(1.0, 0.82, 0.58), emission_strength=0.9)
    portal_mark = material("Dream revealed lunar portal symbol", (0.69, 0.73, 0.96),
                           emission=(0.58, 0.67, 1.0), emission_strength=3.0)
    blue = material("Dream small paper-boat blue", (0.24, 0.49, 0.56), roughness=0.8)

    cube("SM_Dream_Mirror_Sea", (0, 7, -0.25), (60, 70, 0.45), sea)
    cube("Dream mauve distant bank", (0, 23, 1.2),
         (60, 0.20, 2.4), mauve)
    for i in range(6):
        # Sparse mirrored disks act as impossible ripples beneath the stairs.
        cylinder(f"Dream tide pale ripple {i}",
                 (-3.8 + i * 1.62, 2.4 + 0.34 * (i % 2), 0.003),
                 0.49 + 0.1 * (i % 3), 0.012, cream, vertices=48)

    bpy.ops.object.empty_add(location=(-1.35, 7.0, 2.85))
    door = bpy.context.object
    door.name = "SM_Dream_Opening_Door_Rig"
    door["symbol"] = "unsupported threshold over a mirror sea"
    # The portal frame has no supporting wall or island.
    for side in (-1, 1):
        cube(f"Dream unsupported frame upright {side}",
             (side * 1.48, 7.02, 2.72), (0.24, 0.40, 5.5), cream, edge=0.05)
    cube("SM_Dream_Unsupported_Doorway", (0, 7.02, 5.47),
         (3.18, 0.42, 0.32), cream, edge=0.05)
    cube("Dream portal inner glow", (0, 7.13, 2.75),
         (2.66, 0.06, 5.20), portal)
    # The concealed lunar mark makes opening the door a visible symbolic reveal.
    bpy.ops.mesh.primitive_torus_add(major_radius=0.81, minor_radius=0.055,
                                     location=(0, 6.99, 3.03),
                                     rotation=(math.pi / 2, 0, 0))
    lunar = bpy.context.object
    lunar.name = "SM_Dream_Revealed_Lunar_Ring"
    lunar.data.materials.append(portal_mark)
    sphere("Dream lunar mark center", (0, 6.96, 3.03),
           0.20, portal_mark, scale=(1, 0.24, 1))
    attach(cube("SM_Dream_Rose_Door_Panel", (0, 6.76, 2.73),
                (2.76, 0.16, 5.25), rose, edge=0.05), door)
    keyhole = attach(sphere("Dream door keyhole crown", (0.18, 6.63, 3.12),
                            0.28, glint, scale=(1, 0.22, 1)), door)
    attach(cube("Dream door keyhole stem", (0.18, 6.59, 2.72),
                (0.16, 0.04, 0.65), glint), door)
    if variant == 2:
        animate(door, "rotation_euler", ((1, (0, 0, 0)),
                (23, (0, 0, 0)), (55, (0, 0, -1.05)),
                (72, (0, 0, -1.18))))
    else:
        animate(door, "rotation_euler", ((1, (0, 0, 0)),
                (72, (0, 0, -0.05))))

    stairs = []
    for i in range(8):
        y = -2.4 + i * 1.1
        z = 0.30 + i * 0.18
        x = 0.40 * math.sin(i * 0.72)
        step = cube(f"SM_Dream_Floating_Step_{i}",
                    (x, y, z), (2.25, 0.69, 0.20), cream, edge=0.055)
        step["unsupported"] = True
        stairs.append(step)
        if variant == 2:
            animate(step, "location", ((1, (x, y, z)),
                    (34, (x, y, z + 0.20 + (i % 3) * 0.035)),
                    (72, (x, y, z + 0.05 * (i % 2)))))
        else:
            animate(step, "location", ((1, (x, y, z)),
                    (72, (x, y, z + 0.01))))

    # The key is larger than the nearby boat and floats without a chain.
    bpy.ops.mesh.primitive_torus_add(major_radius=0.62, minor_radius=0.10,
                                     location=(-4.25, 8.0, 4.66),
                                     rotation=(math.pi / 2, 0, 0))
    ring = bpy.context.object
    ring.name = "SM_Dream_Giant_Key_Ring"
    ring.data.materials.append(gold)
    cube("Dream giant key shaft", (-4.25, 8.0, 2.86),
         (0.22, 0.20, 2.78), gold, edge=0.04)
    for i in range(2):
        cube(f"Dream giant key tooth {i}",
             (-3.91, 8.0, 1.70 + i * 0.38),
             (0.57, 0.20, 0.18), gold, edge=0.025)
    ring["scale_play"] = "giant key beside tiny boat"

    bpy.ops.object.empty_add(location=(0, 0, 0))
    boat = bpy.context.object
    boat.name = "SM_Dream_Tiny_Boat_Rig"
    attach(cube("SM_Dream_Small_Boat_Hull", (3.0, 0.0, 0.28),
                (1.24, 0.48, 0.22), blue, edge=0.08), boat)
    attach(cylinder("Dream boat mast", (3.0, 0.0, 0.73),
                    0.025, 0.87, gold, vertices=12), boat)
    sail_mesh = bpy.data.meshes.new("Dream folded sail mesh")
    sail_mesh.from_pydata(((3.02, 0.0, 0.37), (3.02, 0.0, 1.20),
                           (3.47, 0.0, 0.53)), (), ((0, 1, 2),))
    sail_mesh.update()
    sail = bpy.data.objects.new("Dream tiny ivory sail", sail_mesh)
    scene.collection.objects.link(sail)
    sail.data.materials.append(cream)
    attach(sail, boat)
    if variant == 2:
        animate(boat, "location", ((1, (0, -0.5, 0)),
                (36, (-0.28, 0.7, 0.14)), (72, (-0.60, 1.8, 0.04))))
    else:
        animate(boat, "location", ((1, (0, 0, 0)), (72, (0, 0.10, 0))))

    area_light("Dream large peach softbox", (6, -3, 10), 1550, 8,
               color=(1.0, 0.66, 0.61), target=(0, 5, 2.5))
    area_light("Dream lilac door rim", (-5, 10, 8), 1250, 7,
               color=(0.64, 0.69, 1.0), target=(0, 5, 2.8))
    area_light("Dream low misty fill", (2, 4, 5), 460, 9,
               color=(0.78, 0.76, 1.0), target=(0, 4, 1.0))
    cam = camera("Dream tide witness camera", (5.9, -10.7, 3.45),
                 (0, 4.7, 2.5), lens=37)
    animate(cam, "location", ((1, (5.9, -10.7, 3.45)),
             (72, (5.3 if variant == 2 else 5.85,
                   -9.5 if variant == 2 else -10.6, 3.35))))
    scene["dream_recipe"] = "unsupported doorway, giant symbolic key, tiny boat, levitating stairs, soft pastel physics"
    scene["dream_variant"] = variant
    return scene
