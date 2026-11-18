"""Original cosmic horror stage: a tiny witness below an impossible void aperture."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def ring(name, location, width, height, thickness, mat, tilt=0):
    """A vertically mounted, stretched torus keeps the portal legible at GIF scale."""
    bpy.ops.mesh.primitive_torus_add(major_segments=72, minor_segments=10,
                                     location=location, rotation=(math.pi / 2, 0, tilt),
                                     major_radius=1, minor_radius=thickness)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (width, height, 1)
    obj.data.materials.append(mat)
    return obj


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2, 3):
        raise ValueError("Unknown authored cosmic aperture candidate")
    scene = reset_scene(spec, background=(0.001, 0.002, 0.011))
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.18
    scene.view_settings.view_transform = "AgX"
    stone = material("Abyss blue black stone", (0.013, 0.027, 0.060), roughness=0.89)
    deep = material("Abyss deeper face", (0.002, 0.006, 0.019), roughness=0.94)
    edge = material("Sickly old gold", (0.30, 0.24, 0.065), metallic=0.58,
                    roughness=0.44, emission=(0.65, 0.46, 0.055), emission_strength=0.27)
    lumen = material("Aperture sickly gold seam", (0.70, 0.53, 0.11),
                     emission=(1.0, 0.70, 0.10), emission_strength=3.5)
    void = material("Unknowable black core", (0.0004, 0.0004, 0.0015), roughness=1)
    witness = material("Witness blue silhouette", (0.028, 0.065, 0.11), roughness=0.81)

    # Oversized disconnected architecture and a very small human establish wrong scale.
    cube("SM_Cosmic_Floor", (0, 0, -0.23), (21, 22, 0.42), deep)
    for i in range(9):
        y = -8.0 + i * 2.1
        slab = cube(f"Cosmic misregistered slab {i}",
                    ((-1) ** i * (0.10 + i * 0.028), y, 0.015 + (i % 3) * 0.035),
                    (3.5 + i * 0.25, 1.42, 0.19), stone, edge=0.035)
        slab.rotation_euler.z = (-1) ** i * (0.012 + i * 0.008)
    for side in (-1, 1):
        for i in range(4):
            x = side * (3.8 + i * 1.4)
            p = cube(f"Cosmic floating monolith {side} {i}",
                     (x, 0.3 + i * 1.7, 2.4 + i * 0.42),
                     (0.42, 0.48, 4.8 + i * 0.8), stone, edge=0.055)
            p.rotation_euler.y = side * (0.06 + i * 0.045)
            cube(f"Cosmic monolith gold cut {side} {i}",
                 (x, -0.01 + i * 1.7, 3.1 + i * 0.45),
                 (0.06, 0.04, 0.55), edge)

    core = sphere("SM_Cosmic_Void", (0, 4.15, 4.75), 1,
                  void, segments=64, rings=32, scale=(2.53, 0.38, 3.56))
    core["unknowable_form"] = True
    outer = ring("SM_Cosmic_Broken_Aperture", (0, 3.9, 4.75),
                 2.88, 3.90, 0.072, stone)
    ring("Cosmic broken aperture gold rim", (0.0, 3.68, 4.75),
         2.66, 3.68, 0.027, edge, tilt=0.09)
    inner_ring = ring("Cosmic off-axis inner ring", (0.24, 3.46, 4.85),
                      1.92, 2.88, 0.032, edge, tilt=-0.19)
    if variant == 3:
        key(inner_ring, "rotation_euler",
            ((1, (math.pi / 2, 0, -0.19)),
             (36, (math.pi / 2, 0, 0.12)),
             (72, (math.pi / 2, 0, 0.43))))
    shards = []
    for i in range(9):
        angle = 2 * math.pi * i / 9
        x = 3.25 * math.cos(angle)
        z = 4.75 + 4.28 * math.sin(angle)
        shard = cube(f"Cosmic detached orbit shard {i}", (x, 3.65, z),
                     (0.25, 0.25, 0.60 + (i % 3) * 0.24), stone, edge=0.018)
        shard.rotation_euler.y = 0.32 + angle
        shards.append(shard)
    if variant == 3:
        orbit = bpy.data.objects.new("Cosmic broken orbit control", None)
        scene.collection.objects.link(orbit)
        orbit.location = (0, 3.65, 4.75)
        bpy.context.view_layer.update()
        for shard in shards:
            shard.parent = orbit
            shard.matrix_parent_inverse = orbit.matrix_world.inverted()
        key(orbit, "rotation_euler", ((1, (0, -0.18, 0)),
                                       (72, (0, 0.37, 0))))
    # A narrow vertical wound reveals little of the object beyond the rings.
    slit = cube("SM_Cosmic_Gold_Slit", (0, 3.16, 4.75),
                (0.21 if variant == 1 else 0.13, 0.06, 3.0), lumen, edge=0.04)
    key(slit, "scale", ((1, (0.35 if variant == 3 else 1, 1, 0.66)),
                         (38, (2.25 if variant == 3 else 1.45 if variant == 2 else 1, 1, 1)),
                         (72, (0.7 if variant >= 2 else 1, 1, 0.80))))
    if variant >= 2:
        # Rotating disconnected bars imply an impossible iris without explaining its shape.
        iris = bpy.data.objects.new("Cosmic iris motion control", None)
        scene.collection.objects.link(iris)
        iris.location = (0, 3.08, 4.75)
        for i in range(7):
            angle = 2 * math.pi * i / 7
            blade = cube(f"Cosmic iris blade {i}",
                         (math.cos(angle) * 1.05, 3.04,
                          4.75 + math.sin(angle) * 1.59),
                         (0.17, 0.12, 1.16), deep, edge=0.02)
            blade.parent = iris
            blade.matrix_parent_inverse = iris.matrix_world.inverted()
            blade.rotation_euler.y = angle + 0.29
        key(iris, "rotation_euler", ((1, (0, 0, -0.08)),
                                      (36, (0, 0, 0.25 if variant == 3 else 0.13)),
                                      (72, (0, 0, 0.83 if variant == 3 else 0.33))))
        # Sparse glints and partly hidden tendrils suggest depth, never a complete creature.
        stars = bpy.data.objects.new("Cosmic impossible depth control", None)
        scene.collection.objects.link(stars)
        stars.location = (0, 3.31, 4.75)
        for i in range(22):
            angle = i * 2.39996
            radius = 0.18 + 1.7 * math.sqrt((i + 0.5) / 22)
            x = math.cos(angle) * radius
            z = math.sin(angle) * radius * 1.45
            point = sphere(f"Cosmic unreachable glint {i}", (x, -0.03, z),
                           0.019 if i % 4 else 0.032, lumen,
                           segments=8, rings=4)
            point.parent = stars
        key(stars, "rotation_euler", ((1, (0, 0, -0.04)),
                                       (72, (0, 0, 0.48 if variant == 3 else 0.13))))
        for side in (-1, 1):
            curve = bpy.data.curves.new(f"Cosmic unseen tendril {side}", "CURVE")
            curve.dimensions = "3D"
            curve.bevel_depth = 0.095
            curve.bevel_resolution = 2
            path = curve.splines.new("POLY")
            path.points.add(7)
            for i, point in enumerate(path.points):
                t = i / 7
                point.co = (side * (1.1 + 5.2 * t), 4.46 + 0.4 * t,
                            5.0 + 2.4 * math.sin(t * math.pi * 1.2) + side * 0.28, 1)
            tendril = bpy.data.objects.new(f"Cosmic partial silhouette {side}", curve)
            scene.collection.objects.link(tendril)
            tendril.data.materials.append(stone)
    else:
        iris = None

    # The witness is deliberately under 1.5 m while the aperture spans 8 m.
    body = cylinder("SM_Cosmic_Witness", (-0.48, -4.5, 0.78),
                    0.16, 1.05, witness, vertices=10)
    head = sphere("Cosmic witness head", (-0.48, -4.5, 1.44),
                  0.20, witness, segments=16, rings=8)
    for obj in (body, head):
        obj["tiny_witness"] = True
    for side in (-1, 1):
        cube(f"Cosmic witness leg {side}",
             (-0.48 + side * 0.10, -4.5, 0.19), (0.09, 0.10, 0.42), witness)
    area_light("Cosmic abyss blue fill", (-4, -7, 7), 650, 8,
               color=(0.12, 0.29, 0.78), target=(0, 1, 2))
    area_light("Cosmic sickly gold rim", (2, 2.4, 8.5), 980, 4,
               color=(1, 0.64, 0.13), target=(0, 3, 5))
    area_light("Cosmic witness edge", (-1, -2.5, 3.2), 90, 2,
               color=(0.30, 0.58, 0.92), target=(-0.48, -4.5, 0.8))
    cam = camera("Cosmic impossible scale camera", (8.5, -14.6, 6.4),
                 (0, 2, 4.35), ortho=17.8)
    key(cam, "location", ((1, (8.5, -14.6, 6.4)),
                          (72, (6.3, -12.6, 5.8) if variant == 3 else
                           (7.3, -13.6, 6.1))))
    scene["cosmic_recipe"] = "tiny witness, detached geometry, abyssal blue, sickly gold, unshown void"
    scene["cosmic_variant"] = variant
    return scene
