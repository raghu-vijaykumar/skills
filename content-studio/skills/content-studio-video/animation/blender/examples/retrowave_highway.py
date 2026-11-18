"""Original neon retrowave highway with a chrome car crossing a grid horizon."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def attach(obj, parent):
    # Preserve a designed car silhouette while the whole rig drives down the grid.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def ridge(name, y, low, peaks, mat):
    """A folded mesh gives the horizon a hand-authored synthetic skyline."""
    verts = [(-20, y, low)]
    verts.extend((x, y, height) for x, height in peaks)
    verts.append((20, y, low))
    verts.extend(((20, y, -0.5), (-20, y, -0.5)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, (), (tuple(range(len(verts))),))
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown retrowave highway candidate")
    scene = reset_scene(spec, background=(0.22, 0.08, 0.24))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.48
    road = material("Retro midnight violet grid ground", (0.030, 0.022, 0.074),
                    metallic=0.12, roughness=0.52)
    cyan = material("Retro electric cyan grid", (0.03, 0.75, 0.84),
                    emission=(0.04, 0.75, 0.94), emission_strength=2.4)
    pink = material("Retro neon magenta lane", (0.89, 0.09, 0.49),
                    emission=(0.94, 0.10, 0.53), emission_strength=2.8)
    sun = material("Retro peach striped sun", (1.0, 0.32, 0.17),
                   emission=(1.0, 0.38, 0.18), emission_strength=2.8)
    sun_cut = material("Retro dusk stripe shadow", (0.18, 0.055, 0.24),
                       emission=(0.18, 0.055, 0.24), emission_strength=0.4)
    far = material("Retro purple mountain silhouette", (0.055, 0.034, 0.12),
                   roughness=1)
    near = material("Retro dark mountain silhouette", (0.032, 0.027, 0.080),
                    roughness=1)
    chrome = material("Retro satin chrome coupe", (0.48, 0.60, 0.68),
                      metallic=0.86, roughness=0.24)
    dark = material("Retro tire and smoked window", (0.025, 0.035, 0.060),
                    metallic=0.12, roughness=0.51)
    red = material("Retro rear red light", (0.94, 0.06, 0.14),
                   emission=(1.0, 0.025, 0.09), emission_strength=2.4)

    cube("SM_Retro_Grid_Ground", (0, 8, -0.12), (52, 66, 0.22), road)
    # Perpendicular emissive rulings preserve perspective in the actual 3D camera.
    for i in range(-15, 16):
        cube(f"Retro cyan longitudinal grid {i}",
             (i * 1.5, 4.0, 0.006), (0.028, 34.0, 0.013), cyan)
    for i in range(23):
        cube(f"Retro cyan cross grid {i}",
             (0, -11.0 + i * 1.45, 0.007), (46.0, 0.029, 0.013), cyan)
    for side in (-1, 1):
        cube(f"Retro magenta highway edge {side}",
             (side * 2.85, 4.0, 0.030), (0.065, 34.0, 0.025), pink)
        cube(f"Retro dark road divider {side}",
             (side * 2.33, 4.0, 0.017), (0.12, 34.0, 0.010), dark)
    cylinder("SM_Retro_Striped_Sunset", (0, 20.0, 6.2),
             3.65, 0.12, sun, vertices=64, rotation=(math.pi / 2, 0, 0))
    for i, offset in enumerate((-2.45, -1.95, -1.38, -0.72, 0.04)):
        chord = 2 * math.sqrt(3.65 ** 2 - offset ** 2)
        cube(f"Retro sunset dusk stripe {i}", (0, 19.90, 6.2 + offset),
             (chord, 0.04, 0.11 + 0.02 * i), sun_cut)
    ridge("Retro far mountain ridge", 18.9, 0.2,
          ((-16, 2.5), (-12, 1.2), (-9, 3.0), (-5, 0.7),
           (-2, 2.2), (1, 0.5), (5, 2.7), (9, 1.1), (13, 2.8), (17, 1.3)), far)
    ridge("Retro near mountain ridge", 16.4, 0.2,
          ((-18, 1.2), (-14, 2.5), (-10, 0.7), (-6, 1.9),
           (-2, 0.5), (3, 1.7), (7, 0.3), (12, 2.0), (17, 0.8)), near)

    # A spare chrome gateway frames the car's journey without a cyberpunk city.
    for side in (-1, 1):
        cube(f"Retro chrome gate post {side}",
             (side * 3.5, 6.25, 1.85), (0.14, 0.18, 3.7), chrome)
        cube(f"Retro magenta gate post glow {side}",
             (side * 3.40, 6.16, 1.85), (0.025, 0.025, 3.45), pink)
    cube("SM_Retro_Neon_Gate", (0, 6.25, 3.65),
         (7.15, 0.17, 0.16), chrome, edge=0.04)
    cube("Retro gate crown glow", (0, 6.16, 3.78),
         (7.05, 0.03, 0.035), pink)

    bpy.ops.object.empty_add(location=(0, 0, 0))
    car = bpy.context.object
    car.name = "SM_Retro_Chrome_Coupe_Rig"
    car["direction"] = "drives toward the synthetic sunset"
    attach(cube("SM_Retro_Chrome_Coupe_Body", (0, -2.4, 0.72),
                (2.05, 3.18, 0.52), chrome, edge=0.20), car)
    attach(cube("Retro smoked cockpit", (0, -2.08, 1.19),
                (1.58, 1.55, 0.43), dark, edge=0.19), car)
    attach(cube("Retro chrome windshield line", (0, -2.81, 1.14),
                (1.38, 0.045, 0.065), cyan), car)
    attach(cube("Retro rear spoiler", (0, -3.96, 1.13),
                (2.35, 0.17, 0.09), chrome, edge=0.035), car)
    for side in (-1, 1):
        attach(cube(f"Retro red rear light {side}",
                    (side * 0.75, -4.02, 0.78),
                    (0.40, 0.045, 0.11), red), car)
        attach(cube(f"Retro cyan rocker stripe {side}",
                    (side * 1.035, -2.39, 0.60),
                    (0.025, 2.62, 0.045), cyan), car)
        for fore in (-1, 1):
            wheel = attach(cylinder(f"SM_Retro_Coupe_Wheel_{side}_{fore}",
                                    (side * 1.08, -2.40 + fore * 1.06, 0.43),
                                    0.40, 0.17, dark, vertices=28,
                                    rotation=(0, math.pi / 2, 0)), car)
            attach(cylinder(f"Retro chrome wheel hub {side} {fore}",
                            (side * 1.18, -2.40 + fore * 1.06, 0.43),
                            0.20, 0.025, chrome, vertices=28,
                            rotation=(0, math.pi / 2, 0)), car)
            if variant == 2:
                animate(wheel, "rotation_euler", ((1, (0, math.pi / 2, 0)),
                        (72, (9.5, math.pi / 2, 0))))
    if variant == 2:
        animate(car, "location", ((1, (0, 0, 0)),
                (36, (0, 3.6, 0)), (72, (0, 7.2, 0))))
    else:
        animate(car, "location", ((1, (0, 0, 0)),
                (72, (0, 0.25, 0))))

    area_light("Retro coral sunset key", (1, 15, 9), 1420, 8,
               color=(1.0, 0.42, 0.27), target=(0, 1.2, 0.8))
    area_light("Retro electric cyan car rim", (-5, -3, 6), 1030, 5,
               color=(0.13, 0.85, 1.0), target=(0, 0, 0.9))
    area_light("Retro magenta horizon fill", (6, 2, 7), 560, 7,
               color=(1.0, 0.14, 0.65), target=(0, 3, 1.5))
    cam = camera("Retro highway follow camera", (5.0, -11.2, 3.2),
                 (0, 4.8, 1.75), lens=34)
    animate(cam, "location", ((1, (5.0, -11.2, 3.2)),
             (72, (4.75 if variant == 2 else 4.98,
                   -10.45 if variant == 2 else -11.16, 3.15))))
    scene["retro_recipe"] = "striped sunset, perspective cyan grid, chrome coupe, magenta gateway, dusk mountains"
    scene["retro_variant"] = variant
    return scene
