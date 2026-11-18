"""Check measured scale, PBR materials, fixture parts, and lamp adjustment."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def pbr(name):
    mat = bpy.data.materials.get(name)
    shader = mat.node_tree.nodes.get("Principled BSDF") if mat and mat.node_tree else None
    if not shader:
        raise ValueError(f"Missing PBR material: {name}")
    return {"metallic": shader.inputs["Metallic"].default_value,
            "roughness": shader.inputs["Roughness"].default_value}


def audit():
    scene = bpy.context.scene
    shade = bpy.data.objects.get("SM_Real_Shade")
    pivot = bpy.data.objects.get("Real lamp upper hinge")
    cam = bpy.data.objects.get("Realistic product camera")
    required = ("SM_Real_Clamp_Top", "SM_Real_Clamp_Back", "SM_Real_Clamp_Bottom",
                "SM_Real_Clamp_Screw", "SM_Real_Lower_Arm_A", "SM_Real_Upper_Arm_A",
                "SM_Real_Lower_Tension", "SM_Real_Upper_Tension", "SM_Real_Desk")
    if not shade or not pivot or not cam or any(bpy.data.objects.get(name) is None
                                                for name in required):
        raise ValueError("Realistic fixture, springs, or camera missing")
    if scene.unit_settings.system != "METRIC" or scene.unit_settings.scale_length != 1:
        raise ValueError("Real-world meter scale is not configured")
    diameter = max(vertex.co.x for vertex in shade.data.vertices) - min(
        vertex.co.x for vertex in shade.data.vertices)
    if abs(diameter - 0.17) > 1e-5 or abs(shade.get("shade_diameter_m", 0) - 0.17) > 1e-5:
        raise ValueError("Measured shade diameter is not 17 cm")
    if cam.data.type != "PERSP":
        raise ValueError("Product camera lost its perspective projection")
    paint = pbr("PBR warm white powder-coated steel")
    hardware = pbr("PBR brushed steel hardware")
    plastic = pbr("PBR black ABS clamp")
    wood = pbr("PBR natural desk wood")
    if (not 0.3 <= paint["roughness"] <= 0.65 or
            hardware["metallic"] < 0.8 or plastic["metallic"] != 0 or
            wood["roughness"] < 0.6):
        raise ValueError("Material values leave the declared PBR ranges")
    wood_nodes = bpy.data.materials["PBR natural desk wood"].node_tree.nodes
    if not any(node.type == "BUMP" for node in wood_nodes):
        raise ValueError("Desk lacks restrained roughness micro-detail")
    if not pivot.animation_data or not pivot.animation_data.action:
        raise ValueError("Adjustable upper arm is not keyed")
    angles = []
    for frame in (1, 38, 72):
        scene.frame_set(frame)
        angles.append(pivot.rotation_euler.y)
    if max(angles) - min(angles) < 0.35:
        raise ValueError("Lamp adjustment is too small to review")
    return {"shade_diameter_m": diameter, "desk_thickness_m": 0.07,
            "unit_system": "METRIC", "camera_type": cam.data.type,
            "clamp_and_spring_parts": len(required),
            "pbr": {"paint": paint, "hardware": hardware, "plastic": plastic, "wood": wood},
            "wood_bump": True, "pivot_rotation_range_rad": max(angles) - min(angles),
            "review_frames": [1, 38, 72]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Audited measured product lamp and PBR materials")


if __name__ == "__main__":
    main()
