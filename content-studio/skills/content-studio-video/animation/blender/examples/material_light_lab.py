"""Three-point lookdev for shared material masters and a moving beauty key."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def label(name, text, x, y, mat):
    bpy.ops.object.text_add(location=(x, y, 0.29))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = text
    obj.data.size = 0.30
    obj.data.extrude = 0.003
    obj.data.materials.append(mat)


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown material-light candidate")
    scene = reset_scene(spec, background=(0.045, 0.052, 0.065))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    stage = material("MAT_Lookdev_Stage", (0.09, 0.11, 0.14), roughness=0.88)
    plinth = material("MAT_Lookdev_Plinth", (0.17, 0.19, 0.22), roughness=0.76)
    text = material("MAT_Lookdev_Label", (0.80, 0.85, 0.84),
                    emission=(0.55, 0.63, 0.65), emission_strength=0.18)
    clay = material("MAT_Lookdev_Clay", (0.46, 0.47, 0.46), roughness=0.73)
    # Reuse three named masters, changing only PBR values between swatches.
    # A restrained fill in the shader keeps EEVEE's unreflected metal legible.
    polished = material("MAT_Metal_Polished", (0.82, 0.51, 0.25),
                        metallic=1.0, roughness=0.24,
                        emission=(0.45, 0.21, 0.07), emission_strength=0.13)
    brushed = material("MAT_Metal_Brushed", (0.65, 0.69, 0.68),
                       metallic=1.0, roughness=0.49)
    ceramic = material("MAT_Ceramic_Glaze", (0.09, 0.57, 0.69),
                       metallic=0.0, roughness=0.28)
    cube("SM_Lookdev_Stage", (0, 0, -0.28),
         (10.2, 6.15, 0.55), stage, edge=0.12)
    entries = ((-3.05, "POLISHED", polished),
               (0, "BRUSHED", brushed),
               (3.05, "CERAMIC", ceramic))
    for i, (x, name, beauty) in enumerate(entries):
        cube(f"SM_Lookdev_Plinth_{i}", (x, 0.18, 0.12),
             (2.54, 3.75, 0.22), plinth, edge=0.055)
        swatch_mat = clay if variant == 1 else beauty
        sphere(f"SM_Lookdev_Swatch_{i}", (x, -0.20, 1.02),
               0.77, swatch_mat, segments=32, rings=20)
        cylinder(f"Lookdev collar {i}", (x, -0.20, 0.30),
                 0.65, 0.12, swatch_mat, vertices=48, edge=0.025)
        label(f"Lookdev label {i}", name, x - 0.92, -1.42, text)
    # Neutral fill and back rim remain fixed; the beauty key sweeps across the samples.
    key_light = area_light("LGT_Key_Main", (-3.9, -3.9, 5.7), 1350, 3.3,
                           color=(1.0, 0.79, 0.57), target=(0, 0, 0.9))
    area_light("LGT_Fill_Soft", (4.4, -1.8, 4.5), 430, 4.8,
               color=(0.72, 0.84, 1.0), target=(0, 0, 0.8))
    area_light("LGT_Rim_Back", (0, 3.7, 5.2), 1000, 3.2,
               color=(0.45, 0.80, 1.0), target=(0, 0, 0.9))
    if variant == 2:
        key(key_light, "location", ((1, (-3.9, -3.9, 5.7)),
                                     (37, (0, -3.9, 5.7)),
                                     (72, (3.9, -3.9, 5.7))))
    camera("Lookdev overview camera", (0, -8.1, 7.5),
           (0, 0, 0.30), ortho=10.65)
    scene["lookdev_recipe"] = "clay baseline, three reusable PBR masters, key fill rim, moving beauty key"
    scene["lookdev_variant"] = variant
    return scene
