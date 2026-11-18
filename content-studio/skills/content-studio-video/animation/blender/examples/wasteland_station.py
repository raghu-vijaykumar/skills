"""Original post-apocalyptic roadside fuel stop and scavenged cart."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Keep the assembled salvage cart's parts at their modeled world positions.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored wasteland station candidate")
    scene = reset_scene(spec, background=(0.52, 0.38, 0.26))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.85
    sand = material("Wasteland sunbaked ochre sand", (0.48, 0.32, 0.18), roughness=1)
    road = material("Wasteland cracked road", (0.13, 0.12, 0.11), roughness=0.98)
    concrete = material("Wasteland dusted concrete", (0.42, 0.37, 0.28), roughness=0.97)
    rust = material("Wasteland oxidized steel", (0.33, 0.13, 0.07), metallic=0.38,
                    roughness=0.88)
    iron = material("Wasteland scavenged dark iron", (0.13, 0.15, 0.15),
                    metallic=0.55, roughness=0.82)
    faded = material("Wasteland faded fuel-stop paint", (0.44, 0.34, 0.20),
                     roughness=0.94)
    tarp = material("Wasteland patched amber tarp", (0.66, 0.31, 0.11),
                    roughness=0.98)
    rubber = material("Wasteland worn tire rubber", (0.065, 0.058, 0.05),
                      roughness=0.99)
    glass = material("Wasteland dusty window glass", (0.12, 0.17, 0.16),
                     roughness=0.62)
    dust = material("Wasteland windblown pale dust", (0.75, 0.58, 0.34),
                    roughness=1)

    cube("SM_Waste_Desert", (0, 7, -0.25), (50, 48, 0.45), sand)
    cube("SM_Waste_Cracked_Road", (0, -2.0, 0.004), (30, 5.8, 0.055), road)
    for i in range(11):
        cube(f"Waste faded road dash {i}", (-12.5 + i * 2.4, -2.0, 0.04),
             (0.9, 0.07, 0.012), faded)
    for i in range(7):
        x = -11 + i * 3.8
        dune = cube(f"Waste windcut berm {i}",
                    (x, 16 + i % 2, 0.4), (4.2, 2.2, 0.75), sand, edge=0.28)
        dune.rotation_euler.z = 0.08 * (i % 3 - 1)

    # Broken canopy and improvised bracing establish a previously serviced road.
    canopy = cube("SM_Waste_Fuel_Canopy", (0.0, 5.3, 4.25),
                  (7.6, 3.5, 0.35), concrete, edge=0.05)
    canopy["collapsed_station"] = True
    canopy.rotation_euler[1] = -0.065
    cube("SM_Waste_Canopy_Standing_Column", (2.7, 5.1, 2.05),
         (0.52, 0.55, 4.10), concrete)
    broken = cube("SM_Waste_Canopy_Broken_Column", (-2.9, 5.1, 1.45),
                  (0.54, 0.55, 2.90), concrete)
    broken.rotation_euler[1] = 0.19
    brace = cube("SM_Waste_Improvised_Brace", (-2.0, 4.9, 2.15),
                 (0.18, 0.25, 4.20), rust)
    brace.rotation_euler[1] = -0.32
    for i in range(5):
        x = -3.35 + i * 1.65
        cube(f"Waste roof rust patch {i}", (x, 5.12, 4.52),
             (0.68, 2.5, 0.025), rust)
    cube("Waste repair shack shell", (5.2, 7.7, 1.4),
         (3.6, 3.5, 2.8), iron, edge=0.03)
    for i in range(4):
        cube(f"Waste shack welded seam {i}", (3.52 + i * 0.98, 5.94, 1.58),
             (0.045, 0.04, 2.55), rust)
    cube("Waste repair shack dusty window", (5.2, 5.91, 1.74),
         (1.15, 0.02, 0.78), glass)
    cube("SM_Waste_Fuel_Pump", (-0.7, 4.0, 1.12),
         (1.1, 0.78, 2.24), faded, edge=0.04)
    cube("Waste pump dead display", (-0.7, 3.59, 1.70),
         (0.64, 0.03, 0.36), glass)
    for i in range(3):
        cylinder(f"Waste pump hose segment {i}",
                 (-0.13 + i * 0.25, 3.62 - i * 0.08, 0.95 - i * 0.21),
                 0.055, 0.56, rubber, vertices=8,
                 rotation=(0, 0.20 * i, 0))
    cube("SM_Waste_Faded_Sign", (-5.0, 5.4, 4.18),
         (1.8, 0.16, 1.1), faded)
    cylinder("Waste sign pole", (-5.0, 5.4, 2.2),
             0.11, 3.3, iron, vertices=8)
    # A three-part abstract mark is the outpost's original, fictional brand.
    for i in range(3):
        cube(f"Waste erased sign mark {i}",
             (-5.48 + i * 0.48, 5.29, 4.17),
             (0.21, 0.02, 0.32 + 0.12 * i), tarp)

    bpy.ops.object.empty_add(location=(-4.6, -2.2, 0.70))
    cart = bpy.context.object
    cart.name = "SM_Waste_Scavenger_Cart_Rig"
    cart["scavenged_transport"] = "patched four-wheel fuel hauler"
    attach(cube("SM_Waste_Scavenger_Cart", (-4.6, -2.2, 0.81),
                (2.55, 1.35, 0.58), rust, edge=0.06), cart)
    attach(cube("Waste cart patched tarp roof", (-4.6, -2.2, 1.58),
                (2.7, 1.42, 0.11), tarp), cart)
    for side in (-1, 1):
        for fore in (-1, 1):
            attach(cube(f"Waste cart tarp support {side} {fore}",
                        (-4.6 + fore * 1.10, -2.2 + side * 0.58, 1.32),
                        (0.065, 0.065, 0.52), iron), cart)
    for side in (-1, 1):
        for fore in (-1, 1):
            x = -4.6 + fore * 0.94
            y = -2.2 + side * 0.72
            wheel = cylinder(f"Waste cart tire {side} {fore}",
                             (x, y, 0.48), 0.43, 0.18,
                             rubber, vertices=12, rotation=(math.pi / 2, 0, 0))
            attach(wheel, cart)
            attach(cylinder(f"Waste cart iron hub {side} {fore}",
                            (x, y + side * 0.12, 0.48), 0.16, 0.035,
                            iron, vertices=12,
                            rotation=(math.pi / 2, 0, 0)), cart)
    for i in range(3):
        attach(cube(f"Waste cart repair plate {i}",
                    (-5.38 + i * 0.74, -2.98, 0.84),
                    (0.50, 0.025, 0.36), faded), cart)
    attach(cube("Waste cart cargo crate", (-4.6, -2.2, 1.14),
                (1.05, 0.80, 0.37), concrete), cart)
    if variant == 2:
        animate(cart, "location", ((1, (-4.6, -2.2, 0.70)),
                 (24, (-3.25, -2.18, 0.70)),
                 (48, (-1.55, -2.16, 0.71)),
                 (72, (0.40, -2.12, 0.70))))
    else:
        animate(cart, "location", ((1, (-4.6, -2.2, 0.70)),
                 (72, (-3.80, -2.18, 0.70))))
    bpy.ops.object.empty_add(location=(-7, 0.5, 0))
    gust = bpy.context.object
    gust.name = "SM_Waste_Dust_Gust_Rig"
    for i in range(18):
        attach(cube(f"Waste windblown dust streak {i}",
                    (-7 + i % 6 * 0.72, 0.5 + i // 6 * 0.9,
                     0.20 + (i % 3) * 0.26),
                    (0.24 + (i % 3) * 0.17, 0.06, 0.025), dust), gust)
    if variant == 2:
        animate(gust, "location", ((1, (-7, 0.5, 0)),
                 (72, (4.5, 0.5, 0))))
    else:
        animate(gust, "location", ((1, (-7, 0.5, 0)),
                 (72, (-6.4, 0.5, 0))))
    area_light("Waste warm late sun", (-6, -5, 10), 1700, 8,
               color=(1, 0.70, 0.45), target=(0, 3, 1.8))
    area_light("Waste pale sky fill", (5, 1, 9), 900, 8,
               color=(0.70, 0.78, 0.84), target=(0, 3, 1.8))
    cam = camera("Wasteland station inspection camera", (8.6, -12.5, 5.3),
                 (0.1, 3.2, 2.15), lens=36)
    animate(cam, "location", ((1, (8.6, -12.5, 5.3)),
             (72, (7.7 if variant == 2 else 8.5,
                   -11.3 if variant == 2 else -12.3, 5.1))))
    scene["apocalypse_recipe"] = "post-apoc roadside collapse, faded fictional fuel sign, rust patches, improvised brace, scavenger cart, dust"
    scene["apocalypse_variant"] = variant
    return scene
