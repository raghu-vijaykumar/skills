"""Original worn freight depot with a moving, suspended cargo cage."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Keep modeled world positions while moving the crane load as one assembly.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def rusted_metal():
    """Use procedural pigment variation to make oxidation part of the surface."""
    mat = material("Depot oxidized structural steel", (0.16, 0.16, 0.16),
                   metallic=0.45, roughness=0.86)
    nodes = mat.node_tree.nodes
    tex = nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 5.5
    tex.inputs["Detail"].default_value = 4.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (0.065, 0.075, 0.078, 1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (0.32, 0.13, 0.065, 1)
    mat.node_tree.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    mat.node_tree.links.new(ramp.outputs["Color"],
                            nodes["Principled BSDF"].inputs["Base Color"])
    return mat


def hook_curve(name, location, steel):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.075
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(7)
    shape = ((0, 0, 0.32), (0, 0, 0.10), (0.04, 0, -0.12),
             (0.20, 0, -0.30), (0.42, 0, -0.30),
             (0.57, 0, -0.18), (0.55, 0, 0.02), (0.43, 0, 0.12))
    for point, (x, y, z) in zip(spline.points, shape):
        point.co = (x, y, z, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    curve.materials.append(steel)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown freight-depot candidate")
    scene = reset_scene(spec, background=(0.018, 0.025, 0.027))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22
    concrete = material("Depot stained cold concrete", (0.18, 0.20, 0.20), roughness=0.98)
    wet = material("Depot wet dark floor", (0.055, 0.067, 0.070),
                   metallic=0.12, roughness=0.31)
    steel = rusted_metal()
    deep = material("Depot old coal-black iron", (0.045, 0.052, 0.052),
                    metallic=0.48, roughness=0.87)
    ochre = material("Depot worn warning ochre", (0.39, 0.22, 0.075), roughness=0.90)
    flake = material("Depot flaking pale paint", (0.42, 0.44, 0.37), roughness=0.99)
    amber = material("Depot lone sodium work lamp", (0.88, 0.43, 0.13),
                     emission=(1.0, 0.45, 0.11), emission_strength=2.2)

    cube("SM_Depot_Wet_Floor", (0, 4, -0.15), (19, 24, 0.30), wet)
    cube("SM_Depot_Stained_Back_Wall", (0, 9.3, 3.05),
         (19, 0.35, 6.15), concrete)
    for side in (-1, 1):
        cube(f"Depot side wall {side}", (side * 8.85, 3.8, 3.05),
             (0.34, 14.0, 6.15), concrete)
    # The repeated heavy bays sell an occupied industrial volume without crowds.
    for i in range(5):
        y = -3.1 + i * 2.65
        for side in (-1, 1):
            cube(f"Depot structural upright {i} {side}",
                 (side * 7.75, y, 3.05), (0.52, 0.62, 6.1), steel)
            cube(f"Depot rust bleed {i} {side}",
                 (side * 7.39, y - 0.07, 1.7),
                 (0.017, 0.18, 2.8), ochre)
        cube(f"Depot overhead truss {i}", (0, y, 5.85),
             (16.0, 0.54, 0.70), steel)
    cube("SM_Depot_Gantry_Beam", (0, 2.30, 5.12),
         (13.8, 0.67, 0.52), deep)
    for side in (-1, 1):
        cube(f"Depot gantry flange {side}", (0, 2.3 + side * 0.38, 5.12),
             (13.8, 0.10, 0.11), steel)
    # A worn repair panel and rust trails tell the depot's history at hero scale.
    cube("SM_Depot_Patched_Shutter", (0, 9.05, 2.13),
         (6.5, 0.12, 4.25), deep)
    for i in range(11):
        cube(f"Depot dented shutter slat {i}", (0, 8.98, 0.33 + 0.35 * i),
             (6.48, 0.06, 0.065), steel)
    for i in range(9):
        x = -2.8 + i * 0.72
        cube(f"Depot chipped paint patch {i}", (x, 8.89, 3.5 + 0.09 * (i % 3)),
             (0.20 + (i % 2) * 0.1, 0.014, 0.075), flake)
    for i in range(5):
        cube(f"Depot shutter rust drip {i}", (-2.5 + 1.15 * i, 8.88, 2.52),
             (0.06, 0.015, 1.3 + 0.2 * (i % 2)), ochre)
    for side in (-1, 1):
        cube(f"Depot worn rail {side}", (side * 1.9, 1.5, 0.08),
             (0.13, 13.3, 0.13), steel)
        for i in range(8):
            cube(f"Depot rail sleeper {side} {i}",
                 (side * 1.9, -4.9 + i * 1.7, 0.02),
                 (0.65, 0.23, 0.06), deep)
    for i in range(4):
        cylinder(f"Depot abandoned oil drum {i}",
                 (5.45 + (i % 2) * 0.85, 1.5 + (i // 2) * 1.08, 0.53),
                 0.39, 1.02, steel, vertices=24)
    cube("Depot safety placard", (-6.2, 8.89, 3.2),
         (1.28, 0.025, 0.86), ochre)
    for i in range(3):
        cube(f"Depot worn placard slash {i}", (-6.52 + i * 0.33, 8.865, 3.2),
             (0.075, 0.013, 0.64), deep)

    bpy.ops.object.empty_add(location=(0, 0, 0))
    load = bpy.context.object
    load.name = "SM_Depot_Suspended_Load_Rig"
    load["story"] = "abandoned rusty depot, repaired cargo cage still on the gantry"
    start_x = -3.4
    center_y = 2.3
    attach(cube("SM_Depot_Crane_Trolley", (start_x, center_y, 4.69),
                (1.22, 0.98, 0.45), ochre, edge=0.04), load)
    for side in (-1, 1):
        attach(cylinder(f"Depot trolley roller {side}",
                        (start_x + side * 0.43, center_y, 4.96),
                        0.19, 0.13, deep, vertices=24,
                        rotation=(math.pi / 2, 0, 0)), load)
    for i in range(11):
        # Alternating links remain individually inspectable in the saved scene.
        bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.045,
                                         location=(start_x, center_y, 4.35 - i * 0.22))
        link = bpy.context.object
        link.name = f"Depot heavy chain link {i}"
        link.rotation_euler[1] = (i % 2) * math.pi / 2
        link.data.materials.append(steel)
        attach(link, load)
    attach(hook_curve("SM_Depot_Crane_Hook", (start_x, center_y, 1.78), steel), load)
    cage = attach(cube("SM_Depot_Cargo_Cage_Base",
                       (start_x + 0.25, center_y, 0.69),
                       (2.0, 1.3, 0.14), steel, edge=0.03), load)
    for side in (-1, 1):
        for fore in (-1, 1):
            attach(cube(f"Depot battered cage upright {side} {fore}",
                        (start_x + 0.25 + side * 0.88,
                         center_y + fore * 0.54, 1.28),
                        (0.10, 0.10, 1.35), deep), load)
        attach(cube(f"Depot cage side bar {side}",
                    (start_x + 0.25 + side * 0.88, center_y, 1.37),
                    (0.10, 1.12, 0.08), steel), load)
    for i in range(4):
        attach(cube(f"Depot cargo lattice {i}",
                    (start_x - 0.50 + i * 0.5, center_y - 0.54, 1.21),
                    (0.06, 0.07, 1.15), steel), load)
    attach(cube("Depot cage flaking repair plate",
                (start_x + 0.25, center_y - 0.58, 1.00),
                (0.55, 0.035, 0.26), flake), load)
    if variant == 2:
        animate(load, "location", ((1, (0, 0, 0)),
                (38, (2.35, 0, 0)), (72, (4.2, 0, 0))))
        animate(load, "rotation_euler", ((1, (0, 0, 0)),
                (36, (0, 0.018, 0.025)), (56, (0, -0.025, -0.020)),
                (72, (0, 0.010, 0))))
    else:
        animate(load, "location", ((1, (0, 0, 0)), (72, (0.16, 0, 0))))
    cube("Depot lone bulb housing", (4.9, 7.5, 4.75),
         (0.80, 0.70, 0.20), deep)
    cylinder("SM_Depot_Amber_Work_Lamp", (4.9, 7.5, 4.60),
             0.31, 0.08, amber, vertices=24)
    area_light("Depot cold roof shaft", (-4.8, 1.0, 6.4), 1120, 4.5,
               color=(0.59, 0.75, 0.83), target=(-1.5, 2.5, 1.3))
    area_light("Depot lonely warm practical", (4.9, 7.0, 4.4), 620, 2.0,
               color=(1.0, 0.53, 0.22), target=(1.0, 4.0, 1.0))
    area_light("Depot dark steel fill", (6.7, -3.5, 4.5), 150, 6.0,
               color=(0.55, 0.67, 0.70), target=(0, 3.5, 1.7))
    cam = camera("Gritty depot inspection camera", (7.8, -10.8, 3.65),
                 (0, 3.4, 2.30), lens=32)
    animate(cam, "location", ((1, (7.8, -10.8, 3.65)),
             (72, (7.25 if variant == 2 else 7.75,
                   -9.6 if variant == 2 else -10.7, 3.58))))
    scene["dark_recipe"] = "low-key cold shaft, lone warm practical, oxidized industrial weight, flaking repair, lonely moving load"
    scene["dark_variant"] = variant
    return scene
