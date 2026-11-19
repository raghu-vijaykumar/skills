"""Code-sculpted guardian, shrinkwrapped quad cage, and atlased hair cards."""

import math
from pathlib import Path

import bpy
from mathutils import Vector

from common import area_light, camera, cylinder, material, reset_scene, sphere


def collection(name):
    group = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(group)
    return group


def move_to(obj, group):
    for prior in tuple(obj.users_collection):
        prior.objects.unlink(obj)
    group.objects.link(obj)
    return obj


def face_forms(obj):
    # Primary brow, cheek, muzzle, and jaw masses precede multires surface detail.
    for vert in obj.data.vertices:
        x, y, z = vert.co
        front = max(0.0, -y)
        brow = math.exp(-((abs(x) - 0.32) / 0.20) ** 2 - ((z - 0.25) / 0.18) ** 2)
        cheek = math.exp(-((abs(x) - 0.43) / 0.25) ** 2 - ((z + 0.10) / 0.25) ** 2)
        muzzle = math.exp(-(x / 0.32) ** 2 - ((z + 0.28) / 0.22) ** 2)
        vert.co.x = x * (0.66 - 0.09 * max(0.0, -z))
        vert.co.y = y * 0.53 - front * (0.08 * brow + 0.06 * cheek + 0.15 * muzzle)
        vert.co.z = z * 0.79 + 0.025 * brow - 0.018 * cheek
    obj.data.update()


def duplicate(obj, name, x, group, *, hidden=False):
    copy = obj.copy()
    copy.data = obj.data.copy()
    copy.name = name
    group.objects.link(copy)
    copy.location.x = x
    copy.hide_render = hidden
    return copy


def high_sculpt(mat, x, high_group, reference_group, *, detailed):
    obj = sphere("SM_Guardian_High_Sculpt", (x, 0, 1.22), 1.0, mat,
                 segments=32, rings=18)
    move_to(obj, high_group)
    base = duplicate(obj, "SM_Guardian_Clean_Base", x, reference_group,
                     hidden=True)
    base["before_surface_sculpt"] = True
    if detailed:
        face_forms(obj)
        # Multires remains editable; restrained cloud displacement adds stone
        # pores only after the large silhouette and facial masses exist.
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        multi = obj.modifiers.new("Primary-to-tertiary Multires", "MULTIRES")
        for _ in range(2):
            bpy.ops.object.multires_subdivide(modifier=multi.name,
                                              mode="CATMULL_CLARK")
        multi.levels = multi.sculpt_levels = multi.render_levels = 2
        texture = bpy.data.textures.new("T_Guardian_StonePores", type="CLOUDS")
        texture.noise_scale = 0.09
        texture.noise_depth = 2
        displacement = obj.modifiers.new("Tertiary stone pore relief", "DISPLACE")
        displacement.texture = texture
        displacement.strength = 0.025
        displacement.mid_level = 0.5
        obj["surface_pass"] = "primary facial masses, multires subdivision, tertiary pore relief"
    return obj


def feature(name, location, scale, mat, group):
    obj = sphere(name, location, 1, mat, segments=20, rings=10)
    obj.scale = scale
    return move_to(obj, group)


def add_features(x, group, body_mat, eye_mat, *, finished):
    for side in (-1, 1):
        feature(f"Guardian {x:.1f} ear {side}",
                (x + side * 0.52, 0.01, 1.92), (0.22, 0.19, 0.46),
                body_mat, group)
        feature(f"Guardian {x:.1f} eye {side}",
                (x + side * 0.26, -0.51, 1.35), (0.105, 0.055, 0.10),
                eye_mat, group)
        if finished:
            feature(f"Guardian {x:.1f} brow ridge {side}",
                    (x + side * 0.26, -0.49, 1.50), (0.22, 0.07, 0.045),
                    body_mat, group)
    feature(f"Guardian {x:.1f} nose", (x, -0.54, 1.02),
            (0.20, 0.18, 0.16), body_mat, group)


