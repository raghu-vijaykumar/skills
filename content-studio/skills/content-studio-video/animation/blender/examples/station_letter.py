"""Original narrative station plate with a single letter interaction cue."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2, 3):
        raise ValueError("Unknown narrative station candidate")
    scene = reset_scene(spec, background=(0.025, 0.045, 0.065))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.38
    floor = material("Station wet stone", (0.10, 0.14, 0.17), roughness=0.36)
    wall = material("Station blue wall", (0.12, 0.18, 0.22), roughness=0.83)
    trim = material("Station cold trim", (0.28, 0.37, 0.40), metallic=0.33,
                    roughness=0.52)
    night = material("Station rain window night", (0.035, 0.12, 0.19),
                     emission=(0.05, 0.19, 0.28), emission_strength=0.60)
    rain = material("Station rain streak silver", (0.45, 0.70, 0.75),
                    emission=(0.21, 0.48, 0.57), emission_strength=0.48)
    ochre = material("Station waiting bench", (0.43, 0.24, 0.13), roughness=0.80)
    silhouette = material("Station lone witness coat", (0.05, 0.075, 0.085),
                          roughness=0.87)
    skin = material("Station witness pale face", (0.61, 0.49, 0.37), roughness=0.72)
    paper = material("Station letter warm paper", (0.85, 0.77, 0.60), roughness=0.78)
    cue_mat = material("Station singular interaction cyan", (0.05, 0.55, 0.72),
                       emission=(0.03, 0.50, 0.66), emission_strength=1.20)
    cube("SM_Narrative_Platform", (0, 0, -0.18), (9.2, 5.2, 0.35), floor,
         edge=0.065)
    for i in range(7):
        cube(f"Station platform seam {i}", (-4.0 + i * 1.35, -0.08, 0.01),
             (0.035, 4.82, 0.025), trim)
    # Open wall modules leave a true background-plate opening around the rain window.
    cube("Station wall left", (-4.22, 2.25, 1.70), (0.55, 0.28, 3.38), wall)
    cube("Station wall right", (2.50, 2.25, 1.70), (4.10, 0.28, 3.38), wall)
    cube("Station wall lintel", (-1.86, 2.25, 3.20), (4.18, 0.28, 0.36), wall)
    cube("Station wall sill", (-1.86, 2.25, 0.44), (4.18, 0.31, 0.88), wall)
    cube("SM_Narrative_Rain_Window", (-1.86, 2.43, 1.84),
         (4.12, 0.06, 2.43), night)
    for x in (-3.88, -1.86, 0.16):
        cube(f"Station window mullion {x}", (x, 2.11, 1.83),
             (0.08, 0.11, 2.51), trim)
    for i in range(8):
        x = -3.54 + i * 0.46
        z = 1.15 + (i % 3) * 0.47
        drop = cube(f"Station rain streak {i}", (x, 2.08, z),
                    (0.025, 0.025, 0.23 + (i % 2) * 0.17), rain)
        if variant in (2, 3):
            key(drop, "location", ((1, (x, 2.08, z)),
                                    (72, (x, 2.08, z - 0.51))))
    # The witness and letter form one readable silhouette with calm negative space.
    bench = cube("SM_Narrative_Bench", (-1.25, 0.15, 0.62),
                 (3.75, 0.87, 0.18), ochre, edge=0.05)
    cube("Station bench back", (-1.25, 0.60, 1.15),
         (3.75, 0.16, 1.10), ochre, edge=0.04)
    for x in (-2.80, 0.30):
        cube(f"Station bench leg {x}", (x, 0.15, 0.29),
             (0.21, 0.43, 0.57), trim)
    if variant == 3:
        # A seated coat, hanging arms, and feet distinguish the witness from a post.
        witness = cylinder("SM_Narrative_Lone_Witness", (-2.21, -0.08, 1.23),
                           0.36, 0.95, silhouette, vertices=10)
        for side in (-1, 1):
            cube(f"Station witness arm {side}",
                 (-2.21 + side * 0.36, -0.19, 1.20),
                 (0.19, 0.21, 0.63), silhouette, edge=0.04)
            cube(f"Station witness leg {side}",
                 (-2.21 + side * 0.17, -0.53, 0.43),
                 (0.20, 0.26, 0.72), silhouette, edge=0.04)
        sphere("Station witness head", (-2.21, -0.08, 1.93),
               0.29, skin, segments=16, rings=8)
        sphere("Station witness dark hair", (-2.21, -0.08, 2.07),
               0.29, silhouette, segments=16, rings=8,
               scale=(1, 1, 0.48))
        cube("Station witness nose toward letter", (-1.92, -0.18, 1.88),
             (0.13, 0.14, 0.10), skin, edge=0.015)
    else:
        witness = cylinder("SM_Narrative_Lone_Witness", (-2.21, -0.08, 1.35),
                           0.30, 1.23, silhouette, vertices=10)
        sphere("Station witness head", (-2.21, -0.08, 2.08),
               0.30, skin, segments=16, rings=8)
    cube("Station witness suitcase", (-3.04, -0.42, 0.36),
         (0.54, 0.36, 0.69), silhouette, edge=0.04)
    letter = cube("SM_Narrative_Sealed_Letter", (-0.01, -0.15, 0.78),
                  (0.72, 0.47, 0.05), paper, edge=0.012)
    seal = cube("Station letter seal", (-0.01, -0.15, 0.82),
                (0.11, 0.11, 0.018), ochre)
    # A thin halo leaves the letter and bench readable under the single interaction cue.
    bpy.ops.mesh.primitive_torus_add(major_radius=0.51, minor_radius=0.025,
                                     location=(-0.01, -0.15, 0.79))
    cue = bpy.context.object
    cue.name = "SM_Narrative_Letter_Cue"
    cue.data.materials.append(cue_mat)
    cue.scale = (0.02, 0.02, 0.02)
    if variant in (2, 3):
        # One cue appears only after the camera has established the quiet plate.
        key(cue, "scale", ((1, (0.02, 0.02, 0.02)),
                            (28, (0.02, 0.02, 0.02)),
                            (44, (1, 1, 1)), (72, (1, 1, 1))))
        key(letter, "location", ((1, (-0.01, -0.15, 0.78)),
                                  (44, (-0.01, -0.15, 0.78)),
                                  (72, (-0.01, -0.15, 1.24))))
        key(seal, "location", ((1, (-0.01, -0.15, 0.82)),
                                (44, (-0.01, -0.15, 0.82)),
                                (72, (-0.01, -0.15, 1.28))))
    area_light("Station blue window wash", (-1.9, 1.08, 3.3), 820, 3.2,
               color=(0.40, 0.70, 1.0), target=(-1.9, 0, 1.2))
    area_light("Station letter warm pool", (1.95, -2.75, 4.4), 720, 2.7,
               color=(1.0, 0.70, 0.40), target=(0, -0.2, 0.8))
    cam = camera("Station letter emotional camera", (3.9, -8.0, 4.2),
                 (-0.65, 0.2, 1.35), lens=38)
    if variant in (2, 3):
        key(cam, "location", ((1, (3.9, -8.0, 4.2)),
                              (72, (3.26, -6.75, 3.82))))
    scene["narrative_recipe"] = "rain window plate, lone witness, sealed letter, one late interaction cue, emotional camera push"
    scene["narrative_variant"] = variant
    return scene
