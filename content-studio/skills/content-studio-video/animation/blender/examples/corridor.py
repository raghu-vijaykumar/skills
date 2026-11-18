"""Original atmospheric corridor built from repeated modules and practical lighting."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.005, 0.012, 0.02))
    wall = material("Blue concrete panels", (0.075, 0.12, 0.15), metallic=0.05, roughness=0.9)
    trim = material("Dark iron framing", (0.045, 0.09, 0.105), metallic=0.75, roughness=0.36)
    floor = material("Worn slate floor", (0.075, 0.105, 0.12), metallic=0.1, roughness=0.42)
    pipe = material("Oxidized pipe", (0.11, 0.16, 0.17), metallic=0.72, roughness=0.41)
    glow = material("Fluorescent practical", (0.68, 0.91, 0.94), emission=(0.55, 0.85, 1),
                    emission_strength=4)
    amber = material("Amber line", (0.63, 0.3, 0.07), metallic=0.35, roughness=0.38)
    red = material("Red end light", (0.4, 0.02, 0.02), emission=(1, 0.04, 0.025),
                   emission_strength=4)

    cube("Corridor floor", (0, 8, -0.13), (4.7, 23, 0.25), floor, 0.03)
    cube("Ceiling", (0, 8, 3.35), (4.7, 23, 0.18), wall)
    for x, side in [(-2.31, "Left"), (2.31, "Right")]:
        cube(side + " long wall", (x, 8, 1.65), (0.18, 23, 3.3), wall)
        for z in (0.62, 2.62):
            cylinder(side + " utility pipe", (x * 0.9, 8, z), 0.045, 22.2, pipe,
                     vertices=16, rotation=(1.570796, 0, 0))
        for bay in range(7):
            y = bay * 3
            cube(side + f" wall panel {bay}", (x * 0.955, y + 1.5, 1.55),
                 (0.09, 2.52, 2.13), wall, 0.025)
            cube(side + f" lower rail {bay}", (x * 0.89, y + 1.5, 0.33),
                 (0.10, 2.7, 0.1), trim, 0.015)

    for bay in range(8):
        y = bay * 3
        for x in (-2.05, 2.05):
            cube(f"Arch pillar {bay} {x}", (x, y, 1.68), (0.34, 0.3, 3.3), trim, 0.035)
        cube(f"Arch beam {bay}", (0, y, 3.1), (4.42, 0.32, 0.38), trim, 0.035)
        cube(f"Floor seam {bay}", (0, y, 0.014), (4.15, 0.045, 0.02), pipe)
        if bay < 7:
            cube(f"Ceiling diffuser {bay}", (0, y + 1.5, 3.18),
                 (0.32, 1.6, 0.055), glow, 0.025)
            cube(f"Floor guide {bay}", (0, y + 1.5, 0.016),
                 (0.045, 2.25, 0.018), amber)

    for y in (4.5, 10.5, 16.5):
        for x in (-2.16, 2.16):
            cube(f"Service door {x} {y}", (x, y, 1.31), (0.075, 1.16, 2.45),
                 trim, 0.035)
            cube(f"Door handle {x} {y}", (x * 0.94, y + 0.29, 1.16),
                 (0.08, 0.23, 0.075), amber, 0.012)

    cube("End door", (0, 19.25, 1.46), (2.6, 0.16, 2.9), trim, 0.05)
    cube("End door light", (0, 19.12, 2.82), (1.4, 0.05, 0.13), red, 0.02)
    for x in (-1.16, 1.16):
        cube(f"End door seam {x}", (x, 19.12, 1.45), (0.07, 0.05, 2.6), pipe)

    cam = camera("Hero camera", (0, -2.2, 1.72), (0, 17, 1.6), lens=27)
    cam.keyframe_insert(data_path="location", frame=1)
    cam.location.y = 1.3
    cam.keyframe_insert(data_path="location", frame=96)
    for bay in range(7):
        y = bay * 3 + 1.5
        light = area_light("Flicker light" if bay == 2 else f"Ceiling light {bay}",
                           (0, y, 3.03), 330, 2.2,
                           color=(0.53, 0.78, 1.0), target=(0, y, 0.3))
        if bay == 2:
            for frame, power in [(1, 330), (36, 330), (38, 35), (40, 330),
                                 (51, 330), (53, 45), (56, 330), (96, 330)]:
                light.data.energy = power
                light.data.keyframe_insert(data_path="energy", frame=frame)
    area_light("End warning", (0, 18.5, 2.7), 620, 2.0,
               color=(1, 0.16, 0.09), target=(0, 16.5, 1.4))
    return scene