def hair_atlas():
    image = bpy.data.images.new("T_Hair_Guardian_RGBA", 256, 256, alpha=True)
    image.colorspace_settings.name = "sRGB"
    pixels = []
    for y in range(256):
        for x in range(256):
            strip = x // 64
            local = (x % 64) / 63
            # Four padded, vertically flowing clumps share a compact RGBA atlas.
            edge = min(local, 1 - local)
            alpha = max(0.0, min(1.0, (edge - 0.07) * 11))
            alpha *= max(0.0, min(1.0, (255 - y) / 28))
            grain = 0.035 * math.sin(y * 0.27 + strip * 1.7)
            tone = 0.88 + strip * 0.035
            pixels.extend(((0.20 + grain) * tone, (0.31 + grain) * tone,
                           (0.31 + grain * 0.5) * tone, alpha))
    image.pixels.foreach_set(pixels)
    image.pack()
    return image


def hair_material(image):
    mat = material("MAT_Guardian_HairCards", (0.19, 0.30, 0.31), roughness=0.84)
    mat.surface_render_method = "DITHERED"
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Packed guardian hair atlas"
    tex.image = image
    bsdf = nodes.get("Principled BSDF")
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    mat["clump_strips"] = 4
    return mat


def hair_card(index, side, xpos, mat, group):
    band = index % 16
    t = band / 15
    root = Vector((side * (0.06 + 0.46 * t), -0.35 + 0.12 * (band % 3),
                   1.91 - 0.12 * t))
    tip = Vector((side * (0.24 + 0.53 * t), root.y - 0.13,
                  1.57 - 0.34 * t))
    flow = tip - root
    across = Vector((-flow.z, 0, flow.x)).normalized()
    width = 0.075 + 0.018 * (band % 4)
    vertices = []
    for step in range(5):
        u = step / 4
        center = root.lerp(tip, u)
        center.y -= 0.07 * math.sin(math.pi * u)
        half = width * (1 - 0.78 * u)
        vertices.extend((center - across * half, center + across * half))
    faces = [(2 * step, 2 * step + 1, 2 * step + 3, 2 * step + 2)
             for step in range(4)]
    mesh = bpy.data.meshes.new(f"Guardian hair card {index:02d} mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="HairAtlasUV")
    strip = index % 4
    for poly in mesh.polygons:
        row = poly.index
        for loop_idx in poly.loop_indices:
            vertex = mesh.loops[loop_idx].vertex_index
            horizontal = 0.10 if vertex % 2 == 0 else 0.90
            uv.data[loop_idx].uv = ((strip + horizontal) / 4,
                                    (vertex // 2) / 4)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(f"SM_HairCard_Guardian_{index:02d}", mesh)
    group.objects.link(obj)
    obj.location.x = xpos
    obj.shape_key_add(name="Basis")
    breeze = obj.shape_key_add(name="Breeze")
    for index_in_card, vertex in enumerate(breeze.data):
        row = index_in_card // 2
        vertex.co.x += side * 0.11 * (row / 4) ** 2
        vertex.co.y -= 0.025 * (row / 4)
    for frame, value in ((1, 0), (36, 1), (72, 0)):
        breeze.value = value
        breeze.keyframe_insert(data_path="value", frame=frame)
    obj["flow_region"] = "forehead-to-temple fan"
    return obj


def label(text, location, mat):
    data = bpy.data.curves.new(text, "FONT")
    data.body = text
    data.align_x = "CENTER"
    data.size = 0.13
    obj = bpy.data.objects.new(text, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler.x = math.pi / 2
    data.materials.append(mat)
    return obj


def make_scene(spec, spec_dir: Path):
    variant = int(spec.get("variant", 2))
    if variant not in (1, 2):
        raise ValueError("Unknown guardian craft candidate")
    scene = reset_scene(spec, background=(0.015, 0.028, 0.038))
    scene.unit_settings.system = "METRIC"
    scene["guardian_variant"] = variant
    high_group = collection("COL_Guardian_High")
    low_group = collection("COL_Guardian_Low")
    reference_group = collection("COL_Guardian_Reference")
    hair_group = collection("COL_Hair_Guardian")
    clay = material("MAT_Guardian_TerracottaClay", (0.65, 0.34, 0.23),
                    roughness=0.88)
    jade = material("MAT_Guardian_RetopoJade", (0.13, 0.50, 0.45),
                    roughness=0.52)
    charcoal = material("MAT_Guardian_Eyes", (0.025, 0.07, 0.08), roughness=0.30)
    grey = material("MAT_Guardian_GreyBlock", (0.48, 0.55, 0.55), roughness=0.85)
    high = high_sculpt(clay if variant == 2 else grey, -1.18, high_group,
                       reference_group, detailed=variant == 2)
    target = duplicate(high, "SM_Guardian_High_Reference", 1.18,
                       reference_group, hidden=True)
    low = sphere("SM_Guardian_Low_Retopo", (1.18, 0, 1.22), 1,
                 jade if variant == 2 else grey, segments=24, rings=14)
    move_to(low, low_group)
    if variant == 2:
        face_forms(low)
        wrap = low.modifiers.new("Sculpt silhouette shrinkwrap", "SHRINKWRAP")
        wrap.target = target
        wrap.wrap_method = "NEAREST_SURFACEPOINT"
        wrap.offset = 0.012
        low["retopo_intent"] = "quad-dominant static head shell, shrinkwrapped to multires reference"
        # A separate wire copy exposes the actual cage density in the delivered shot.
        cage = duplicate(low, "SM_Guardian_Retopo_Cage_Display", 1.18,
                         low_group)
        cage.data.materials.clear()
        cage.data.materials.append(material("MAT_Guardian_CageLines", (0.025, 0.13, 0.14),
                                           roughness=1.0))
        cage.modifiers["Sculpt silhouette shrinkwrap"].offset = 0.018
        wire = cage.modifiers.new("Visible retopology quads", "WIREFRAME")
        wire.thickness = 0.003
    for x, group, mat in ((-1.18, high_group, clay if variant == 2 else grey),
                          (1.18, low_group, jade if variant == 2 else grey)):
        add_features(x, group, mat, charcoal, finished=variant == 2)
    if variant == 2:
        atlas = hair_atlas()
        hair = hair_material(atlas)
        cap = material("MAT_Guardian_HairCap", (0.17, 0.29, 0.29),
                       roughness=0.86)
        feature("SM_Guardian_ScalpCap", (1.18, 0.01, 1.86),
                (0.61, 0.45, 0.22), cap, hair_group)
        for index in range(32):
            hair_card(index, 1 if index < 16 else -1, 1.18, hair, hair_group)
    stage = material("MAT_Guardian_Stage", (0.09, 0.17, 0.19), roughness=0.79)
    line = material("MAT_Guardian_Label", (0.015, 0.075, 0.08),
                    roughness=1.0)
    for x, name in ((-1.18, "Guardian sculpt pedestal"),
                    (1.18, "Guardian retopo pedestal")):
        cylinder(name, (x, 0, 0.02), 0.90, 0.10, stage, vertices=48, edge=0.04)
    label("HIGH SCULPT", (-1.18, -1.02, 0.18), line)
    label("RETOPO + GROOM", (1.18, -1.02, 0.18), line)
    cam = camera("Guardian craft comparison camera", (0, -6.2, 2.0),
                 (0, 0, 1.22), ortho=5.25)
    if variant == 2:
        for frame, x, y in ((1, -0.12, -6.2), (36, 0.03, -5.86),
                            (72, 0.16, -5.7)):
            cam.location.x, cam.location.y = x, y
            cam.keyframe_insert(data_path="location", frame=frame)
    area_light("Guardian warm key", (-3.2, -3.0, 4.5), 900, 3,
               color=(1.0, 0.78, 0.57), target=(-0.5, 0, 1.2))
    area_light("Guardian cool fill", (3.0, -2.0, 3.3), 650, 2.8,
               color=(0.46, 0.91, 0.93), target=(1, 0, 1.2))
    area_light("Guardian upper rim", (0, 2.0, 4.2), 700, 2.2,
               target=(0, 0, 1.7))
    return scene
