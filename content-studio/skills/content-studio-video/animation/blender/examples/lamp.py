"""Original measured desk-lamp benchmark for modeling and grounded prop craft."""

from pathlib import Path

import bpy
from mathutils import Vector

from common import area_light, bevel, camera, cube, cylinder, material, reset_scene, sphere


def in_collection(obj, collection):
    """Keep the benchmark blockout separate from editable finished geometry."""
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def connect(name, start, end, radius, mat, collection):
    direction = Vector(end) - Vector(start)
    middle = (Vector(start) + Vector(end)) / 2
    obj = cylinder(name, middle, radius, direction.length, mat, vertices=32, edge=0.004)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return in_collection(obj, collection)


def parent_keep_world(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.018, 0.022, 0.028))
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    blockout = bpy.data.collections.new("COL_Blockout")
    geometry = bpy.data.collections.new("COL_Geo")
    scene.collection.children.link(blockout)
    scene.collection.children.link(geometry)

    enamel = material("Pine green enamel", (0.075, 0.23, 0.2), metallic=0.35, roughness=0.29)
    brushed = material("Brushed brass", (0.48, 0.31, 0.12), metallic=0.78, roughness=0.32)
    dark = material("Graphite joint", (0.035, 0.045, 0.048), metallic=0.45, roughness=0.42)
    table = material("Charcoal stone table", (0.09, 0.1, 0.11), roughness=0.82)
    paper = material("Notebook paper", (0.62, 0.55, 0.41), roughness=0.78)
    light_mat = material("Warm lamp diffuser", (0.9, 0.7, 0.43), roughness=0.42,
                         emission=(1.0, 0.64, 0.24), emission_strength=0.2)

    # The preserved blockout establishes an approximately 0.55 m desktop prop.
    proxy = in_collection(cube("SM_Lamp_Blockout", (-0.22, 0, 0.28),
                               (0.72, 0.36, 0.55), dark), blockout)
    proxy.hide_render = True
    proxy.hide_viewport = True
    proxy["intent"] = "Scale and silhouette reference retained for comparison"

    in_collection(cube("SM_Stage", (0, 0, -0.055), (2.6, 2.4, 0.09), table, 0.018), geometry)
    # The notebook gives the lamp a grounded task and shows its changing light pool.
    in_collection(cube("SM_Notebook", (-0.54, 0.05, 0.002),
                       (0.32, 0.23, 0.018), paper, 0.004), geometry)
    base = in_collection(cylinder("SM_Lamp_Base", (0, 0, 0.035), 0.18, 0.07,
                                  enamel, edge=0.008), geometry)
    base["size_m"] = 0.36
    in_collection(cylinder("SM_Lamp_Base_Trim", (0, 0, 0.068), 0.15, 0.009,
                           brushed, edge=0.002), geometry)
    in_collection(sphere("SM_Lamp_Lower_Joint", (-0.11, 0, 0.12), 0.042, dark), geometry)
    connect("SM_Lamp_Lower_Arm", (-0.11, 0, 0.12), (-0.18, 0, 0.37),
            0.021, brushed, geometry)
    in_collection(sphere("SM_Lamp_Elbow", (-0.18, 0, 0.37), 0.045, dark), geometry)

    bpy.ops.object.empty_add(location=(-0.18, 0, 0.37))
    head_pivot = bpy.context.object
    head_pivot.name = "Lamp head pivot"
    head_pivot["intent"] = "Adjustable head and upper arm remain separately editable"
    in_collection(head_pivot, geometry)
    upper = connect("SM_Lamp_Upper_Arm", (-0.18, 0, 0.37), (-0.41, 0, 0.51),
                    0.018, brushed, geometry)
    parent_keep_world(upper, head_pivot)
    head_joint = in_collection(sphere("SM_Lamp_Head_Joint", (-0.41, 0, 0.51),
                                       0.039, dark), geometry)
    parent_keep_world(head_joint, head_pivot)

    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.155, radius2=0.055,
                                    depth=0.16, location=(-0.42, 0, 0.43))
    shade = bpy.context.object
    shade.name = "SM_Lamp_Shade"
    shade.data.materials.append(enamel)
    bevel(shade, 0.006, 2)
    shade = in_collection(shade, geometry)
    parent_keep_world(shade, head_pivot)
    diffuser = in_collection(cylinder("SM_Lamp_Diffuser", (-0.42, 0, 0.349),
                                      0.135, 0.008, light_mat, vertices=48), geometry)
    parent_keep_world(diffuser, head_pivot)
    rim = in_collection(cylinder("SM_Lamp_Rim", (-0.42, 0, 0.345),
                                0.151, 0.008, brushed, vertices=48), geometry)
    parent_keep_world(rim, head_pivot)
    bpy.ops.object.light_add(type="SPOT", location=(-0.42, 0, 0.33))
    task_light = bpy.context.object
    task_light.name = "Lamp task light"
    task_light.data.color = (1.0, 0.7, 0.35)
    task_light.data.spot_size = 0.95
    task_light.data.spot_blend = 0.5
    in_collection(task_light, geometry)
    parent_keep_world(task_light, head_pivot)
    in_collection(cylinder("SM_Lamp_Switch", (0.1, -0.11, 0.077), 0.018, 0.014,
                           dark, vertices=24), geometry)

    head_pivot.rotation_euler.y = 0.24
    head_pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    head_pivot.rotation_euler.y = -0.18
    head_pivot.keyframe_insert(data_path="rotation_euler", frame=72)
    head_pivot.keyframe_insert(data_path="rotation_euler", frame=96)
    bsdf = light_mat.node_tree.nodes.get("Principled BSDF")
    glow = bsdf.inputs["Emission Strength"]
    glow.default_value = 0.2
    glow.keyframe_insert(data_path="default_value", frame=1)
    glow.default_value = 3.5
    glow.keyframe_insert(data_path="default_value", frame=35)
    glow.keyframe_insert(data_path="default_value", frame=96)
    task_light.data.energy = 0
    task_light.data.keyframe_insert(data_path="energy", frame=1)
    task_light.data.energy = 220
    task_light.data.keyframe_insert(data_path="energy", frame=35)
    task_light.data.keyframe_insert(data_path="energy", frame=96)

    cam = camera("Hero camera", (1.24, -1.83, 1.03), (-0.2, 0, 0.25), lens=51)
    cam.keyframe_insert(data_path="location", frame=1)
    cam.location = (1.15, -1.68, 0.97)
    cam.keyframe_insert(data_path="location", frame=96)
    area_light("Large softbox", (0.5, -1.2, 1.7), 220, 1.4, target=(-0.2, 0, 0.25))
    area_light("Cool edge", (-1.2, 0.6, 1.1), 170, 1.1,
               color=(0.57, 0.76, 1.0), target=(-0.2, 0, 0.25))
    area_light("Warm fill", (0.4, 1.1, 0.7), 120, 1.1,
               color=(1.0, 0.66, 0.35), target=(-0.2, 0, 0.25))
    return scene
