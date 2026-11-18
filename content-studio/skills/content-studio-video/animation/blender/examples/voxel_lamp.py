"""Original grid-built voxel lamp with stepped head motion and light cue."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, material, reset_scene


VOXEL_M = 0.05
FACES = {
    (0, -1, 0): (0, 1, 5, 4),
    (0, 1, 0): (3, 7, 6, 2),
    (-1, 0, 0): (0, 4, 7, 3),
    (1, 0, 0): (1, 2, 6, 5),
    (0, 0, -1): (0, 3, 2, 1),
    (0, 0, 1): (4, 5, 6, 7),
}


def voxels(name, cells, mat, collection):
    """Emit exposed grid faces only so hidden cube interiors add no polygons."""
    occupied = set(cells)
    vertices, polygons = [], []
    half = VOXEL_M / 2
    for x, y, z in sorted(occupied):
        center = (x * VOXEL_M, y * VOXEL_M, (z + 0.5) * VOXEL_M)
        corners = [
            (center[0] + sx * half, center[1] + sy * half, center[2] + sz * half)
            for sx, sy, sz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                               (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))
        ]
        for direction, face in FACES.items():
            if tuple(a + b for a, b in zip((x, y, z), direction)) in occupied:
                continue
            start = len(vertices)
            vertices.extend(corners[index] for index in face)
            polygons.append(tuple(range(start, start + 4)))
    mesh = bpy.data.meshes.new(name + " grid")
    mesh.from_pydata(vertices, [], polygons)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(mat)
    obj["voxel_size_m"] = VOXEL_M
    obj["occupied_cells"] = len(occupied)
    return obj


def parent_keep_world(obj, pivot):
    bpy.context.view_layer.update()
    transform = obj.matrix_world.copy()
    obj.parent = pivot
    obj.matrix_world = transform


def constant_position_keys(obj):
    """Keep every in-between frame on the declared grid."""
    action = obj.animation_data.action
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves
    else:
        curves = action.fcurves
    for curve in curves:
        if curve.data_path == "location":
            for point in curve.keyframe_points:
                point.interpolation = "CONSTANT"


def make_scene(spec, spec_dir=Path(".")):
    if abs(float(spec.get("voxel_size_m", VOXEL_M)) - VOXEL_M) > 1e-8:
        raise ValueError("This authored voxel benchmark uses a 0.05 m grid")
    scene = reset_scene(spec, background=(0.018, 0.035, 0.055))
    scene.unit_settings.system = "METRIC"
    prop = bpy.data.collections.new("COL_Voxel_Prop")
    scene.collection.children.link(prop)
    teal = material("Voxel teal", (0.06, 0.42, 0.44), roughness=0.85)
    copper = material("Voxel copper", (0.58, 0.3, 0.11), roughness=0.76)
    graphite = material("Voxel graphite", (0.05, 0.08, 0.1), roughness=0.9)
    paper = material("Voxel notebook", (0.73, 0.62, 0.4), roughness=1)
    gold = material("Voxel bulb", (1.0, 0.55, 0.13), roughness=0.8,
                    emission=(1.0, 0.52, 0.12), emission_strength=0.1)
    ground = material("Voxel navy stage", (0.045, 0.07, 0.095), roughness=1)
    cube("SM_Voxel_Stage", (0, 0, -0.055), (1.8, 1.6, 0.1), ground)
    voxels("SM_Voxel_Notebook", {(x, y, 0) for x in range(-10, -4)
                                  for y in range(-2, 3)}, paper, prop)
    base = {(x, y, z) for x in range(-3, 4) for y in range(-3, 4)
            for z in (0, 1) if x * x + y * y <= 10}
    voxels("SM_Voxel_Base", base, teal, prop)
    voxels("SM_Voxel_Lower_Arm", {(-round((z - 2) * 0.4), 0, z)
                                   for z in range(2, 8)}, copper, prop)
    voxels("SM_Voxel_Elbow", {(-2, 0, 7), (-2, 0, 8)}, graphite, prop)

    bpy.ops.object.empty_add(location=(-2 * VOXEL_M, 0, 8 * VOXEL_M))
    pivot = bpy.context.object
    pivot.name = "Voxel head control"
    # Cell coordinates remain integer-valued; the control moves in whole voxels.
    upper = voxels("SM_Voxel_Upper_Arm",
                   {(-2, 0, 8), (-3, 0, 8), (-3, 0, 9), (-4, 0, 9),
                    (-5, 0, 10), (-6, 0, 10)}, copper, prop)
    parent_keep_world(upper, pivot)
    shade = voxels("SM_Voxel_Shade",
                   {(-6, 0, 11)} |
                   {(x, y, 10) for x in range(-7, -4) for y in range(-1, 2)} |
                   {(x, y, 9) for x in range(-8, -3) for y in range(-2, 3)},
                   teal, prop)
    parent_keep_world(shade, pivot)
    bulb = voxels("SM_Voxel_Bulb", {(x, y, 8) for x in range(-7, -4)
                                    for y in range(-1, 2)}, gold, prop)
    parent_keep_world(bulb, pivot)
    bpy.ops.object.light_add(type="SPOT", location=(-6 * VOXEL_M, 0, 8 * VOXEL_M))
    task = bpy.context.object
    task.name = "Voxel task light"
    task.data.color = (1, 0.62, 0.22)
    task.data.spot_size = 0.9
    task.data.spot_blend = 0.05
    parent_keep_world(task, pivot)

    for frame, x, z in ((1, -2, 8), (25, -2, 7), (49, -2, 6), (72, -2, 6)):
        pivot.location = (x * VOXEL_M, 0, z * VOXEL_M)
        pivot.keyframe_insert(data_path="location", frame=frame)
    constant_position_keys(pivot)
    glow = gold.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    glow.default_value = 0.1
    glow.keyframe_insert(data_path="default_value", frame=1)
    glow.default_value = 3.0
    glow.keyframe_insert(data_path="default_value", frame=38)
    task.data.energy = 0
    task.data.keyframe_insert(data_path="energy", frame=1)
    task.data.energy = 170
    task.data.keyframe_insert(data_path="energy", frame=38)
    task.data.keyframe_insert(data_path="energy", frame=72)
    camera("Voxel camera", (1.2, -1.6, 1.0), (-0.2, 0, 0.25), lens=47)
    area_light("Voxel key", (0.5, -1.2, 1.5), 170, 1.0,
               target=(-0.2, 0, 0.3))
    return scene
