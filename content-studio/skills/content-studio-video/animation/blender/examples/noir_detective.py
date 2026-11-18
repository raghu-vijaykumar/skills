"""Original limited-palette noir alley with a walking fedora silhouette."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def attach(obj, parent):
    bpy.context.view_layer.update()
    matrix = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = matrix
    return obj


def control(name, location, parent=None):
    bpy.ops.object.empty_add(location=location)
    obj = bpy.context.object
    obj.name = name
    return attach(obj, parent) if parent else obj


def volume_material():
    """A thin haze exposes the motivated key without washing out shadows."""
    mat = bpy.data.materials.new("Noir low density alley haze")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (0.33, 0.39, 0.46, 1)
    volume.inputs["Density"].default_value = 0.018
    volume.inputs["Anisotropy"].default_value = 0.35
    mat.node_tree.links.new(volume.outputs["Volume"], output.inputs["Volume"])
    return mat


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.004, 0.007, 0.012))
    scene.unit_settings.system = "METRIC"
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.12
    ink = material("Noir coat charcoal", (0.018, 0.025, 0.035), roughness=0.96)
    hat_mat = material("Noir fedora near black", (0.025, 0.033, 0.044), roughness=0.88)
    leather = material("Noir briefcase dark leather", (0.035, 0.044, 0.06), roughness=0.7)
    concrete = material("Noir damp wall", (0.09, 0.11, 0.14), roughness=0.93)
    street = material("Noir mirror wet asphalt", (0.028, 0.04, 0.055),
                      metallic=0.72, roughness=0.095)
    street["wet_street_mirror"] = True
    pale = material("Noir cold window slashes", (0.42, 0.58, 0.69),
                    emission=(0.52, 0.72, 0.85), emission_strength=1.8)
    amber = material("Noir one warm practical", (0.36, 0.20, 0.08),
                     emission=(1, 0.55, 0.2), emission_strength=2.4)
    puddle = material("Noir puddle edge glint", (0.10, 0.17, 0.23),
                      metallic=0.55, roughness=0.16,
                      emission=(0.20, 0.31, 0.42), emission_strength=0.06)

    cube("SM_Noir_Wet_Street", (0, 0, -0.09), (9, 7, 0.18), street)
    cube("Noir back wall", (0, 2.4, 1.63), (9, 0.2, 3.45), concrete)
    for index in range(6):
        # Emissive slats mimic a hard key through blinds; dark gaps retain detail.
        cube(f"SM_Noir_Blinds_Light_{index}", (-1.25, 2.27, 0.95 + index * 0.31),
             (2.15, 0.025, 0.075), pale)
    cube("Noir doorway", (2.22, 2.24, 1.15), (1.23, 0.08, 2.3), hat_mat)
    cube("Noir doorway practical", (2.22, 2.18, 2.27), (1.03, 0.035, 0.04), amber)
    for index, x in enumerate((-2.2, -1.15, 0.55, 1.72)):
        # Uneven specular pools replace rigid floor bars; ripples track falling rain.
        glint = sphere(f"Noir wet reflection {index}", (x, -0.28, 0.008),
                       0.45, puddle, scale=(1.1 + index * 0.16, 0.65, 0.018))
        glint.rotation_euler.z = (index - 1.5) * 0.15
    for index, x in enumerate((-1.55, 0.62, 1.78)):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.13,
                                        minor_radius=0.004,
                                        location=(x, -0.43, 0.022))
        ripple = bpy.context.object
        ripple.name = f"Noir puddle ripple {index}"
        ripple.data.materials.append(puddle)
        for frame, scale in ((1, 0.55), (24, 1.35), (48, 0.55), (72, 1.35)):
            ripple.scale = (scale, scale * 0.55, 1)
            ripple.keyframe_insert(data_path="scale", frame=frame)
    cube("Noir alley haze", (0, 0.85, 1.48), (5.4, 2.4, 2.8), volume_material()).hide_select = True

    root = control("Noir detective root", (-1.05, -0.65, 0))
    # A flared coat, low fedora brim, and blocky case identify the silhouette.
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.38, radius2=0.24,
                                    depth=1.14, location=(-1.05, -0.65, 1.04))
    coat = bpy.context.object
    coat.name = "SM_Noir_Trench_Coat"
    coat.data.materials.append(ink)
    attach(coat, root)
    attach(sphere("Noir detective head", (-1.05, -0.65, 1.80), 0.24,
                  ink, scale=(0.86, 0.80, 1.0)), root)
    attach(cylinder("Noir fedora crown", (-1.05, -0.65, 2.10), 0.22, 0.24,
                    hat_mat, vertices=24), root)
    brim = attach(cylinder("SM_Noir_Fedora_Brim", (-1.05, -0.65, 2.01),
                           0.39, 0.055, hat_mat, vertices=32), root)
    brim.scale.y = 0.80
    attach(cube("Noir coat lapel", (-1.05, -0.855, 1.43),
                (0.15, 0.035, 0.42), leather), root)
    for side, x in (("left", -1.27), ("right", -0.83)):
        leg = control(f"Noir {side} leg control", (x, -0.65, 0.61), root)
        attach(cylinder(f"Noir {side} leg", (x, -0.65, 0.35),
                        0.085, 0.53, ink, vertices=12), leg)
        attach(cube(f"Noir {side} shoe", (x, -0.75, 0.08),
                    (0.20, 0.29, 0.15), hat_mat, edge=0.015), leg)
        for frame, angle in ((1, -0.24 if side == "left" else 0.24),
                             (18, 0.27 if side == "left" else -0.27),
                             (36, -0.22 if side == "left" else 0.22),
                             (54, 0.18 if side == "left" else -0.18),
                             (72, 0)):
            leg.rotation_euler.y = angle
            leg.keyframe_insert(data_path="rotation_euler", frame=frame)
    arm = control("Noir case arm control", (-0.80, -0.65, 1.48), root)
    attach(cylinder("Noir right arm", (-0.77, -0.65, 1.13), 0.105, 0.75,
                    ink, vertices=12), arm)
    attach(cube("SM_Noir_Briefcase", (-0.75, -0.71, 0.50),
                (0.43, 0.18, 0.32), leather, edge=0.025), arm)
    attach(cube("Noir briefcase handle", (-0.75, -0.71, 0.70),
                (0.18, 0.08, 0.08), pale, edge=0.015), arm)
    for frame, x, swing in ((1, -1.05, -0.12), (18, -0.52, 0.20),
                            (36, 0.10, -0.16), (54, 0.63, 0.14),
                            (72, 1.03, 0)):
        root.location.x = x
        root.keyframe_insert(data_path="location", frame=frame)
        arm.rotation_euler.y = swing
        arm.keyframe_insert(data_path="rotation_euler", frame=frame)

    # Thin moving rain strokes are visible against the window slashes.
    rain_mat = material("Noir rain silver", (0.24, 0.38, 0.48),
                        emission=(0.30, 0.43, 0.53), emission_strength=0.35)
    for index in range(18):
        x = -3.05 + (index * 1.71) % 6.10
        y = -1.22 + (index % 3) * 0.19
        z = 0.65 + (index * 0.47) % 2.2
        streak = cylinder(f"Noir rain streak {index}", (x, y, z),
                          0.006, 0.18 + (index % 3) * 0.04,
                          rain_mat, vertices=6)
        streak.rotation_euler.y = -0.09
        for frame, shift in ((1, 0), (18, -0.54), (36, -1.11),
                             (54, -1.67), (72, -2.23)):
            streak.location.z = z + shift
            streak.keyframe_insert(data_path="location", frame=frame)

    camera("Noir alley camera", (0, -8, 1.92), (0, 0, 1.34), ortho=6.8)
    area_light("Noir hard window key", (-1.35, 0.3, 3.25), 1050, 0.35,
               color=(0.66, 0.82, 1), target=(0, -0.5, 1.2))
    area_light("Noir warm doorway practical", (2.0, 1.75, 2.2), 260, 0.55,
               color=(1, 0.56, 0.24), target=(0.85, -0.4, 0.95))
    scene["noir_palette"] = "black, silver-blue, one warm practical"
    return scene
