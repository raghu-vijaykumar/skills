"""Original cozy reading nook with a rocking chair and warming lamp."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Preserve soft furniture positions while the chair rocks as one hero object.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored cozy nook candidate")
    scene = reset_scene(spec, background=(0.54, 0.48, 0.37))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.82
    wall = material("Nook gentle cream wall", (0.66, 0.62, 0.48), roughness=1)
    floor = material("Nook warm oak floor", (0.39, 0.24, 0.13), roughness=0.87)
    wood = material("Nook rounded walnut furniture", (0.29, 0.16, 0.09), roughness=0.82)
    cushion = material("Nook sage velvet cushion", (0.23, 0.38, 0.29), roughness=0.96)
    coral = material("Nook soft coral throw", (0.69, 0.31, 0.24), roughness=0.98)
    cream = material("Nook cream woven rug", (0.72, 0.63, 0.47), roughness=1)
    paper = material("Nook book page cream", (0.80, 0.73, 0.58), roughness=0.94)
    blue = material("Nook muted blue book", (0.20, 0.36, 0.41), roughness=0.9)
    green = material("Nook leafy indoor plant", (0.16, 0.31, 0.17), roughness=0.88)
    terracotta = material("Nook earthen plant pot", (0.58, 0.27, 0.16), roughness=0.96)
    glow = material("Nook warm lamp bulb", (0.95, 0.69, 0.31),
                    emission=(1.0, 0.64, 0.22), emission_strength=1.7)
    window = material("Nook warm afternoon window", (0.70, 0.75, 0.62),
                      emission=(0.79, 0.73, 0.51), emission_strength=0.65)

    cube("SM_Nook_Oak_Floor", (0, 3, -0.12), (18, 18, 0.23), floor)
    cube("SM_Nook_Cream_Wall", (0, 7.5, 2.9), (18, 0.35, 5.8), wall)
    cube("Nook low wainscot", (0, 7.23, 0.82), (18, 0.09, 1.64), cream)
    cube("Nook warm window pane", (-3.5, 7.28, 3.30),
         (2.85, 0.035, 2.60), window)
    for side in (-1, 1):
        cube(f"Nook window jamb {side}", (-3.5 + side * 1.5, 7.20, 3.30),
             (0.14, 0.11, 2.9), wood)
    for level in (-1, 1):
        cube(f"Nook window rail {level}", (-3.5, 7.19, 3.30 + level * 1.37),
             (3.12, 0.13, 0.14), wood)
    cube("Nook window mullion", (-3.5, 7.17, 3.30),
         (0.12, 0.12, 2.70), wood)
    cylinder("SM_Nook_Round_Rug", (0, 1.75, 0.02),
             3.15, 0.035, cream, vertices=48)
    cylinder("Nook rug center motif", (0, 1.75, 0.045),
             2.45, 0.025, coral, vertices=48)

    bpy.ops.object.empty_add(location=(0, 1.85, 0.42))
    chair = bpy.context.object
    chair.name = "SM_Nook_Rocking_Chair_Rig"
    chair["soft_hero"] = "rounded sage reading chair"
    attach(cube("SM_Nook_Sage_Chair_Seat", (0, 1.85, 0.92),
                (2.15, 1.65, 0.40), cushion, edge=0.20), chair)
    attach(cube("Nook sage chair back", (0, 2.59, 1.82),
                (2.18, 0.40, 1.96), cushion, edge=0.22), chair)
    for side in (-1, 1):
        attach(cube(f"Nook padded arm {side}",
                    (side * 1.02, 1.82, 1.30), (0.36, 1.52, 0.47),
                    cushion, edge=0.16), chair)
        attach(cube(f"Nook walnut rocker rail {side}",
                    (side * 0.82, 1.89, 0.23), (0.12, 2.22, 0.12),
                    wood, edge=0.055), chair)
        for fore in (-1, 1):
            attach(cube(f"Nook chair leg {side} {fore}",
                        (side * 0.83, 1.85 + fore * 0.56, 0.51),
                        (0.17, 0.18, 0.86), wood, edge=0.04), chair)
    attach(cube("Nook coral folded throw", (-0.36, 1.25, 1.17),
                (1.22, 0.58, 0.07), coral, edge=0.035), chair)
    if variant == 2:
        animate(chair, "rotation_euler", ((1, (0.0, 0, 0)),
                (24, (0.085, 0, 0)), (48, (-0.078, 0, 0)),
                (72, (0.055, 0, 0))))
    else:
        animate(chair, "rotation_euler", ((1, (0.0, 0, 0)),
                (72, (0.006, 0, 0))))

    cylinder("Nook walnut side table top", (2.75, 1.47, 1.00),
             0.78, 0.13, wood, vertices=40)
    cylinder("Nook walnut side table stem", (2.75, 1.47, 0.55),
             0.12, 0.87, wood, vertices=20)
    cylinder("Nook walnut side table foot", (2.75, 1.47, 0.10),
             0.48, 0.12, wood, vertices=30)
    cube("Nook blue book", (2.55, 1.55, 1.12),
         (0.85, 0.62, 0.12), blue, edge=0.025)
    cube("Nook cream book pages", (2.55, 1.55, 1.20),
         (0.75, 0.54, 0.035), paper)
    cylinder("Nook tea mug", (3.22, 1.27, 1.18),
             0.17, 0.25, cream, vertices=24)
    cylinder("Nook tea surface", (3.22, 1.27, 1.32),
             0.14, 0.018, coral, vertices=24)
    cylinder("Nook plant clay pot", (-3.38, 2.55, 0.38),
             0.48, 0.76, terracotta, vertices=18)
    for i in range(7):
        leaf = sphere(f"Nook safe plant leaf {i}",
                      (-3.38 + (i % 3 - 1) * 0.20,
                       2.55 + (i // 3 - 1) * 0.19,
                       0.97 + i % 3 * 0.19),
                      0.22, green, segments=12, rings=8,
                      scale=(0.45, 0.65, 1.35))
        leaf.rotation_euler[1] = (i % 3 - 1) * 0.32
    for level in range(2):
        cube(f"Nook wall book shelf {level}",
             (3.75, 6.82, 2.05 + level * 1.45),
             (2.65, 0.38, 0.12), wood, edge=0.025)
        for i in range(5):
            cube(f"Nook safe shelf book {level} {i}",
                 (2.68 + i * 0.46, 6.76,
                  2.36 + level * 1.45 + (i % 2) * 0.06),
                 (0.31, 0.23, 0.56 + (i % 2) * 0.1),
                 [blue, coral, paper][(i + level) % 3], edge=0.025)
    cylinder("Nook reading lamp stem", (3.95, 2.4, 1.32),
             0.09, 2.62, wood, vertices=16)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.50,
                                    radius2=0.25, depth=0.50,
                                    location=(3.95, 2.4, 2.73))
    shade = bpy.context.object
    shade.name = "SM_Nook_Rounded_Lamp_Shade"
    shade.data.materials.append(cream)
    cylinder("Nook reading bulb", (3.95, 2.4, 2.43),
             0.18, 0.10, glow, vertices=24)
    if variant == 2:
        # Make the practical lamp visibly wake up with its area-light contribution.
        bulb_strength = glow.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        for frame, value in ((1, 0.15), (22, 0.15), (38, 3.0), (72, 3.0)):
            bulb_strength.default_value = value
            bulb_strength.keyframe_insert(data_path="default_value", frame=frame)
    lamp = area_light("SM_Nook_Warm_Reading_Light", (3.95, 1.7, 2.53),
                      90 if variant == 2 else 450, 2.5,
                      color=(1.0, 0.67, 0.35), target=(0.5, 1.9, 1.0))
    if variant == 2:
        animate(lamp.data, "energy", ((1, 90), (22, 90),
                 (38, 460), (72, 460)))
    area_light("Nook soft window key", (-3.6, 5.5, 4.5), 880, 6,
               color=(1.0, 0.78, 0.52), target=(0, 1.7, 1.3))
    area_light("Nook warm soft fill", (5.0, -3.0, 5.0), 520, 7,
               color=(0.78, 0.86, 1.0), target=(0, 2.0, 1.2))
    cam = camera("Cozy nook friendly-eye camera", (5.8, -9.1, 2.15),
                 (0, 2.5, 1.55), lens=36)
    animate(cam, "location", ((1, (5.8, -9.1, 2.15)),
             (72, (5.25 if variant == 2 else 5.7,
                   -7.9 if variant == 2 else -8.9, 2.05))))
    scene["cozy_recipe"] = "warm soft key and fill, rounded sage chair, safe books and plant, gentle rocking, friendly-eye camera"
    scene["cozy_variant"] = variant
    return scene
