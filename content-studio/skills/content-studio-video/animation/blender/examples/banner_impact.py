"""Pinned cloth, baked rigid-body impact, and timed game-style energy ribbons."""

import math
from pathlib import Path

import bpy
from mathutils import Vector

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def collection(name):
    group = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(group)
    return group


def move_to(obj, group):
    for prior in tuple(obj.users_collection):
        prior.objects.unlink(obj)
    group.objects.link(obj)
    return obj


def label(text, location, mat, size=0.15):
    data = bpy.data.curves.new(text, "FONT")
    data.body = text
    data.align_x = "CENTER"
    data.size = size
    data.materials.append(mat)
    obj = bpy.data.objects.new(text, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler.x = math.pi / 2
    return obj


def banner_mesh(mat, group):
    # Even quad spacing and a separate pin column keep the wind test stable.
    vertices = [(-2.05 + col * 0.125, 0, 2.18 - row * 0.10)
                for row in range(9) for col in range(13)]
    faces = [(row * 13 + col, row * 13 + col + 1,
              (row + 1) * 13 + col + 1, (row + 1) * 13 + col)
             for row in range(8) for col in range(12)]
    mesh = bpy.data.meshes.new("Banner 13 by 9 quad mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(mat)
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new("SRC_Cloth_Banner", mesh)
    group.objects.link(obj)
    return obj


def bake_banner(source, group, wind_strength):
    scene = bpy.context.scene
    pin = source.vertex_groups.new(name="PIN_Cloth")
    pin.add([row * 13 for row in range(9)], 1, "REPLACE")
    cloth = source.modifiers.new("Wind-blown banner cloth", "CLOTH")
    cloth.settings.quality = 8
    cloth.settings.mass = 0.3
    cloth.settings.air_damping = 1.0
    cloth.settings.vertex_group_mass = pin.name
    cloth.settings.pin_stiffness = 1.0
    cloth.point_cache.frame_start = 1
    cloth.point_cache.frame_end = 92
    # Outward wind keeps the flag broadside to the review camera while gravity
    # still forms its folds; a transverse gust would turn this thin mesh edge-on.
    bpy.ops.object.effector_add(type="WIND", location=(-3.0, 0, 1.7),
                                rotation=(0, math.pi / 2, 0.24))
    wind = bpy.context.object
    wind.name = "SRC_Wind_Banner"
    for frame, strength in ((1, 11), (21, wind_strength), (42, 8),
                            (66, wind_strength + 4), (92, 11)):
        wind.field.strength = strength
        wind.field.keyframe_insert(data_path="strength", frame=frame)
    wind["baked_strength_range"] = [8, wind_strength + 4]
    move_to(wind, group)
    samples = []
    # A 20-frame settle precedes the 72 delivered frames.
    for frame in range(1, 93):
        scene.frame_set(frame)
        if frame >= 21:
            evaluated = source.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
            samples.append([vertex.co.copy() for vertex in mesh.vertices])
            evaluated.to_mesh_clear()
    if len(samples) != 72:
        raise RuntimeError("Cloth bake did not cover the shot")
    # Bake to shape keys so each resumable render frame is self-contained.
    baked = bpy.data.objects.new("SM_Baked_Wind_Banner", source.data.copy())
    group.objects.link(baked)
    baked.shape_key_add(name="Basis")
    for frame, coords in enumerate(samples, start=1):
        key = baked.shape_key_add(name=f"Cloth_{frame:03d}")
        for vertex, coordinate in zip(key.data, coords):
            vertex.co = coordinate
        keys = ([(frame - 1, 0)] if frame > 1 else []) + [(frame, 1)]
        keys += [(frame + 1, 0)] if frame < 72 else []
        for at, value in keys:
            key.value = value
            key.keyframe_insert(data_path="value", frame=at)
    solid = baked.modifiers.new("Fabric thickness", "SOLIDIFY")
    solid.thickness = 0.012
    source.hide_render = True
    cloth.show_render = cloth.show_viewport = False
    wind.animation_data_clear()
    wind.field.strength = 0
    scene["cloth_preroll"] = 20
    scene["cloth_baked_frames"] = 72
    return baked


def impact_orb(orb_mat, plate, group):
    scene = bpy.context.scene
    source = sphere("SRC_Rigidbody_Orb", (1.37, 0, 2.28), 0.25,
                    orb_mat, segments=24, rings=12)
    move_to(source, group)
    bpy.context.view_layer.objects.active = source
    bpy.ops.object.select_all(action="DESELECT")
    source.select_set(True)
    bpy.ops.rigidbody.object_add()
    source.rigid_body.type = "ACTIVE"
    source.rigid_body.collision_shape = "SPHERE"
    source.rigid_body.use_margin = True
    source.rigid_body.collision_margin = 0.02
    source.rigid_body.restitution = 0.30
    source.rigid_body.friction = 0.65
    bpy.context.view_layer.objects.active = plate
    bpy.ops.object.select_all(action="DESELECT")
    plate.select_set(True)
    bpy.ops.rigidbody.object_add()
    plate.rigid_body.type = "PASSIVE"
    plate.rigid_body.collision_shape = "BOX"
    plate.rigid_body.use_margin = True
    plate.rigid_body.collision_margin = 0.02
    world = scene.rigidbody_world
    world.substeps_per_frame = 120
    world.solver_iterations = 20
    world.point_cache.frame_start = 1
    world.point_cache.frame_end = 72
    samples = []
    # Record the physics engine's evaluated world transforms, then play only
    # those baked keys in the delivery object.
    for frame in range(1, 73):
        scene.frame_set(frame)
        samples.append(source.matrix_world.copy())
    baked = bpy.data.objects.new("SM_Baked_Impact_Orb", source.data.copy())
    group.objects.link(baked)
    baked.rotation_mode = "QUATERNION"
    for frame, matrix in enumerate(samples, start=1):
        baked.location = matrix.translation
        baked.rotation_quaternion = matrix.to_quaternion()
        baked.keyframe_insert(data_path="location", frame=frame)
        baked.keyframe_insert(data_path="rotation_quaternion", frame=frame)
    source.hide_render = True
    impact = next((frame for frame, matrix in enumerate(samples, start=1)
                   if matrix.translation.z <= 0.56), None)
    if impact is None:
        raise RuntimeError("Rigid body never reached the conductive plate")
    scene["physics_baked_frames"] = len(samples)
    scene["impact_frame"] = impact
    return baked, impact


def energy_ribbons(group, impact, *, complete):
    # The game-style FX route uses authored emissive meshes with start/peak/tail
    # timing; it makes no claim about Mantaflow or particle simulation.
    amber = material("MAT_FX_Amber", (0.8, 0.25, 0.02), roughness=0.35,
                     emission=(1.0, 0.38, 0.04), emission_strength=7)
    cyan = material("MAT_FX_Cyan", (0.02, 0.55, 0.74), roughness=0.35,
                    emission=(0.15, 0.9, 1.0), emission_strength=6)
    for index in range(12):
        angle = 2 * math.pi * index / 12
        inner, outer = 0.24, 0.60 + 0.12 * (index % 3)
        width = 0.035 + 0.014 * (index % 2)
        center = Vector((1.37, -0.20, 0.37))
        along = Vector((math.cos(angle), 0, math.sin(angle)))
        side = Vector((-along.z, 0, along.x))
        vertices = [center + along * inner - side * width,
                    center + along * inner + side * width,
                    center + along * outer + side * width * 0.16,
                    center + along * outer - side * width * 0.16]
        mesh = bpy.data.meshes.new(f"Impact ribbon {index:02d} mesh")
        mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
        mesh.update()
        mesh.materials.append(amber if index % 2 else cyan)
        obj = bpy.data.objects.new(f"FX_Impact_Ribbon_{index:02d}", mesh)
        group.objects.link(obj)
        obj["fx_kind"] = "timed emissive mesh ribbon"
        if complete:
            for frame, scale in ((1, 0), (max(1, impact - 3), 0),
                                 (impact + 1, 1), (impact + 13, 0)):
                obj.scale = (scale, scale, scale)
                obj.keyframe_insert(data_path="scale", frame=frame)
        else:
            obj.hide_render = True
    bpy.ops.mesh.primitive_torus_add(major_segments=48, minor_segments=8,
                                     location=(1.37, -0.21, 0.37),
                                     rotation=(math.pi / 2, 0, 0),
                                     major_radius=0.30, minor_radius=0.012)
    ring = bpy.context.object
    ring.name = "FX_Impact_Ring"
    ring.data.materials.append(cyan)
    move_to(ring, group)
    if complete:
        for frame, scale in ((1, 0.01), (max(1, impact - 3), 0.01),
                             (impact + 1, 1), (impact + 12, 1.8),
                             (impact + 20, 0.01)):
            ring.scale = (scale, scale, scale)
            ring.keyframe_insert(data_path="scale", frame=frame)
    else:
        ring.hide_render = True
    return ring


def make_scene(spec, spec_dir: Path):
    variant = int(spec.get("variant", 2))
    if variant not in (1, 2):
        raise ValueError("Unknown banner impact candidate")
    scene = reset_scene(spec, background=(0.012, 0.024, 0.037))
    scene.unit_settings.system = "METRIC"
    scene["banner_impact_variant"] = variant
    cloth_group = collection("COL_Cloth_Banner")
    physical_group = collection("COL_Physics_Impact")
    fx_group = collection("COL_FX_Impact")
    ink = material("MAT_Stage_Ink", (0.035, 0.085, 0.11), roughness=0.85)
    gold = material("MAT_Stage_Brass", (0.58, 0.30, 0.11), metallic=0.68,
                    roughness=0.36)
    fabric = material("MAT_Banner_DeepTeal", (0.025, 0.40, 0.43),
                      roughness=0.95)
    metal = material("MAT_Orb_Copper", (0.66, 0.20, 0.08), metallic=0.85,
                     roughness=0.22)
    grey = material("MAT_Greyblock", (0.42, 0.52, 0.54), roughness=0.82)
    floor = cube("Impact lab floor", (0, 0, -0.10), (6.6, 5.5, 0.20), ink)
    cylinder("Banner mast", (-2.14, 0, 1.33), 0.055, 2.30, gold,
             vertices=24)
    source_flag = banner_mesh(fabric if variant == 2 else grey, cloth_group)
    if variant == 2:
        # The pole is a simple separate collider, away from the pin column.
        mast = bpy.data.objects["Banner mast"]
        bpy.context.view_layer.objects.active = mast
        bpy.ops.object.select_all(action="DESELECT")
        mast.select_set(True)
        bpy.ops.object.modifier_add(type="COLLISION")
        banner = bake_banner(source_flag, cloth_group, 20)
    else:
        source_flag.name = "SM_Baked_Wind_Banner"
        banner = source_flag
    plate = cube("SM_Conductive_Impact_Plate", (1.37, 0, 0.12),
                 (2.15, 2.4, 0.24), gold if variant == 2 else grey, edge=0.06)
    move_to(plate, physical_group)
    if variant == 2:
        orb, impact = impact_orb(metal, plate, physical_group)
    else:
        orb = sphere("SM_Baked_Impact_Orb", (1.37, 0, 2.28), 0.25,
                     grey, segments=24, rings=12)
        move_to(orb, physical_group)
        impact = 18
    energy_ribbons(fx_group, impact, complete=variant == 2)
    title = material("MAT_Label_Ink", (0.02, 0.10, 0.12), roughness=1)
    label("PINNED CLOTH", (-1.30, -1.47, 0.08), title)
    label("RIGID IMPACT + FX", (1.37, -1.47, 0.08), title)
    cam = camera("Banner impact camera", (0, -6.9, 2.45),
                 (0, 0, 1.27), ortho=5.8)
    area_light("Impact warm key", (-3.2, -3.8, 4.7), 950, 3.2,
               color=(1.0, 0.72, 0.45), target=(-1.2, 0, 1.2))
    area_light("Impact cool fill", (3.0, -3.0, 4.3), 800, 3.2,
               color=(0.42, 0.83, 1.0), target=(1.5, 0, 1.0))
    area_light("Upper rim", (0, 2.0, 4.4), 650, 2.8,
               target=(0, 0, 1.3))
    scene.frame_set(1)
    return scene
