"""Original insectoid creature with a functional rigid-shell FK armature."""

import math
from pathlib import Path

import bpy
from mathutils import Vector

from common import area_light, camera, cube, material, reset_scene, sphere


def collection(name):
    group = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(group)
    return group


def move_to(obj, group):
    for old in tuple(obj.users_collection):
        old.objects.unlink(obj)
    group.objects.link(obj)
    return obj


def limb_segment(name, start, end, radius, mat):
    a, b = Vector(start), Vector(end)
    middle = (a + b) / 2
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=radius * 0.68,
                                    radius2=radius, depth=(b - a).length,
                                    location=middle)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    return obj


def wing_cover(name, side, mat):
    # A broad, low-density shell reads as an elytron from the gameplay-height camera.
    points = [(0.16, side * 0.12, 0.93), (-0.11, side * 0.16, 1.00),
              (-0.56, side * 0.24, 0.98), (-0.83, side * 0.28, 0.87),
              (-0.69, side * 0.47, 0.83), (-0.35, side * 0.52, 0.88),
              (0.06, side * 0.38, 0.91)]
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(points, [], [(0, 1, 2, 3, 4, 5, 6)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    solid = obj.modifiers.new("Elytron shell thickness", "SOLIDIFY")
    solid.thickness = 0.035
    bevel = obj.modifiers.new("Rounded shell edge", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 2
    obj.modifiers.new("Weighted shell normals", "WEIGHTED_NORMAL")
    return obj


def bone(edit, name, head, tail, parent=None):
    item = edit.new(name)
    item.head, item.tail = head, tail
    if parent:
        item.parent = edit[parent]
        item.use_connect = False
    return item


def armature(group):
    data = bpy.data.armatures.new("Reed beetle FK skeleton")
    arm = bpy.data.objects.new("ARM_Reed_Beetle", data)
    group.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    edit = data.edit_bones
    bone(edit, "root", (0, 0, 0.07), (0, 0, 0.72))
    bone(edit, "thorax", (0, 0, 0.72), (0.24, 0, 0.78), "root")
    bone(edit, "head", (0.24, 0, 0.78), (0.66, 0, 0.80), "thorax")
    bone(edit, "abdomen", (0, 0, 0.72), (-0.48, 0, 0.72), "thorax")
    for side, sign in (("L", 1), ("R", -1)):
        bone(edit, f"{side}_elytron", (0.09, sign * 0.13, 0.91),
             (-0.39, sign * 0.37, 0.93), "thorax")
        for index, x in enumerate((-0.38, -0.02, 0.34)):
            hip = (x, sign * 0.25, 0.63)
            knee = (x + (0.09 if index == 2 else -0.08), sign * 0.52, 0.38)
            foot = (x + (0.16 if index == 2 else -0.15), sign * 0.70, 0.025)
            upper = f"{side}_leg_{index}_upper"
            bone(edit, upper, hip, knee, "thorax")
            bone(edit, f"{side}_leg_{index}_lower", knee, foot, upper)
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.show_in_front = True
    arm.hide_render = True
    for pose in arm.pose.bones:
        pose.rotation_mode = "XYZ"
    return arm


def bind(obj, arm, bone_name, group):
    # Rigid weights are appropriate to an arthropod exoskeleton, and keep every
    # segment attached to an inspectable named bone instead of an object pivot.
    group_weight = obj.vertex_groups.new(name=bone_name)
    group_weight.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    mod = obj.modifiers.new("Beetle rigid shell armature", "ARMATURE")
    mod.object = arm
    move_to(obj, group)
    return obj


def make_scene(spec, spec_dir: Path):
    variant = int(spec.get("variant", 2))
    if variant not in (1, 2):
        raise ValueError("Unknown beetle candidate")
    scene = reset_scene(spec, background=(0.015, 0.045, 0.060))
    scene.unit_settings.system = "METRIC"
    scene["beetle_variant"] = variant
    rig_group = collection("COL_Rig_Reed_Beetle")
    creature = collection("COL_Creature_Reed_Beetle")
    stage = collection("COL_Stage_Reed_Beetle")
    amber = material("MAT_Beetle_AmberShell", (0.48, 0.17, 0.055),
                     metallic=0.24, roughness=0.27)
    jade = material("MAT_Beetle_JadeThorax", (0.04, 0.40, 0.26),
                    metallic=0.21, roughness=0.35)
    dark = material("MAT_Beetle_DarkJoint", (0.018, 0.045, 0.042), roughness=0.60)
    eye = material("MAT_Beetle_GlassEye", (0.014, 0.050, 0.082),
                   metallic=0.15, roughness=0.12)
    if variant == 1:
        amber = jade = material("MAT_Beetle_Greyblock", (0.46, 0.52, 0.55),
                                roughness=0.9)
    arm = armature(rig_group)
    bind(sphere("SM_Beetle_Abdomen", (-0.36, 0, 0.74), 0.43, amber,
                segments=24, rings=12, scale=(1.34, 0.85, 0.63)),
         arm, "abdomen", creature)
    bind(sphere("SM_Beetle_Thorax", (0.21, 0, 0.77), 0.28, jade,
                segments=24, rings=12, scale=(1.1, 0.85, 0.92)),
         arm, "thorax", creature)
    bind(sphere("SM_Beetle_Head", (0.60, 0, 0.78), 0.22, jade,
                segments=24, rings=12, scale=(1.06, 0.92, 0.86)),
         arm, "head", creature)
    for side, sign in (("L", 1), ("R", -1)):
        bind(wing_cover(f"SM_Beetle_{side}_Elytron", sign, amber),
             arm, f"{side}_elytron", creature)
        bind(sphere(f"SM_Beetle_{side}_Eye", (0.71, sign * 0.145, 0.83),
                    0.09, eye, segments=16, rings=8, scale=(1, 0.65, 0.88)),
             arm, "head", creature)
        bind(limb_segment(f"SM_Beetle_{side}_Antenna", (0.74, sign * 0.08, 0.89),
                          (0.99, sign * 0.22, 1.11), 0.025, dark),
             arm, "head", creature)
        for index, x in enumerate((-0.38, -0.02, 0.34)):
            hip = (x, sign * 0.25, 0.63)
            knee = (x + (0.09 if index == 2 else -0.08), sign * 0.52, 0.38)
            foot = (x + (0.16 if index == 2 else -0.15), sign * 0.70, 0.025)
            upper = f"{side}_leg_{index}_upper"
            lower = f"{side}_leg_{index}_lower"
            bind(limb_segment(f"SM_Beetle_{side}_Leg_{index}_Upper", hip, knee,
                              0.048, dark), arm, upper, creature)
            bind(limb_segment(f"SM_Beetle_{side}_Leg_{index}_Lower", knee, foot,
                              0.032, dark), arm, lower, creature)
            bind(sphere(f"Beetle {side} knee {index}", knee, 0.062, amber,
                        segments=12, rings=6), arm, upper, creature)
    slate = material("MAT_Beetle_Stage", (0.09, 0.16, 0.18), roughness=0.83)
    rim = material("MAT_Beetle_Rim", (0.16, 0.31, 0.29), metallic=0.38,
                   roughness=0.42)
    move_to(cube("Beetle specimen pedestal", (0, 0, -0.09),
                 (2.8, 2.1, 0.18), slate, edge=0.09), stage)
    move_to(cube("Beetle pedestal rim", (0, 0, -0.18),
                 (3.04, 2.32, 0.10), rim, edge=0.04), stage)
    move_to(cube("Beetle background", (0, 0, -0.33),
                 (12, 12, 0.12), slate), stage)
    camera("Beetle three-quarter camera", (2.55, -4.3, 2.55),
           (0, 0, 0.63), ortho=3.5)
    area_light("Beetle soft key", (0.4, -2.4, 3.6), 750, 2.4,
               target=(0, 0, 0.72))
    area_light("Beetle amber rim", (-1.7, 1.5, 2.5), 580, 1.8,
               color=(1.0, 0.59, 0.29), target=(-0.2, 0, 0.68))
    area_light("Beetle cyan fill", (1.9, 1.2, 1.8), 330, 2.2,
               color=(0.36, 0.91, 0.83), target=(0, 0, 0.8))
    if variant == 2:
        # FK wing and leg keys expose a real joint hierarchy while the shell
        # weights stay rigid; the phase offset suggests a six-legged gait.
        poses = ((1, 0.00, 0.0), (18, 0.12, 0.12),
                 (36, 0.62, -0.18), (54, 0.32, 0.18), (72, 0.0, 0.0))
        for frame, wing_angle, gait in poses:
            for side, sign in (("L", 1), ("R", -1)):
                cover = arm.pose.bones[f"{side}_elytron"]
                cover.rotation_euler.x = wing_angle
                cover.keyframe_insert(data_path="rotation_euler", frame=frame)
                for index in range(3):
                    phase = -1 if (index + (0 if side == "L" else 1)) % 2 else 1
                    upper = arm.pose.bones[f"{side}_leg_{index}_upper"]
                    lower = arm.pose.bones[f"{side}_leg_{index}_lower"]
                    upper.rotation_euler.x = phase * gait
                    lower.rotation_euler.x = -phase * gait * 0.55
                    upper.keyframe_insert(data_path="rotation_euler", frame=frame)
                    lower.keyframe_insert(data_path="rotation_euler", frame=frame)
            head = arm.pose.bones["head"]
            head.rotation_euler.z = 0.05 * math.sin(frame * 0.08)
            head.keyframe_insert(data_path="rotation_euler", frame=frame)
        arm["rig_type"] = "rigid_exoskeleton_fk"
        arm["rig_test_frames"] = [1, 36, 72]
    return scene
