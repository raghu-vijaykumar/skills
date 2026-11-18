"""Original first-person forest cabin shot in a grounded indie horror lane."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, look_at, material, reset_scene


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored forest cabin candidate")
    scene = reset_scene(spec, background=(0.018, 0.027, 0.038))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.16
    scene.view_settings.view_transform = "AgX"
    earth = material("Cabin wet forest earth", (0.075, 0.083, 0.065), roughness=0.98)
    path = material("Cabin pale gravel path", (0.24, 0.23, 0.20), roughness=1)
    wood = material("Cabin weathered timber", (0.22, 0.17, 0.12), roughness=0.96)
    roofmat = material("Cabin dark shingle", (0.105, 0.12, 0.11), roughness=1)
    pine = material("Cabin deep fir needles", (0.035, 0.09, 0.070), roughness=1)
    pine_far = material("Cabin distant gray fir", (0.08, 0.13, 0.13), roughness=1)
    red = material("Cabin red trail paint", (0.53, 0.025, 0.017), roughness=0.86)
    warm = material("Cabin warm vacant window", (0.72, 0.42, 0.14),
                    emission=(0.88, 0.48, 0.14), emission_strength=2.8)
    black = material("Cabin blackened window", (0.015, 0.023, 0.023), roughness=1)
    moon = material("Cabin desaturated moon fog", (0.12, 0.17, 0.19), roughness=1)

    cube("SM_Cabin_Forest_Floor", (0, 5, -0.22), (70, 75, 0.43), earth)
    # The rough path and paint marks make the cabin readable in low light.
    for i in range(12):
        y = -10 + i * 1.75
        x = 0.4 * math.sin(i * 0.65)
        cube(f"Cabin gravel path tile {i}", (x, y, 0.003),
             (2.9 + 0.12 * (i % 3), 1.65, 0.012), path)
        if i < 8:
            mark = cube(f"SM_Cabin_Red_Trail_Marker_{i}",
                        (x + 1.16, y, 0.018), (0.22, 0.14, 0.017), red)
            mark["route_index"] = i
    cabin = cube("SM_Cabin_Timber_Shell", (0, 9.75, 1.63),
                 (5.7, 4.0, 3.35), wood, edge=0.04)
    cabin["forest_lane"] = "cabin"
    for side in (-1, 1):
        slab = cube(f"Cabin pitched roof side {side}",
                    (side * 1.49, 9.75, 3.82), (3.42, 4.75, 0.22), roofmat)
        slab.rotation_euler[1] = side * 0.28
    for i in range(8):
        cube(f"Cabin front weathered seam {i}",
             (-2.5 + i * 0.72, 7.73, 1.75), (0.022, 0.02, 3.1), roofmat)
    cube("Cabin porch deck", (0, 6.85, 0.24),
         (5.2, 2.2, 0.22), wood)
    cube("Cabin porch step", (0, 5.67, 0.10),
         (3.6, 0.34, 0.17), wood)
    for side in (-1, 1):
        cube(f"Cabin porch upright {side}", (side * 2.35, 6.7, 1.90),
             (0.17, 0.19, 3.8), wood)
    cube("SM_Cabin_Closed_Door", (0.65, 7.70, 1.40),
         (1.18, 0.05, 2.70), roofmat)
    cube("Cabin black window recess", (-1.55, 7.65, 2.05),
         (1.15, 0.06, 1.15), black)
    pane = cube("SM_Cabin_Window_Glow", (-1.55, 7.61, 2.05),
                (1.02, 0.025, 1.02), warm)
    for x in (-2.15, -0.94):
        cube(f"Cabin window upright {x}", (x, 7.56, 2.05),
             (0.08, 0.08, 1.38), wood)
    cube("Cabin window crossbar", (-1.55, 7.55, 2.05),
         (1.34, 0.08, 0.08), wood)
    window_light = area_light("SM_Cabin_Window_Light", (-1.5, 6.8, 2.2),
                              460, 2.2, color=(1.0, 0.58, 0.24),
                              target=(-1.6, 4.0, 0.2))
    if variant == 2:
        for frame, on in ((1, False), (42, False), (45, True),
                          (51, False), (55, True), (72, True)):
            pane.hide_render = on
            pane.keyframe_insert(data_path="hide_render", frame=frame)
        animate(window_light.data, "energy", ((1, 460), (42, 460),
                  (45, 0), (51, 480), (55, 0), (72, 0)))
    # Sparse chunky firs frame the path; far rows use a paler silhouette.
    for i in range(30):
        side = -1 if i % 2 else 1
        y = -8.7 + (i // 2) * 1.82
        x = side * (3.7 + 0.9 * ((i * 7) % 4))
        height = 3.6 + (i % 5) * 0.45
        trunk = cylinder(f"SM_Cabin_Fir_Trunk_{i}",
                         (x, y, height * 0.39), 0.14,
                         height * 0.78, wood, vertices=7)
        trunk["fir_index"] = i
        for tier in range(3):
            bpy.ops.mesh.primitive_cone_add(vertices=7,
                       radius1=1.05 - tier * 0.16,
                       radius2=0, depth=1.65,
                       location=(x, y, height * (0.46 + tier * 0.17)))
            crown = bpy.context.object
            crown.name = f"Cabin fir crown {i} {tier}"
            crown.data.materials.append(pine_far if i > 20 else pine)
    for i in range(6):
        x = -12 + i * 4.6
        cube(f"Cabin distant mist plane {i}",
             (x, 29.0 + i % 2, 2.2), (3.9, 0.08, 4.4), moon)
    # A low cool fill retains the cabin silhouette after its practical light fails.
    area_light("Cabin cool night fill", (-4.0, 1.0, 7.5), 430, 7.0,
               color=(0.52, 0.69, 0.84), target=(0, 8.5, 1.5))
    cam = camera("Forest cabin first-person camera", (1.38, -10.4, 1.78),
                 (0, 9.0, 1.83), lens=38)
    if variant == 2:
        animate(cam, "location", ((1, (1.38, -10.4, 1.78)),
                 (24, (1.10, -8.2, 1.75)),
                 (45, (0.87, -6.2, 1.73)),
                 (72, (0.48, -3.9, 1.70))))
        animate(cam, "rotation_euler", ((1, tuple(cam.rotation_euler)),
                 (24, (cam.rotation_euler.x, cam.rotation_euler.y,
                       cam.rotation_euler.z + 0.015)),
                 (45, (cam.rotation_euler.x, cam.rotation_euler.y,
                       cam.rotation_euler.z - 0.025)),
                 (72, (cam.rotation_euler.x, cam.rotation_euler.y,
                       cam.rotation_euler.z + 0.018))))
    else:
        animate(cam, "location", ((1, (1.38, -10.4, 1.78)),
                 (72, (1.15, -8.9, 1.78))))
    bpy.ops.object.light_add(type="SPOT", location=(1.22, -10.10, 1.61))
    flashlight = bpy.context.object
    flashlight.name = "SM_Cabin_Flashlight_Cone"
    flashlight.data.energy = 3200
    flashlight.data.spot_size = 0.85
    flashlight.data.spot_blend = 0.55
    flashlight.data.color = (0.78, 0.87, 1.0)
    look_at(flashlight, (0, 8.5, 1.35))
    bpy.context.view_layer.update()
    world = flashlight.matrix_world.copy()
    flashlight.parent = cam
    flashlight.matrix_world = world
    scene["indie_recipe"] = "first-person cabin forest lane, red path markers, fir silhouettes, failing window, handheld flashlight"
    scene["indie_variant"] = variant
    return scene
