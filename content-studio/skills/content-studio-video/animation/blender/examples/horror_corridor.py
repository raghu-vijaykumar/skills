"""Original sparse institutional corridor with fog, flicker, and a door reveal."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, material, reset_scene


WIDTH_M = 1.44
HEIGHT_M = 2.3


def to_collection(obj, collection):
    for previous in list(obj.users_collection):
        previous.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def parent_keep_world(obj, pivot):
    bpy.context.view_layer.update()
    matrix = obj.matrix_world.copy()
    obj.parent = pivot
    obj.matrix_world = matrix


def volume_material():
    mat = bpy.data.materials.new("Horror desaturated fog")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (0.42, 0.5, 0.45, 1)
    volume.inputs["Density"].default_value = 0.027
    volume.inputs["Anisotropy"].default_value = 0.3
    mat.node_tree.links.new(volume.outputs["Volume"], out.inputs["Volume"])
    return mat


def make_scene(spec, spec_dir=Path(".")):
    if (abs(float(spec.get("corridor_width_m", WIDTH_M)) - WIDTH_M) > 1e-8 or
            abs(float(spec.get("ceiling_height_m", HEIGHT_M)) - HEIGHT_M) > 1e-8):
        raise ValueError("This authored horror corridor is 1.44 m wide and 2.3 m tall")
    scene = reset_scene(spec, background=(0.003, 0.007, 0.006))
    scene.unit_settings.system = "METRIC"
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.08
    set_collection = bpy.data.collections.new("COL_Horror_Corridor")
    scene.collection.children.link(set_collection)
    concrete = material("Horror stained concrete", (0.078, 0.095, 0.075), roughness=0.92)
    floor_mat = material("Horror damp floor", (0.052, 0.067, 0.058), roughness=0.62)
    rust = material("Horror old iron", (0.13, 0.062, 0.036), metallic=0.75, roughness=0.85)
    dark = material("Horror black doorway", (0.008, 0.014, 0.011), roughness=1)
    chair_mat = material("Horror faded chair", (0.16, 0.19, 0.15), roughness=0.89)
    light_mat = material("Horror flickering fluorescent", (0.38, 0.55, 0.42),
                         emission=(0.55, 0.88, 0.61), emission_strength=2.5)
    amber = material("Horror warm door slit", (0.42, 0.22, 0.06),
                     emission=(1, 0.42, 0.12), emission_strength=3)

    # The hall uses one narrow traversal path and one misplaced narrative prop.
    to_collection(cube("SM_Horror_Floor", (0, 5, -0.065),
                       (WIDTH_M, 12, 0.13), floor_mat), set_collection)
    to_collection(cube("SM_Horror_Ceiling", (0, 5, HEIGHT_M + 0.06),
                       (WIDTH_M, 12, 0.12), concrete), set_collection)
    for side, x in (("Left", -WIDTH_M / 2), ("Right", WIDTH_M / 2)):
        to_collection(cube(f"SM_Horror_{side}_Wall", (x, 5, HEIGHT_M / 2),
                           (0.12, 12, HEIGHT_M), concrete), set_collection)
        for bay in range(4):
            y = bay * 2.7 + 0.5
            to_collection(cube(f"SM_Horror_{side}_Joint_{bay}",
                               (x - 0.012 if x > 0 else x + 0.012, y, 1.15),
                               (0.015, 0.018, 2.2), rust), set_collection)
    for y, z, width in ((2.2, 1.3, 0.22), (5.8, 0.62, 0.29), (8.1, 1.75, 0.17)):
        to_collection(cube(f"SM_Horror_Water_Stain_{y}",
                           (-0.652, y, z), (0.004, width, 0.36),
                           floor_mat), set_collection)

    # One chair faces the wall; the rest of the midground remains bare.
    to_collection(cube("SM_Horror_Chair_Seat", (0.31, 5.6, 0.43),
                       (0.38, 0.39, 0.045), chair_mat, edge=0.006), set_collection)
    to_collection(cube("SM_Horror_Chair_Back", (0.48, 5.6, 0.77),
                       (0.045, 0.39, 0.65), chair_mat, edge=0.006), set_collection)
    for x in (0.15, 0.47):
        for y in (5.45, 5.75):
            to_collection(cube(f"SM_Horror_Chair_Leg_{x}_{y}",
                               (x, y, 0.21), (0.025, 0.025, 0.42), rust), set_collection)

    to_collection(cube("SM_Horror_End_Wall", (0, 10.86, 1.15),
                       (WIDTH_M, 0.12, HEIGHT_M), concrete), set_collection)
    to_collection(cube("SM_Horror_Doorway", (0, 10.72, 1.05),
                       (1.02, 0.04, 2.1), dark), set_collection)
    to_collection(cube("SM_Horror_Door_Slit", (0.39, 10.67, 1.05),
                       (0.04, 0.015, 1.86), amber), set_collection)
    bpy.ops.object.empty_add(location=(-0.46, 10.62, 0))
    hinge = to_collection(bpy.context.object, set_collection)
    hinge.name = "Horror door hinge"
    door = to_collection(cube("SM_Horror_Door", (0, 10.58, 1.05),
                              (0.92, 0.06, 2.1), rust, edge=0.009), set_collection)
    parent_keep_world(door, hinge)
    handle = to_collection(cube("SM_Horror_Door_Handle", (0.31, 10.53, 1.0),
                                (0.025, 0.025, 0.11), dark), set_collection)
    parent_keep_world(handle, hinge)
    hinge.rotation_euler.z = 0
    hinge.keyframe_insert(data_path="rotation_euler", frame=1)
    hinge.keyframe_insert(data_path="rotation_euler", frame=40)
    hinge.rotation_euler.z = -0.55
    hinge.keyframe_insert(data_path="rotation_euler", frame=72)

    fixture = to_collection(cube("SM_Horror_Fluorescent_Housing", (0, 2.6, 2.26),
                                 (0.16, 1.1, 0.06), rust), set_collection)
    tube = to_collection(cube("SM_Horror_Fluorescent_Tube", (0, 2.6, 2.22),
                              (0.07, 0.98, 0.025), light_mat), set_collection)
    tube["single_flicker_source"] = True
    practical = area_light("Horror single practical", (0, 2.6, 2.15),
                           115, 1.0, color=(0.56, 0.8, 0.58),
                           target=(0, 3.2, 0.5))
    to_collection(practical, set_collection)
    for frame, power in ((1, 115), (31, 115), (33, 8), (36, 115),
                         (47, 115), (49, 6), (51, 115), (72, 115)):
        practical.data.energy = power
        practical.data.keyframe_insert(data_path="energy", frame=frame)
        emission = light_mat.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
        emission.default_value = 2.5 * power / 115
        emission.keyframe_insert(data_path="default_value", frame=frame)
    area_light("Horror distant warm bleed", (0.22, 10.45, 1.5),
               12, 0.8, color=(1, 0.34, 0.12), target=(0, 9.5, 1.0))

    fog = to_collection(cube("Horror corridor fog", (0, 4.7, 1.15),
                             (1.28, 10.5, 2.16), volume_material()), set_collection)
    fog.hide_select = True
    cam = camera("Horror eye camera", (0, -2.1, 1.6), (0, 8.5, 1.55), lens=31)
    cam.keyframe_insert(data_path="location", frame=1)
    cam.location.y = -0.75
    cam.keyframe_insert(data_path="location", frame=72)
    return scene
