"""Audit the insectoid silhouette, rigid-shell weights, FK hierarchy, and poses."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing beetle object: {name}")
    return obj


def fully_bound(obj, arm):
    modifiers = [mod for mod in obj.modifiers if mod.type == "ARMATURE"]
    if len(modifiers) != 1 or modifiers[0].object != arm:
        return False
    if len(obj.vertex_groups) != 1 or obj.vertex_groups[0].name not in arm.data.bones:
        return False
    index = obj.vertex_groups[0].index
    return all(any(member.group == index and abs(member.weight - 1) < 0.0001
                   for member in vert.groups) for vert in obj.data.vertices)


def audit():
    scene = bpy.context.scene
    variant = scene.get("beetle_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown beetle variant")
    arm = required("ARM_Reed_Beetle")
    group = bpy.data.collections.get("COL_Creature_Reed_Beetle")
    rig_group = bpy.data.collections.get("COL_Rig_Reed_Beetle")
    stage = bpy.data.collections.get("COL_Stage_Reed_Beetle")
    if not all((group, rig_group, stage)):
        raise ValueError("Missing creature, rig, or stage collection")
    creature_meshes = [obj for obj in group.objects if obj.type == "MESH"]
    bones = {bone.name: bone for bone in arm.data.bones}
    wing_names = [f"{side}_elytron" for side in ("L", "R")]
    leg_names = [f"{side}_leg_{index}_{part}"
                 for side in ("L", "R") for index in range(3)
                 for part in ("upper", "lower")]
    required_bones = {"root", "thorax", "head", "abdomen", *wing_names,
                      *leg_names}
    checks = {
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "metric_stage": (scene.unit_settings.system == "METRIC" and
                         required("Beetle specimen pedestal").name in stage.objects),
        "named_armature": arm.type == "ARMATURE" and arm.name in rig_group.objects,
        "bone_set": set(bones) == required_bones,
        "bone_hierarchy": (bones["thorax"].parent.name == "root" and
                           all(bones[name].parent.name == "thorax"
                               for name in wing_names) and
                           all(bones[f"{side}_leg_{index}_upper"].parent.name
                               == "thorax" and
                               bones[f"{side}_leg_{index}_lower"].parent.name
                               == f"{side}_leg_{index}_upper"
                               for side in ("L", "R") for index in range(3))),
        "insect_anatomy": all(required(name).name in group.objects for name in
                              ("SM_Beetle_Abdomen", "SM_Beetle_Thorax",
                               "SM_Beetle_Head", "SM_Beetle_L_Eye",
                               "SM_Beetle_R_Eye", "SM_Beetle_L_Antenna",
                               "SM_Beetle_R_Antenna", "SM_Beetle_L_Elytron",
                               "SM_Beetle_R_Elytron")),
        "six_jointed_legs": all(required(f"SM_Beetle_{side}_Leg_{index}_{part}").name
                                  in group.objects for side in ("L", "R")
                                  for index in range(3)
                                  for part in ("Upper", "Lower")),
        "rigid_weights": all(fully_bound(obj, arm) for obj in creature_meshes),
        "wing_shells": all(any(mod.type == "SOLIDIFY" for mod in
                               required(f"SM_Beetle_{side}_Elytron").modifiers)
                           for side in ("L", "R")),
        "camera": scene.camera == required("Beetle three-quarter camera") and
                  scene.camera.data.type == "ORTHO",
    }
    angles = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        angles[frame] = [round(arm.pose.bones[name].rotation_euler.x, 3)
                         for name in wing_names]
    if variant == 2:
        checks["fk_pose_keys"] = (arm.animation_data is not None and
                                  arm.animation_data.action is not None and
                                  arm.get("rig_type") == "rigid_exoskeleton_fk")
        checks["symmetric_wing_reveal"] = (angles[1] == [0, 0] and
                                           angles[36] == [0.62, 0.62] and
                                           angles[72] == [0, 0])
        scene.frame_set(36)
        checks["leg_motion"] = any(abs(arm.pose.bones[name].rotation_euler.x)
                                   > 0.01 for name in leg_names)
        checks["finished_palette"] = all(bpy.data.materials.get(name) for name in
                                         ("MAT_Beetle_AmberShell",
                                          "MAT_Beetle_JadeThorax",
                                          "MAT_Beetle_GlassEye"))
    else:
        checks["static_blockout"] = (not arm.animation_data and
                                     angles[1] == angles[36] == angles[72])
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Beetle rig audit failed: " + ", ".join(failed))
    return {"variant": variant, "checks": checks, "bone_count": len(bones),
            "rigged_mesh_count": len(creature_meshes), "wing_angles": angles}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    result = audit()
    output = args.out.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Audited beetle variant {result['variant']} with {len(result['checks'])} checks")


if __name__ == "__main__":
    main()
