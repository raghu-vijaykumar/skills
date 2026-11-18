"""Original empty poolrooms corridor with repeating bays and a slow wrongward drift."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, material, reset_scene


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored liminal pool candidate")
    scene = reset_scene(spec, background=(0.08, 0.15, 0.14))
    scene.view_settings.view_transform = "AgX"
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.34
    cream = material("Poolrooms yellowed ceramic", (0.60, 0.62, 0.46), roughness=0.86)
    pale = material("Poolrooms lighter grout", (0.38, 0.47, 0.40), roughness=0.89)
    teal = material("Poolrooms glossy shallow water", (0.10, 0.44, 0.48),
                    roughness=0.15)
    water_shader = teal.node_tree.nodes.get("Principled BSDF")
    water_shader.inputs["Coat Weight"].default_value = 0.65
    water_shader.inputs["Coat Roughness"].default_value = 0.10
    water_shader.inputs["Transmission Weight"].default_value = 0.12
    foam = material("Poolrooms faint water glints", (0.42, 0.81, 0.80),
                    emission=(0.32, 0.58, 0.55), emission_strength=0.24)
    ceiling = material("Poolrooms washed ceiling", (0.61, 0.67, 0.58), roughness=0.91)
    lamp = material("Poolrooms fluorescent strips", (0.78, 0.91, 0.76),
                    emission=(0.80, 1.0, 0.81), emission_strength=3.0)
    dark = material("Poolrooms endless far opening", (0.035, 0.11, 0.12), roughness=1)

    # Five repeated bays and vacant walkways carry the architecture, without props.
    cube("SM_Pool_Hall_Floor", (0, 7.2, -0.20), (10.5, 33, 0.36), cream)
    cube("Pool left wall", (-5.2, 7.2, 2.05), (0.18, 33, 4.20), cream)
    cube("Pool right wall", (5.2, 7.2, 2.05), (0.18, 33, 4.20), cream)
    cube("Pool ceiling", (0, 7.2, 4.20), (10.5, 33, 0.18), ceiling)
    cube("SM_Pool_Water", (0, 7.4, -0.015), (3.32, 29.5, 0.035), teal)
    for side in (-1, 1):
        cube(f"Pool basin rim {side}", (side * 1.77, 7.4, 0.13),
             (0.26, 29.5, 0.24), cream, edge=0.035)
        for i in range(15):
            y = -6.5 + i * 2.0
            cube(f"Pool walkway grout {side} {i}",
                 (side * 3.46, y, -0.008), (3.12, 0.022, 0.01), pale)
    for i in range(23):
        y = -7.0 + i * 1.3
        cube(f"Pool water cross tile {i}", (0, y, 0.008),
             (3.16, 0.014, 0.006), pale)
    for i in range(5):
        y = i * 5.1
        for side in (-1, 1):
            pillar = cube(f"SM_Pool_Bay_{i}_Pillar_{side}",
                          (side * 3.18, y, 2.03),
                          (0.46, 0.72, 4.06), cream, edge=0.025)
            pillar["repeated_module"] = i
            cube(f"Pool bay {i} wall recess {side}",
                 (side * 4.75, y + 2.2, 1.85),
                 (0.035, 2.9, 2.7), pale)
        header = cube(f"SM_Pool_Bay_{i}_Lintel", (0, y, 3.90),
                      (6.68, 0.72, 0.56), cream, edge=0.025)
        header["repeated_module"] = i
        tube = cube(f"SM_Pool_Fluorescent_{i}", (0, y + 2.2, 4.05),
                    (4.62, 0.13, 0.055), lamp)
        tube["fluorescent_bay"] = i
    cube("SM_Pool_Far_Opening", (0, 23.33, 2.03),
         (5.5, 0.07, 3.7), dark)
    # A thin dark opening after repeated identical bays implies unending rooms.
    cube("Pool far nested doorway", (0.26, 23.25, 1.99),
         (3.70, 0.09, 3.28), cream)
    cube("Pool far nested void", (0.26, 23.14, 1.94),
         (3.12, 0.06, 2.95), dark)

    glints = []
    for i in range(9):
        y = -4.3 + i * 3.0
        x = (-1) ** i * (0.26 + (i % 3) * 0.31)
        glint = cube(f"Pool water glint {i}", (x, y, 0.022),
                     (0.47 + (i % 3) * 0.20, 0.035, 0.006), foam)
        glints.append(glint)
        if variant == 2:
            animate(glint, "location", ((1, (x, y, 0.022)),
                                        (36, (x + 0.18, y + 0.20, 0.022)),
                                        (72, (x - 0.13, y + 0.44, 0.022))))
    lights = []
    for i in range(5):
        y = i * 5.1 + 2.1
        light = area_light(f"Pool fluorescent area {i}", (0, y, 3.95),
                           430, 4.0, color=(0.68, 0.96, 0.86),
                           target=(0, y, 0))
        lights.append(light)
    if variant == 2:
        animate(lights[2].data, "energy", ((1, 430), (28, 430),
                                            (35, 70), (39, 470), (72, 430)))
    cam = camera("Liminal pool inspection camera", (3.05, -8.9, 1.96),
                 (0, 12.0, 1.86), lens=34)
    if variant == 2:
        # A long, steady push is the action: the repeated bays never resolve.
        animate(cam, "location", ((1, (3.05, -8.9, 1.96)),
                                  (36, (2.65, -6.8, 1.96)),
                                  (72, (2.24, -4.1, 1.96))))
    else:
        animate(cam, "location", ((1, (3.05, -8.9, 1.96)),
                                  (72, (2.85, -7.8, 1.96))))
    scene["liminal_recipe"] = "empty modular poolrooms, repeated bays, fluorescent wrongness, endless opening"
    scene["liminal_variant"] = variant
    return scene
