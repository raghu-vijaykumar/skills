"""Original historically inspired Viking longship crossing a rocky fjord."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, look_at, material, reset_scene


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


def hull_mesh(name, timber):
    # The raised ends, curved gunwales, and narrow keel carry the ship silhouette.
    positions = [(-3.2, 0.0, 1.12), (-2.8, -0.65, 0.62),
                 (-1.8, -0.92, 0.48), (1.8, -0.92, 0.48),
                 (2.8, -0.65, 0.62), (3.2, 0.0, 1.20),
                 (-2.8, 0.65, 0.62), (-1.8, 0.92, 0.48),
                 (1.8, 0.92, 0.48), (2.8, 0.65, 0.62),
                 (-1.9, 0.0, 0.00), (1.9, 0.0, 0.00)]
    faces = [(0, 1, 2, 10), (2, 3, 11, 10), (3, 4, 5, 11),
             (0, 10, 6), (6, 10, 11, 7), (7, 11, 5, 9, 8),
             (1, 6, 7, 2), (2, 7, 8, 3), (3, 8, 9, 4),
             (4, 9, 5), (0, 6, 1)]
    mesh = bpy.data.meshes.new("Longship clinker hull mesh")
    mesh.from_pydata(positions, [], faces)
    mesh.materials.append(timber)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj["period_hull"] = "raised-end narrow-keel longship"
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored Viking fjord candidate")
    scene = reset_scene(spec, background=(0.43, 0.55, 0.63))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.72
    sea = material("Viking cold slate sea", (0.10, 0.23, 0.27),
                   metallic=0.12, roughness=0.36)
    timber = material("Viking tarred oak timber", (0.23, 0.13, 0.065), roughness=0.88)
    edge = material("Viking weathered plank edge", (0.39, 0.25, 0.13), roughness=0.9)
    sail = material("Viking undyed wool sail", (0.72, 0.67, 0.55), roughness=0.97)
    red = material("Viking madder dyed wool", (0.47, 0.075, 0.065), roughness=0.96)
    iron = material("Viking forged iron fitting", (0.13, 0.14, 0.14),
                    metallic=0.65, roughness=0.75)
    rock = material("Viking fjord gray rock", (0.30, 0.35, 0.34), roughness=1)
    foam = material("Viking pale water ripple", (0.62, 0.76, 0.76), roughness=0.65)

    cube("SM_Viking_Fjord_Water", (0, 3, -0.18), (50, 38, 0.35), sea)
    for i in range(7):
        x = -12 + i * 4.0
        cube(f"Viking distant rocky shore {i}", (x, 13 + i % 3, 1.2),
             (3.7, 2.8, 2.6 + i % 2), rock, edge=0.34)
    for i in range(10):
        cube(f"Viking water glint {i}",
             (-7 + i * 1.5, -3.0 + (i % 4) * 2.6, 0.013),
             (0.75 + (i % 3) * 0.15, 0.06, 0.015), foam)

    bpy.ops.object.empty_add(location=(-1.75, 1.4, 0.0))
    ship = bpy.context.object
    ship.name = "SM_Viking_Longship_Rig"
    ship["historical_lane"] = "Viking longship, circa ninth to eleventh century"
    attach(hull_mesh("SM_Viking_Clinker_Hull", timber), ship)
    for side in (-1, 1):
        for level in range(3):
            y = side * (0.68 - level * 0.18)
            z = 0.33 + level * 0.13
            attach(cube(f"Viking clinker strake {side} {level}",
                        (0, y, z), (5.2 - level * 0.2, 0.11, 0.10),
                        edge), ship)
        for i in range(6):
            x = -2.25 + i * 0.89
            shield = cylinder(f"Viking round shield {side} {i}",
                              (x, side * 0.92, 0.67), 0.34, 0.06,
                              red if i % 2 == 0 else sail, vertices=20,
                              rotation=(math.pi / 2, 0, 0))
            attach(shield, ship)
            attach(cylinder(f"Viking iron shield boss {side} {i}",
                            (x, side * 0.965, 0.67), 0.10, 0.075,
                            iron, vertices=12,
                            rotation=(math.pi / 2, 0, 0)), ship)
    attach(cylinder("SM_Viking_Timber_Mast", (0, 0, 2.2), 0.13, 3.6,
                    timber, vertices=12), ship)
    attach(cube("Viking square sail yard", (0, 0, 3.7),
                (3.5, 0.13, 0.13), timber), ship)
    sail_panel = attach(cube("SM_Viking_Wool_Square_Sail", (0, 0.015, 2.62),
                             (3.25, 0.06, 2.12), sail), ship)
    for i in range(4):
        attach(cube(f"Viking red sail stripe {i}",
                    (-1.28 + i * 0.85, -0.029, 2.62),
                    (0.36, 0.015, 2.07), red), ship)
    for side in (-1, 1):
        for fore in (-1, 1):
            attach(cube(f"Viking wool rigging {side} {fore}",
                        (side * 0.95, fore * 0.22, 2.35),
                        (0.025, 0.025, 2.7), iron), ship)
    # Oars and round shields are readable historical cues, without invented horns.
    for side in (-1, 1):
        for i in range(4):
            oar = cube(f"Viking rowing oar {side} {i}",
                       (-1.7 + i * 1.08, side * 1.3, 0.40),
                       (0.06, 1.8, 0.06), edge)
            oar.rotation_euler[0] = side * 0.16
            attach(oar, ship)
    attach(cube("Viking raised dragon prow", (3.08, 0, 1.18),
                (0.33, 0.22, 1.26), timber, edge=0.08), ship)
    if variant == 2:
        animate(ship, "location", ((1, (-1.75, 1.4, 0)),
                 (24, (-0.60, 1.5, 0.04)), (48, (0.70, 1.58, 0)),
                 (72, (1.75, 1.68, 0.03))))
        animate(ship, "rotation_euler", ((1, (0, 0, -0.025)),
                 (48, (0, 0, 0.035)), (72, (0, 0, -0.018))))
    else:
        animate(ship, "location", ((1, (-1.75, 1.4, 0)),
                 (72, (-1.05, 1.43, 0.02))))
    area_light("Viking overcast fjord key", (-6, -5, 9), 1350, 8,
               color=(0.86, 0.90, 1.0), target=(0, 1, 1.6))
    area_light("Viking warm horizon fill", (6, 7, 8), 850, 9,
               color=(1.0, 0.78, 0.62), target=(0, 2, 2.0))
    cam = camera("Viking fjord inspection camera", (7.2, -10.3, 4.0),
                 (0, 1.6, 1.65), lens=42)
    cam.keyframe_insert(data_path="rotation_euler", frame=1)
    animate(cam, "location", ((1, (7.2, -10.3, 4.0)),
             (72, (6.8 if variant == 2 else 7.1,
                   -9.5 if variant == 2 else -10.2, 3.9))))
    if variant == 2:
        # Follow the ship late in the crossing so its shield line stays in frame.
        look_at(cam, (2.7, 1.6, 1.65))
        cam.keyframe_insert(data_path="rotation_euler", frame=72)
    scene["historical_recipe"] = "Viking longship with narrow keel, clinker strakes, round shields, oars, wool square sail"
    scene["historical_variant"] = variant
    scene["historical_period"] = "circa ninth to eleventh century Scandinavia"
    return scene
