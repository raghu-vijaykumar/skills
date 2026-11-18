"""Original cheerful felt puppet on a television stage that turns subtly wrong."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def felt(name, color):
    mat = material(name, color, roughness=1)
    noise = mat.node_tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 90
    noise.inputs["Detail"].default_value = 2
    bump = mat.node_tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.022
    mat.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    mat.node_tree.links.new(bump.outputs["Normal"],
                        mat.node_tree.nodes["Principled BSDF"].inputs["Normal"])
    mat["felt_fiber"] = True
    return mat


def attach(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world
    return obj


def text_object(name, body, location, size, mat):
    curve = bpy.data.curves.new(name, "FONT")
    curve.body = body
    curve.size = size
    curve.align_x = "CENTER"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (math.pi / 2, 0, 0)
    curve.materials.append(mat)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown puppet stage candidate")
    scene = reset_scene(spec, background=(0.10, 0.12, 0.17))
    scene.view_settings.view_transform = "AgX"
    yellow = felt("Pip golden felt", (0.91, 0.54, 0.09))
    pink = felt("Pip coral felt ears", (0.82, 0.23, 0.23))
    curtain = felt("Pip rosy stage curtains", (0.52, 0.10, 0.22))
    blue = material("Pip painted blue stage", (0.08, 0.31, 0.40), roughness=0.92)
    cream = material("Pip brand cream", (0.98, 0.83, 0.55), roughness=0.88)
    white = material("Pip hard plastic eyes", (0.97, 0.94, 0.84), roughness=0.17)
    black = material("Pip dead black pupils", (0.012, 0.016, 0.019), roughness=0.09)
    mouthmat = material("Pip smile stitching", (0.28, 0.055, 0.085), roughness=0.96)
    sick = material("Pip sick green spotlight", (0.35, 0.84, 0.23),
                    emission=(0.18, 0.6, 0.12), emission_strength=1.2)

    cube("SM_Puppet_Stage_Floor", (0, 0, -0.17), (9.5, 7.5, 0.32), blue)
    cube("Puppet painted stage back", (0, 2.8, 2.5), (9.5, 0.18, 5.0), cream)
    cube("Puppet cream proscenium top", (0, 2.4, 4.95), (9.5, 0.55, 0.36), cream)
    for side in (-1, 1):
        cube(f"SM_Puppet_Curtain_{side}", (side * 3.77, 1.8, 2.35),
             (1.46, 0.44, 4.70), curtain)
        for i in range(5):
            cube(f"Puppet curtain fold {side} {i}",
                 (side * 3.77 + (i - 2) * 0.27, 1.52, 2.35),
                 (0.075, 0.12, 4.55), pink)
    text_object("SM_Puppet_Show_Banner", "PIP SAYS HELLO!", (0, 2.22, 4.18),
                0.56, blue)
    for i in range(7):
        a = i * 2 * math.pi / 7
        star = sphere(f"Puppet happy star {i}",
                      (2.1 * math.sin(a), 2.26, 2.5 + 1.05 * math.cos(a)),
                      0.08, pink, segments=12, rings=8)
        star.scale = (1.4, 0.4, 1.4)

    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    root.name = "Puppet Pip pose control"
    attach(sphere("SM_Puppet_Felt_Body", (0, 0, 1.38), 1.04, yellow,
                  segments=32, rings=20, scale=(0.93, 0.67, 1.05)), root)
    attach(sphere("SM_Puppet_Felt_Head", (0, -0.07, 2.65), 0.91, yellow,
                  segments=32, rings=20, scale=(1.0, 0.68, 0.87)), root)
    for side in (-1, 1):
        attach(sphere(f"Puppet felt ear {side}",
                      (side * 0.80, 0, 3.36), 0.36, pink,
                      segments=24, rings=12, scale=(0.56, 0.43, 1.40)), root)
        attach(sphere(f"SM_Puppet_Plastic_Eye_{side}",
                      (side * 0.36, -0.59, 2.78), 0.25, white,
                      segments=24, rings=12, scale=(1, 0.46, 1.12)), root)
        pupil = attach(sphere(f"SM_Puppet_Black_Pupil_{side}",
                              (side * 0.36, -0.72, 2.78), 0.13, black,
                              segments=20, rings=10, scale=(0.89, 0.33, 1.02)), root)
        if variant == 2 and side == 1:
            animate(pupil, "location", ((1, (0.36, -0.72, 2.78)),
                        (34, (0.36, -0.72, 2.78)),
                        (57, (0.52, -0.72, 2.62)),
                        (72, (0.52, -0.72, 2.62))))
        arm = attach(sphere(f"SM_Puppet_Foam_Arm_{side}",
                            (side * 1.05, -0.04, 1.70), 0.58, yellow,
                            segments=20, rings=12, scale=(0.44, 0.35, 1.08)), root)
        arm.rotation_euler[1] = side * -0.45
        attach(sphere(f"Puppet foam mitten {side}",
                      (side * 1.40, -0.12, 1.38), 0.27, pink,
                      segments=16, rings=10), root)
    # A friendly stitched smile holds while the plastic eyes stop matching.
    for i in range(9):
        x = (i - 4) * 0.105
        z = 2.33 - 0.13 * (1 - (x / 0.42) ** 2)
        attach(sphere(f"Puppet smile stitch {i}", (x, -0.61, z),
                      0.035, mouthmat, segments=10, rings=8,
                      scale=(1.5, 0.4, 0.55)), root)
    attach(sphere("Puppet foam button", (0, -0.68, 1.35), 0.15, pink,
                  segments=16, rings=10, scale=(1, 0.3, 1)), root)
    for side in (-1, 1):
        attach(sphere(f"Puppet yellow foot {side}", (side * 0.42, -0.22, 0.35),
                      0.31, yellow, segments=20, rings=12,
                      scale=(1.08, 1.40, 0.52)), root)
    warm = area_light("Puppet cheerful key", (-2.7, -3.0, 5.5), 850, 3.5,
                      color=(1.0, 0.72, 0.52), target=(0, 0, 2))
    ill = area_light("SM_Puppet_Sick_Light", (2.4, -1.2, 4.4), 0, 2.8,
                     color=(0.41, 0.96, 0.30), target=(0, 0, 2.4))
    if variant == 2:
        animate(root, "rotation_euler", ((1, (0, 0, 0)),
                 (24, (0, 0, -0.045)), (42, (0, 0, 0.045)),
                 (72, (0, 0, 0.13))))
        animate(ill.data, "energy", ((1, 0), (39, 0),
                 (43, 390), (55, 40), (72, 490)))
        animate(warm.data, "energy", ((1, 850), (39, 850),
                 (43, 310), (72, 120)))
    else:
        animate(root, "rotation_euler", ((1, (0, 0, 0)),
                 (72, (0, 0, 0.04))))
    cam = camera("Puppet stage camera", (0, -8.2, 2.25), (0, 0, 2.05), lens=40)
    animate(cam, "location", ((1, (0, -8.2, 2.25)),
             (72, (0, -7.2 if variant == 2 else -8.0, 2.25))))
    scene["puppet_recipe"] = "felt foam friend, hard plastic eyes, cheerful children show, sick green shift"
    scene["puppet_variant"] = variant
    return scene
