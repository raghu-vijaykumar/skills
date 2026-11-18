"""Original cel-shaded courier with independently animated head and waving arm."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def toon(name, color):
    """Quantize lit values into three bands for an actual cel-shaded material."""
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = (*color, 1)
    shader_rgb = nodes.new("ShaderNodeShaderToRGB")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    stops = ramp.color_ramp.elements
    stops.remove(stops[1])
    stops[0].position = 0
    stops[0].color = (*(v * 0.42 for v in color), 1)
    mid = stops.new(0.38)
    mid.color = (*color, 1)
    high = stops.new(0.78)
    high.color = (*(min(1, v * 1.32) for v in color), 1)
    emission = nodes.new("ShaderNodeEmission")
    links = mat.node_tree.links
    links.new(diffuse.outputs["BSDF"], shader_rgb.inputs["Shader"])
    links.new(shader_rgb.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return mat


def attach(obj, root):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = root
    obj.matrix_world = world


def limb(name, a, b, radius, mat):
    center = tuple((x + y) / 2 for x, y in zip(a, b))
    direction = math.dist(a, b)
    obj = cylinder(name, center, radius, direction, mat, vertices=24)
    from mathutils import Vector
    obj.rotation_euler = (Vector(b) - Vector(a)).to_track_quat("Z", "Y").to_euler()
    return obj


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.05, 0.09, 0.15))
    jacket = toon("Coral cel jacket", (0.9, 0.24, 0.18))
    trim = toon("Amber cel trim", (1.0, 0.68, 0.2))
    skin = toon("Warm cel skin", (0.95, 0.66, 0.46))
    hair = toon("Ink blue hair", (0.065, 0.11, 0.19))
    trousers = toon("Deep indigo trousers", (0.1, 0.16, 0.3))
    white = toon("Cream", (0.95, 0.91, 0.78))
    ink = material("Face ink", (0.014, 0.025, 0.055), roughness=0.8)
    stage = material("Warm paper stage", (0.25, 0.36, 0.43), roughness=0.95)
    cube("Stage", (0, 0, -0.16), (12, 12, 0.2), stage, 0.05)

    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    root.name = "Character root"
    attach(cube("Coat torso", (0, 0, 1.38), (0.98, 0.48, 1.13), jacket, 0.18), root)
    attach(cube("Coat hem", (0, 0, 0.78), (1.12, 0.53, 0.2), jacket, 0.08), root)
    attach(cube("Belt", (0, -0.02, 0.91), (0.94, 0.54, 0.12), trousers, 0.035), root)
    attach(cube("Collar left", (-0.25, -0.29, 1.92), (0.36, 0.1, 0.22), white, 0.04), root)
    attach(cube("Collar right", (0.25, -0.29, 1.92), (0.36, 0.1, 0.22), white, 0.04), root)
    for x, name in [(-0.27, "Left"), (0.27, "Right")]:
        attach(limb(name + " trouser leg", (x, 0, 0.76), (x, 0, 0.18), 0.16, trousers), root)
        attach(cube(name + " boot", (x, -0.12, 0.14), (0.38, 0.62, 0.23), hair, 0.08), root)

    bpy.ops.object.empty_add(location=(0, 0, 2.22))
    head = bpy.context.object
    head.name = "Head control"
    attach(head, root)
    attach(sphere("Head", (0, 0, 2.29), 0.52, skin, scale=(0.96, 0.87, 1.07)), head)
    attach(sphere("Hair cap", (0, 0.045, 2.62), 0.51, hair, scale=(1.02, 0.91, 0.48)), head)
    for x in (-0.32, -0.09, 0.16, 0.35):
        attach(sphere("Hair fringe", (x, -0.37, 2.57), 0.19, hair,
                      scale=(0.9, 0.55, 1.4)), head)
    for x in (-0.18, 0.18):
        attach(sphere("Eye white", (x, -0.43, 2.36), 0.11, white,
                      scale=(0.75, 0.38, 1.05)), head)
        attach(sphere("Eye pupil", (x, -0.476, 2.35), 0.055, ink), head)
    attach(sphere("Nose", (0, -0.47, 2.2), 0.055, skin,
                  scale=(0.65, 1, 0.75)), head)
    attach(cube("Smile", (0, -0.47, 2.07), (0.19, 0.025, 0.025), ink, 0.008), head)

    bpy.ops.object.empty_add(location=(-0.56, 0, 1.78))
    wave = bpy.context.object
    wave.name = "Wave arm control"
    attach(wave, root)
    attach(limb("Wave upper arm", (-0.56, 0, 1.78), (-0.77, 0, 1.23), 0.17, jacket), wave)
    attach(limb("Wave forearm", (-0.77, 0, 1.23), (-0.87, -0.04, 0.91), 0.13, jacket), wave)
    attach(sphere("Waving hand", (-0.87, -0.04, 0.88), 0.16, skin), wave)
    attach(limb("Rest arm", (0.56, 0, 1.78), (0.83, 0, 1.03), 0.16, jacket), root)
    attach(sphere("Rest hand", (0.83, 0, 1.01), 0.16, skin), root)

    for frame, angle, tilt in [(1, 0, -0.22), (28, 1.8, 0.0),
                               (45, 1.55, 0.12), (62, 1.9, -0.08),
                               (78, 1.6, 0.08), (96, 0, -0.22)]:
        wave.rotation_euler.y = angle
        wave.keyframe_insert(data_path="rotation_euler", frame=frame)
        head.rotation_euler.z = tilt
        head.keyframe_insert(data_path="rotation_euler", frame=frame)
    for frame, z in [(1, 0), (45, 0.05), (96, 0)]:
        root.location.z = z
        root.keyframe_insert(data_path="location", frame=frame)

    camera("Hero camera", (4.1, -7.1, 3.2), (0, 0, 1.4), ortho=5.4)
    area_light("Graphic key", (-3, -4, 7), 1100, 3.0, target=(0, 0, 1.5))
    area_light("Warm rim", (2, 3, 5), 850, 2.5, color=(1.0, 0.75, 0.5), target=(0, 0, 1.5))
    return scene
