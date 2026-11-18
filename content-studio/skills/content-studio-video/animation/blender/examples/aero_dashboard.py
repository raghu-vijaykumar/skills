"""Original glossy nature-tech aqua dashboard and unfolding bubble leaf."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def glossy(name, color, roughness=0.12, transmission=0.0, coat=0.55):
    """A restrained glass/plastic stack carries the mid-2000s aqua surface cue."""
    mat = material(name, color, roughness=roughness)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = 0.06
    bsdf.inputs["Transmission Weight"].default_value = transmission
    bsdf.inputs["IOR"].default_value = 1.34 if transmission else 1.48
    mat["aero_gloss_stack"] = True
    return mat


def animate_location(obj, samples):
    for frame, xyz in samples:
        obj.location = xyz
        obj.keyframe_insert(data_path="location", frame=frame)


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown authored Aero candidate")
    scene = reset_scene(spec, background=(0.40, 0.75, 0.83))
    scene.view_settings.view_transform = "AgX"
    scene.render.film_transparent = False
    white = glossy("Aero warm white plastic", (0.90, 0.99, 0.99), roughness=0.14)
    aqua = glossy("Aero luminous aqua shell", (0.08, 0.63, 0.82), roughness=0.08,
                  transmission=0.18, coat=0.8)
    deep = glossy("Aero deep turquoise trim", (0.02, 0.32, 0.51), roughness=0.13)
    inner = glossy("Aero blue bubble core", (0.04, 0.48, 0.75), roughness=0.18)
    glass = glossy("Aero glass bubble skin", (0.30, 0.77, 0.91), roughness=0.04,
                   transmission=0.28, coat=0.95)
    green = glossy("Aero fresh leaf green", (0.25, 0.75, 0.20), roughness=0.24)
    pale = glossy("Aero lemon highlight", (0.80, 0.97, 0.54), roughness=0.17)
    ground = material("Aero spring meadow", (0.31, 0.73, 0.37), roughness=0.84)
    sky = material("Aero sky gradient", (0.45, 0.79, 0.89), roughness=1.0)
    # Large curved-looking color masses keep the stage optimistic and uncluttered.
    cube("Aero blue sky plane", (0, 2.4, 1.7), (13, 0.1, 7), sky)
    cube("Aero green horizon", (0, 2.0, -1.47), (13, 8.0, 0.14), ground)
    for i, (x, z, scale) in enumerate(((-3.6, 1.65, 0.68),
                                       (-2.7, 1.79, 0.78),
                                       (3.1, 1.62, 0.63))):
        cloud = sphere(f"Aero soft cloud {i}", (x, 1.7, z), scale, white,
                       segments=24, rings=12, scale=(1.5, 0.22, 0.45))
        cloud["aero_cloud"] = True
    # The UI card is a physical beveled object with an inset blue face and pill controls.
    card = cube("SM_Aero_Aqua_Card", (0, 0, 0.28), (4.70, 0.31, 2.70),
                white, edge=0.25)
    card["skeuomorphic_panel"] = True
    cube("Aero aqua inset", (0, -0.19, 0.35), (4.34, 0.05, 2.37),
         aqua, edge=0.17)
    cube("Aero deep header", (0, -0.25, 1.20), (4.14, 0.035, 0.39),
         deep, edge=0.16)
    for i, x in enumerate((-1.78, -1.46, -1.14)):
        sphere(f"Aero header dot {i}", (x, -0.31, 1.20), 0.075,
               pale if i == 0 else white, segments=16, rings=8,
               scale=(1, 0.28, 1))
    for i, (z, width) in enumerate(((0.47, 1.40), (0.05, 1.16), (-0.37, 0.84))):
        cube(f"Aero soft UI pill {i}", (0.96, -0.28, z),
             (width, 0.07, 0.25), white, edge=0.11)
        cube(f"Aero colored UI fill {i}", (0.47 + width * 0.31, -0.33, z),
             (width * (0.55 + i * 0.08), 0.03, 0.13),
             green if i == 0 else pale if i == 1 else deep, edge=0.05)
    # A translucent outer shell and colored inner core read as a glassy bubble.
    bubble_control = bpy.data.objects.new("Aero bubble float control", None)
    bpy.context.scene.collection.objects.link(bubble_control)
    inner_core = sphere("Aero bubble inner core", (0, 0, 0), 0.54, inner,
                        segments=48, rings=24)
    outer = sphere("SM_Aero_Glass_Bubble", (0, 0, 0), 0.68, glass,
                   segments=64, rings=32)
    for obj in (inner_core, outer):
        obj.parent = bubble_control
    # A small curved white mark reinforces gloss even in the compressed GIF.
    highlight = sphere("Aero bubble painted glint", (-0.23, -0.59, 0.22),
                       0.16, white, segments=24, rings=12,
                       scale=(0.72, 0.18, 1.55))
    highlight.parent = bubble_control
    animate_location(bubble_control, ((1, (-0.96, -0.64, 0.10)),
                                      (36, (-0.96, -0.64, 0.24)),
                                      (72, (-0.96, -0.64, 0.14))))
    leaf_hinge = bpy.data.objects.new("Aero leaf hinge", None)
    bpy.context.scene.collection.objects.link(leaf_hinge)
    leaf_hinge.parent = bubble_control
    leaf_hinge.location = (0.10, -0.05, 0.50)
    cylinder("Aero leaf stem", (0.0, 0, 0.18), 0.035, 0.46,
             green, vertices=12).parent = leaf_hinge
    leaf = sphere("SM_Aero_Leaf", (0.08, -0.02, 0.43), 0.32,
                  green, segments=24, rings=12, scale=(0.56, 0.15, 1.25))
    leaf.parent = leaf_hinge
    leaf["nature_cue"] = True
    if variant == 2:
        vein = sphere("Aero pale leaf vein", (0.09, -0.12, 0.43),
                      0.20, pale, segments=16, rings=8,
                      scale=(0.075, 0.05, 1.25))
        vein.parent = leaf_hinge
    for frame, angle in ((1, -1.08), (23, -0.88), (50, -0.22), (72, -0.14)):
        leaf_hinge.rotation_euler.y = angle if variant == 2 else -0.72
        leaf_hinge.keyframe_insert(data_path="rotation_euler", frame=frame)
    # Floating small bubbles and a moving specular key make the interface feel alive.
    bubble_count = 2 if variant == 1 else 5
    for i in range(bubble_count):
        x = -2.05 + i * 0.17
        bub = sphere(f"SM_Aero_Bubble_{i}", (x, -0.95, -0.88),
                     0.08 + (i % 3) * 0.028, glass,
                     segments=24, rings=12)
        animate_location(bub, ((1, (x, -0.95, -0.88 - i * 0.09)),
                               (36, (x + 0.11, -0.95, -0.10 + i * 0.06)),
                               (72, (x + 0.08, -0.95, 0.68 + i * 0.10))))
    area_light("Aero softbox left", (-3.0, -3.5, 5.3), 540, 5.0,
               color=(0.93, 1.0, 0.98), target=(0, 0, 0))
    area_light("Aero cyan rim", (2.8, 0.9, 4.4), 390, 3.2,
               color=(0.33, 0.85, 1.0), target=(0, 0, 0))
    sweep = area_light("Aero sweep key", (-2.5, -2.3, 2.8),
                       300 if variant == 2 else 120, 1.15,
                       color=(1.0, 1.0, 0.85), target=(0, -0.2, 0.2))
    animate_location(sweep, ((1, (-2.5, -2.3, 2.8)),
                             (36, (0.2, -2.3, 2.8)),
                             (72, (2.7, -2.3, 2.8))))
    camera("Aero optimism camera", (3.0, -8.2, 2.8), (0, 0, 0.23), ortho=6.6)
    scene["aero_recipe"] = "glossy aqua card, glass bubbles, spring greens, leaf and soft UI motion"
    scene["aero_variant"] = variant
    return scene
