"""Four LODs, packed texture channels, and a separate convex crate proxy."""

import math
from pathlib import Path

import bpy

from common import area_light, camera, cube, material, reset_scene


BOX_FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
LOD_BOX_COUNTS = (22, 10, 6, 2)


def collection(name):
    group = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(group)
    return group


def assign(obj, group):
    for prior in tuple(obj.users_collection):
        prior.objects.unlink(obj)
    group.objects.link(obj)
    return obj


def add_box(vertices, faces, face_materials, center, size, material_index):
    x, y, z = center
    sx, sy, sz = (value / 2 for value in size)
    start = len(vertices)
    vertices.extend(((x - sx, y - sy, z - sz), (x + sx, y - sy, z - sz),
                     (x + sx, y + sy, z - sz), (x - sx, y + sy, z - sz),
                     (x - sx, y - sy, z + sz), (x + sx, y - sy, z + sz),
                     (x + sx, y + sy, z + sz), (x - sx, y + sy, z + sz)))
    for face in BOX_FACES:
        faces.append(tuple(start + index for index in face))
        face_materials.append(material_index)


def atlas_image(name, *, orm=False):
    image = bpy.data.images.new(name, width=256, height=256, alpha=True)
    image.colorspace_settings.name = "Non-Color" if orm else "sRGB"
    pixels = []
    for y in range(256):
        for x in range(256):
            # Six atlas cells share the same grain scale, with panel-to-panel tone shifts.
            panel = (x // 85) + 3 * (y // 128)
            line = math.sin(y * 0.31 + math.sin(x * 0.055) * 1.4)
            grain = 0.045 * line + 0.018 * math.sin(y * 1.35)
            border = min(x % 85, 84 - x % 85, y % 128, 127 - y % 128) < 3
            if orm:
                pixels.extend((0.78 if border else 0.96,
                               0.72 if border else 0.58 + 0.025 * (panel % 3),
                               0.0, 1.0))
            else:
                dark = 0.72 if border else 1.0
                shade = 0.90 + 0.025 * (panel % 3)
                pixels.extend((max(0.0, (0.45 + grain) * shade * dark),
                               max(0.0, (0.24 + grain * 0.55) * shade * dark),
                               max(0.0, (0.105 + grain * 0.25) * shade * dark), 1.0))
    image.pixels.foreach_set(pixels)
    image.pack()
    return image


def atlas_material(color_image, orm_image):
    wood = material("MAT_Crate_WoodAtlas", (0.44, 0.24, 0.11), roughness=0.6)
    nodes, links = wood.node_tree.nodes, wood.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    color = nodes.new("ShaderNodeTexImage")
    color.name = "Crate base-color atlas"
    color.image = color_image
    color.interpolation = "Linear"
    orm = nodes.new("ShaderNodeTexImage")
    orm.name = "Crate AO-roughness-metallic atlas"
    orm.image = orm_image
    split = nodes.new("ShaderNodeSeparateColor")
    split.name = "Unpack ORM channels"
    links.new(color.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(orm.outputs["Color"], split.inputs["Color"])
    links.new(split.outputs["Green"], bsdf.inputs["Roughness"])
    links.new(split.outputs["Blue"], bsdf.inputs["Metallic"])
    wood["orm_red_is_ao"] = True
    return wood


def crate_mesh(name, lod, group, wood, metal, *, use_atlas):
    vertices, faces, face_materials = [], [], []
    add_box(vertices, faces, face_materials, (0, 0, 0), (1.16, 1.16, 1.16), 0)
    if lod <= 2:
        # Corner battens survive LOD2 because they define the crate silhouette.
        for x in (-0.53, 0.53):
            for y in (-0.53, 0.53):
                add_box(vertices, faces, face_materials,
                        (x, y, 0), (0.10, 0.10, 1.16), 1)
    if lod <= 1:
        for y in (-0.54, 0.54):
            for z in (-0.51, 0.51):
                add_box(vertices, faces, face_materials,
                        (0, y, z), (1.16, 0.10, 0.12), 1)
    if lod == 0:
        for x in (-0.43, -0.14, 0.14, 0.43):
            for z in (-0.39, 0.0, 0.39):
                add_box(vertices, faces, face_materials,
                        (x, -0.595, z), (0.045, 0.025, 0.045), 1)
    # The badge keeps both material slots meaningful even on the cheapest LOD.
    add_box(vertices, faces, face_materials,
            (0, -0.595, 0), (0.38, 0.025, 0.15), 1)
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for polygon, material_index in zip(mesh.polygons, face_materials):
        polygon.material_index = material_index
    mesh.materials.append(wood)
    mesh.materials.append(metal)
    texture_uv = mesh.uv_layers.new(name="UVMap")
    lightmap_uv = mesh.uv_layers.new(name="LightmapUV")
    face_count = len(mesh.polygons)
    columns = math.ceil(math.sqrt(face_count))
    rows = math.ceil(face_count / columns)
    for index, polygon in enumerate(mesh.polygons):
        # Body faces occupy six unique atlas cells; repeated trim knowingly shares one.
        panel = index if index < 6 else 0
        col, row = panel % 3, panel // 3
        cell = ((0.01 + col / 3, 0.01 + row / 2),
                ((col + 1) / 3 - 0.01, 0.01 + row / 2),
                ((col + 1) / 3 - 0.01, (row + 1) / 2 - 0.01),
                (0.01 + col / 3, (row + 1) / 2 - 0.01))
        lcol, lrow = index % columns, index // columns
        light_cell = ((0.004 + lcol / columns, 0.004 + lrow / rows),
                      ((lcol + 1) / columns - 0.004, 0.004 + lrow / rows),
                      ((lcol + 1) / columns - 0.004,
                       (lrow + 1) / rows - 0.004),
                      (0.004 + lcol / columns, (lrow + 1) / rows - 0.004))
        for loop_index, uv, light_uv in zip(polygon.loop_indices, cell, light_cell):
            texture_uv.data[loop_index].uv = uv
            lightmap_uv.data[loop_index].uv = light_uv
    obj = bpy.data.objects.new(name, mesh)
    group.objects.link(obj)
    obj["lod_index"] = lod
    obj["texture_atlas"] = use_atlas
    obj["screen_size_min"] = (0.50, 0.25, 0.10, 0.0)[lod]
    obj["screen_size_max"] = (1.0, 0.50, 0.25, 0.10)[lod]
    return obj


def label(group, name, text, location, mat):
    bpy.ops.object.text_add(location=location, rotation=(math.pi / 2, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = text
    obj.data.size = 0.25
    obj.data.extrude = 0.003
    obj.data.materials.append(mat)
    return assign(obj, group)


def proxy_outline(group, mat):
    root = bpy.data.objects.new("Collision view control", None)
    group.objects.link(root)
    root.location = (3.55, 0, 2.17)
    for x in (-0.51, 0.51):
        for y in (-0.51, 0.51):
            rod = assign(cube(f"Collision edge vertical {x} {y}",
                              (x, y, 0), (0.018, 0.018, 1.04), mat), group)
            rod.parent = root
    for z in (-0.51, 0.51):
        for x in (-0.51, 0.51):
            rod = assign(cube(f"Collision edge Y {x} {z}",
                              (x, 0, z), (0.018, 1.04, 0.018), mat), group)
            rod.parent = root
        for y in (-0.51, 0.51):
            rod = assign(cube(f"Collision edge X {y} {z}",
                              (0, y, z), (1.04, 0.018, 0.018), mat), group)
            rod.parent = root
    for frame, z in ((1, 2.17), (40, 2.17), (72, 0.87)):
        root.location.z = z
        root.keyframe_insert(data_path="location", frame=frame)
    return root


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown pipeline candidate")
    scene = reset_scene(spec, background=(0.012, 0.020, 0.032))
    scene.unit_settings.system = "METRIC"
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.28
    stage = collection("COL_Pipeline_Stage")
    lods = collection("COL_LODs_Crate")
    export = collection("COL_Export_Crate")
    collision = collection("COL_Collision_Crate")
    overlay = collection("COL_Collision_Visual")
    lights = collection("COL_Pipeline_Lights")
    stage_mat = material("MAT_Pipeline_Stage", (0.045, 0.07, 0.10), roughness=0.72)
    pad_mat = material("MAT_Pipeline_Pad", (0.08, 0.12, 0.17), roughness=0.62)
    text_mat = material("MAT_Pipeline_Label", (0.50, 0.83, 0.94),
                        emission=(0.43, 0.77, 0.90), emission_strength=0.6)
    metal = material("MAT_Crate_Metal", (0.11, 0.18, 0.21), metallic=0.75,
                     roughness=0.34)
    clay = material("MAT_Crate_Clay", (0.44, 0.46, 0.44), roughness=0.78)
    color_image = atlas_image("T_Crate_BaseColor") if variant == 2 else None
    orm_image = atlas_image("T_Crate_ORM", orm=True) if variant == 2 else None
    wood = atlas_material(color_image, orm_image) if variant == 2 else clay
    accent = material("MAT_Collision_Cyan", (0.06, 0.62, 0.75),
                      emission=(0.04, 0.52, 0.73), emission_strength=1.5)
    assign(cube("SM_Pipeline_Stage", (0, 0, -0.12),
                (9.6, 4.0, 0.24), stage_mat, edge=0.10), stage)
    positions = (-3.55, -1.18, 1.18, 3.55)
    actual = []
    for lod, x in enumerate(positions):
        assign(cube(f"SM_Pipeline_Pad_{lod}", (x, 0, 0.10),
                    (1.82, 1.82, 0.20), pad_mat, edge=0.05), stage)
        obj = crate_mesh(f"SM_Crate_LOD{lod}", lod, lods, wood,
                         metal if variant == 2 else clay, use_atlas=variant == 2)
        obj.location = (x, 0, 0.80)
        for frame, angle in ((1, -0.17), (36, 0.0), (72, 0.22)):
            obj.rotation_euler.z = angle if variant == 2 else 0
            if variant == 2:
                obj.keyframe_insert(data_path="rotation_euler", frame=frame)
        actual.append(len(obj.data.polygons) * 2)
        label(stage, f"LOD{lod} label", f"LOD{lod}  {actual[-1]}T",
              (x - 0.60, -1.37, 0.08), text_mat)
        # Export copies share geometry but have clean origins and no gallery animation.
        copy = obj.copy()
        copy.data = obj.data.copy()
        copy.name = f"SM_Crate_Export_LOD{lod}"
        copy.animation_data_clear()
        copy.location = (0, 0, 0)
        copy.rotation_euler = (0, 0, 0)
        copy.hide_render = True
        export.objects.link(copy)
    # The physical collider is distinct from every render LOD and from its animated outline.
    proxy_mesh = bpy.data.meshes.new("Crate convex collision mesh")
    vertices, faces, face_materials = [], [], []
    add_box(vertices, faces, face_materials, (0, 0, 0), (1.02, 1.02, 1.02), 0)
    proxy_mesh.from_pydata(vertices, [], faces)
    proxy_mesh.update()
    proxy = bpy.data.objects.new("UCX_SM_Crate_Export_01", proxy_mesh)
    collision.objects.link(proxy)
    proxy.hide_render = True
    if variant == 2:
        proxy_outline(overlay, accent)
    assign(area_light("LGT_Pipeline_Key", (-3, -3.5, 5.8), 1300, 4.2,
                      target=(0, 0, 0.5)), lights)
    assign(area_light("LGT_Pipeline_Rim", (3, 2.8, 4.7), 1000, 3.8,
                      color=(0.44, 0.76, 1.0), target=(0, 0, 0.7)), lights)
    cam = assign(camera("Pipeline comparison camera", (0, -8.2, 5.3),
                        (0, 0, 0.78), ortho=10.8), stage)
    scene["pipeline_variant"] = variant
    scene["lod_triangles"] = actual
    scene["atlas_resolution"] = 256 if variant == 2 else 0
    scene["collision_size_m"] = [1.02, 1.02, 1.02]
    return scene
