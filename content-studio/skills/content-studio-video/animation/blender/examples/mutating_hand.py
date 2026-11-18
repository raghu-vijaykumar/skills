"""Original body-horror hand with almost-human anatomy and a fused sixth digit."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def finger(name, base, length, width, skin, nail, tip=None):
    """Keep knuckles and a nail visible so the mutation still reads as a human hand."""
    control = bpy.data.objects.new(f"{name} knuckle control", None)
    bpy.context.scene.collection.objects.link(control)
    control.location = base
    lower = sphere(f"{name} proximal", (0, 0, length * 0.28),
                   1, skin, segments=24, rings=12,
                   scale=(width, width, length * 0.31))
    joint = sphere(f"{name} joint", (0, -0.005, length * 0.55),
                   width * 1.02, skin, segments=20, rings=10)
    upper = sphere(f"{name} distal", (0, 0, length * 0.78),
                   1, tip or skin, segments=24, rings=12,
                   scale=(width * 0.84, width * 0.84, length * 0.26))
    cap = sphere(f"{name} soft tip", (0, 0, length * 1.02),
                 width * 0.84, tip or skin, segments=20, rings=10)
    nail_obj = sphere(f"{name} nail", (0, -width * 0.92, length * 0.91),
                      width * 0.76, nail, segments=20, rings=10,
                      scale=(0.77, 0.26, 1.15))
    for part in (lower, joint, upper, cap, nail_obj):
        part.parent = control
    return control


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2, 3):
        raise ValueError("Unknown authored mutating hand candidate")
    scene = reset_scene(spec, background=(0.060, 0.025, 0.035))
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.75
    scene.view_settings.view_transform = "AgX"
    skin = material("Hand pallid living skin", (0.40, 0.20, 0.20), roughness=0.55)
    skin_shader = skin.node_tree.nodes.get("Principled BSDF")
    skin_shader.inputs["Subsurface Weight"].default_value = 0.12
    # Small surface noise keeps the living material from reading as molded plastic.
    noise = skin.node_tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 24
    bump = skin.node_tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.09
    bump.inputs["Distance"].default_value = 0.012
    skin.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    skin.node_tree.links.new(bump.outputs["Normal"], skin_shader.inputs["Normal"])
    blush = material("Hand scar tissue", (0.31, 0.10, 0.12), roughness=0.64)
    nail = material("Hand pale translucent nails", (0.67, 0.47, 0.39), roughness=0.38)
    metal = material("Hand surgical steel fusion", (0.23, 0.29, 0.31),
                     metallic=0.84, roughness=0.22)
    ceramic = material("Hand bone white plastic", (0.62, 0.61, 0.55), roughness=0.26)
    vein = material("Hand dark wine vessels", (0.12, 0.026, 0.040), roughness=0.46)
    plinth_mat = material("Hand charcoal examination stone", (0.060, 0.044, 0.055),
                          roughness=0.86)
    cube("Hand floor", (0, 0, -0.22), (30, 20, 0.4), plinth_mat)
    cube("Hand examination plinth", (0, 0.48, 0.23), (3.4, 1.8, 0.36),
         plinth_mat, edge=0.08)
    cylinder("Hand wrist", (0, 0, 0.90), 0.31, 1.18, skin, vertices=40)
    palm = sphere("SM_Body_Horror_Palm", (0, 0, 1.73), 1, skin,
                  segments=48, rings=24, scale=(0.72, 0.25, 0.83))
    palm["human_anatomy"] = True
    sphere("Hand fleshy thenar pad", (-0.45, -0.04, 1.58), 0.38, skin,
           segments=24, rings=12, scale=(0.68, 0.62, 1.1))
    # Fused surface plates cross the palm from moist skin to cool steel and plastic.
    for i, (x, z, width) in enumerate(((0.08, 1.26, 0.22),
                                       (0.22, 1.57, 0.25),
                                       (0.34, 1.89, 0.26))):
        plate = sphere(f"SM_Body_Horror_Fusion_{i}", (x, -0.237, z),
                       0.33, metal if i < 2 else ceramic,
                       segments=24, rings=12, scale=(width / 0.33, 0.12, 0.72))
        plate["material_transition"] = True
        if variant >= 2:
            animate(plate, "scale", ((1, (0.30, 0.12, 0.48)),
                                      (36, (width / 0.33, 0.12, 0.72)),
                                      (72, (width / 0.33 * 1.12, 0.12, 0.78))))
    for i in range(6):
        x = -0.25 + i * 0.10
        vessel = cylinder(f"Hand fine vessel {i}", (x, -0.265, 1.3 + i * 0.14),
                          0.008, 0.34, vein, vertices=8)
        vessel.rotation_euler.y = -0.28 + i * 0.06

    positions = [(-0.58, 2.26, 0.86, 0.115),
                 (-0.29, 2.43, 1.17, 0.125),
                 (0.01, 2.48, 1.31, 0.128),
                 (0.31, 2.41, 1.11, 0.123),
                 (0.57, 2.28, 0.86, 0.11)]
    if variant == 3:
        # Four ordinary fingers and a thumb preserve human recognition;
        # the separate growing branch then becomes exactly the sixth digit.
        positions.pop()
    fingers = []
    for i, (x, z, length, width) in enumerate(positions):
        ctl = finger(f"Hand digit {i}", (x, -0.015, z), length,
                     width, skin, nail, metal if variant >= 2 and i == 3 else None)
        fingers.append(ctl)
        initial = 0.82 - i * 0.08
        animate(ctl, "rotation_euler", ((1, (initial, 0, 0)),
                                        (36, (0.44, 0, 0)),
                                        (72, (0.08 + i * 0.025, 0, 0))))
    thumb = finger("Hand thumb", (-0.65, -0.02, 1.53), 0.82,
                   0.16, skin, nail)
    animate(thumb, "rotation_euler", ((1, (0.20, -0.87, 0)),
                                      (72, (0.08, -1.12, 0))))
    sphere("Hand sixth digit scar root", (0.66, -0.03, 2.17),
           0.22, blush, segments=24, rings=12, scale=(0.8, 0.75, 0.55))
    extra = finger("SM_Body_Horror_Extra_Digit", (0.77, -0.07, 2.25),
                   1.18, 0.10, metal if variant >= 2 else skin, ceramic,
                   tip=ceramic if variant >= 2 else skin)
    extra["mutation_branch"] = True
    if variant >= 2:
        animate(extra, "scale", ((1, (0.05, 0.05, 0.05)),
                                  (30, (0.52, 0.52, 0.56)),
                                  (72, (1, 1, 1))))
        animate(extra, "rotation_euler", ((1, (0.76, 0.30, 0)),
                                          (36, (0.38, 0.22, 0)),
                                          (72, (-0.13, 0.13, 0))))
    else:
        extra.scale = (0.58, 0.58, 0.58)
        extra.rotation_euler = (0.58, 0.20, 0)

    # A restrained wet highlight keeps the subject visceral without explicit gore.
    area_light("Hand cold clinical key", (-2.8, -3.5, 5.7), 570, 4.2,
               color=(0.71, 0.85, 1), target=(0, 0, 2))
    area_light("Hand red back edge", (2.0, 1.8, 4.2), 730, 2.6,
               color=(1, 0.20, 0.19), target=(0, 0, 2))
    area_light("Hand metal glint", (2.4, -2.3, 3.5), 135, 1.4,
               color=(1, 0.88, 0.69), target=(0.3, -0.2, 1.7))
    cam = camera("Body horror hand camera", (2.7, -7.0, 3.3),
                 (0, 0, 1.97), ortho=6.6)
    animate(cam, "location", ((1, (2.7, -7.0, 3.3)),
                              (72, (2.2, -6.4, 3.15))))
    scene["body_horror_recipe"] = "recognized hand, sixth digit, skin-to-metal-to-plastic fusion"
    scene["body_horror_variant"] = variant
    return scene
