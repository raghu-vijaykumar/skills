"""Compare PS1-like and modern-console constraints on the same flight beat."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def attach(obj, rig):
    # A shared root makes the two era silhouettes fly through the same beat.
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.matrix_world = world
    return obj


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def text_label(name, body, x, y, mat):
    bpy.ops.object.text_add(location=(x, y, 0.12), rotation=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.size = 0.47
    obj.data.extrude = 0.004
    obj.data.materials.append(mat)
    return obj


def lowres_texture():
    # Nearest-filtered 16 px color blocks enforce an explicit retro texel scale.
    image = bpy.data.images.new("Era PS1 16px texture", width=16, height=16)
    pixels = []
    for y in range(16):
        for x in range(16):
            v = 0.30 if (x // 4 + y // 4) % 2 else 0.56
            pixels.extend((v, v * 0.67, v * 0.39, 1.0))
    image.pixels[:] = pixels
    mat = material("Era PS1 nearest texture", (0.44, 0.31, 0.17), roughness=0.98)
    nodes = mat.node_tree.nodes
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "PS1 nearest texels"
    texture.image = image
    texture.interpolation = "Closest"
    mat.node_tree.links.new(texture.outputs["Color"],
                            nodes.get("Principled BSDF").inputs["Base Color"])
    return mat


def lowpoly_ship(x, hull, accent):
    bpy.ops.object.empty_add(location=(x, 0, 0))
    rig = bpy.context.object
    rig.name = "SM_Era_PS1_Ship_Rig"
    attach(cube("PS1 hull", (x, 0, 0.44),
                (1.19, 1.85, 0.27), hull), rig)
    attach(cube("PS1 left wing", (x - 0.89, -0.36, 0.40),
                (0.69, 0.75, 0.12), hull), rig)
    attach(cube("PS1 right wing", (x + 0.89, -0.36, 0.40),
                (0.69, 0.75, 0.12), hull), rig)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.61,
                                    radius2=0, depth=0.63,
                                    location=(x, 1.18, 0.44),
                                    rotation=(1.5708, 0, 0))
    nose = bpy.context.object
    nose.name = "PS1 triangular nose"
    nose.data.materials.append(hull)
    attach(nose, rig)
    attach(cube("PS1 cockpit slab", (x, 0.15, 0.63),
                (0.57, 0.68, 0.15), accent), rig)
    for offset in (-0.36, 0.36):
        attach(cube(f"PS1 thruster {offset}", (x + offset, -1.00, 0.47),
                    (0.27, 0.19, 0.22), accent), rig)
    return rig


def modern_ship(x, hull, accent, glass):
    bpy.ops.object.empty_add(location=(x, 0, 0))
    rig = bpy.context.object
    rig.name = "SM_Era_PS5_Ship_Rig"
    attach(cube("PS5 beveled hull", (x, 0, 0.45),
                (1.23, 1.95, 0.36), hull, edge=0.22), rig)
    for side in (-1, 1):
        attach(cube(f"PS5 wing {side}", (x + side * 0.89, -0.32, 0.42),
                    (0.83, 0.86, 0.15), hull, edge=0.10), rig)
        attach(cube(f"PS5 gold wing trim {side}",
                    (x + side * 0.94, -0.29, 0.52),
                    (0.65, 0.12, 0.04), accent, edge=0.02), rig)
        attach(cylinder(f"PS5 engine {side}", (x + side * 0.36, -1.05, 0.44),
                        0.18, 0.40, accent, vertices=32,
                        rotation=(1.5708, 0, 0), edge=0.025), rig)
    attach(sphere("PS5 curved cockpit", (x, 0.22, 0.72),
                  0.48, glass, segments=32, rings=20,
                  scale=(0.65, 0.98, 0.43)), rig)
    attach(sphere("PS5 sculpted nose", (x, 1.01, 0.47),
                  0.42, hull, segments=32, rings=20,
                  scale=(0.69, 1.36, 0.41)), rig)
    return rig


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown console era flight candidate")
    scene = reset_scene(spec, background=(0.025, 0.037, 0.060))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.43
    stage = material("Era dark stage", (0.055, 0.075, 0.10), roughness=0.88)
    retro_stage = material("Era retro display", (0.17, 0.13, 0.16), roughness=0.94)
    modern_stage = material("Era modern display", (0.045, 0.09, 0.14), roughness=0.47)
    retro_hull = lowres_texture()
    retro_accent = material("Era PS1 flat accent", (0.80, 0.37, 0.23), roughness=0.93)
    modern_hull = material("Era PS5 PBR hull", (0.43, 0.70, 0.86),
                           metallic=0.77, roughness=0.21)
    modern_trim = material("Era PS5 PBR trim", (0.95, 0.59, 0.23),
                           metallic=0.83, roughness=0.18)
    modern_glass = material("Era PS5 canopy", (0.04, 0.34, 0.54),
                            metallic=0.41, roughness=0.13)
    text_mat = material("Era label ivory", (0.86, 0.85, 0.77),
                        emission=(0.62, 0.62, 0.58), emission_strength=0.34)
    cube("SM_Era_Comparison_Stage", (0, 0, -0.34),
         (10.3, 6.7, 0.55), stage, edge=0.10)
    cube("PS1 display panel", (-2.54, 0, -0.03),
         (4.80, 5.98, 0.08), retro_stage)
    cube("PS5 display panel", (2.54, 0, -0.03),
         (4.80, 5.98, 0.08), modern_stage)
    # Thin physical scanlines establish the left media-era treatment.
    for i in range(14):
        cube(f"PS1 CRT scanline {i}", (-2.54, -2.27 + i * 0.35, 0.015),
             (4.65, 0.015, 0.005), stage)
    text_label("PS1 era label", "PS1", -4.38, 2.08, text_mat)
    text_label("PS5 era label", "PS5", 0.72, 2.08, text_mat)
    left = lowpoly_ship(-2.57, retro_hull, retro_accent)
    right = modern_ship(2.57, modern_hull, modern_trim, modern_glass)
    if variant == 2:
        # Identical rise and bank make geometry and shading differences comparable.
        for rig, x in ((left, -2.57), (right, 2.57)):
            key(rig, "location", ((1, (x, -0.30, 0)),
                                   (24, (x, -0.30, 0)),
                                   (55, (x, 0.18, 0.63)),
                                   (72, (x, 0.18, 0.63))))
            key(rig, "rotation_euler", ((1, (0, 0, 0)),
                                         (55, (0, 0, -0.13)),
                                         (72, (0, 0, -0.13))))
    else:
        left.location.y = right.location.y = -0.30
    area_light("Era warm PS1 key", (-4.4, -3.3, 5.9), 800, 3.6,
               color=(1.0, 0.66, 0.48), target=(-2.5, 0, 0.3))
    area_light("Era cool PS5 key", (4.4, -3.0, 5.8), 1150, 3.8,
               color=(0.55, 0.81, 1.0), target=(2.5, 0, 0.3))
    camera("Era comparison camera", (0, -7.6, 8.5), (0, 0, 0.3), ortho=10.8)
    scene["era_recipe"] = "PS1 low polygon nearest texture and scanlines beside PS5 smooth PBR flight"
    scene["era_variant"] = variant
    return scene
