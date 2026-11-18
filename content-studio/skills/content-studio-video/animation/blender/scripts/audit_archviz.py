"""Audit measured room, window opening, practical lighting, and walkthrough."""

import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing archviz object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("archviz_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown archviz candidate")
    groups = {name: bpy.data.collections.get(name)
              for name in ("COL_Architecture", "COL_Furniture", "COL_Lighting", "COL_Context")}
    if any(group is None for group in groups.values()):
        raise ValueError("Architecture, furniture, lighting, and context must remain separate")
    floor = required("SM_Studio_Floor")
    left = required("SM_Left_Wall")
    right = required("SM_Right_Wall")
    sill = required("SM_Window_Sill")
    header = required("SM_Window_Header")
    window_left = required("SM_Window_Wall_Left")
    window_right = required("SM_Window_Wall_Right")
    sofa = required("SM_Sofa_Base")
    table = required("SM_Coffee_Table_Top")
    sky = required("SM_Window_Exterior_Sky")
    key = required("LGT_Window_Daylight")
    practical = required("LGT_Pendant_Practical")
    cam = required("Archviz eye-level camera")
    checks = {
        "metric_room": (scene.unit_settings.system == "METRIC" and
                        scene.unit_settings.scale_length == 1 and
                        list(scene["archviz_room_m"]) == [5.6, 5.6, 3.0] and
                        max(abs(floor.dimensions[i] - [5.6, 5.6, 0.12][i])
                            for i in range(3)) < 0.001 and
                        left.dimensions.z == right.dimensions.z == 3.0),
        "window_opening": (list(scene["archviz_window_m"]) == [2.10, 1.40] and
                           abs(sill.location.z + sill.dimensions.z / 2 - 0.96) < 0.001 and
                           abs(header.location.z - header.dimensions.z / 2 - 2.36) < 0.001 and
                           abs((window_right.location.x - window_right.dimensions.x / 2) -
                               (window_left.location.x + window_left.dimensions.x / 2) -
                               2.10) < 0.001 and
                           sky.dimensions.x >= 2.10),
        "organization": (floor.name in groups["COL_Architecture"].objects and
                         sofa.name in groups["COL_Furniture"].objects and
                         key.name in groups["COL_Lighting"].objects and
                         cam.name in groups["COL_Context"].objects),
        "furnishing": (sofa.dimensions.x > 2.2 and table.dimensions.x > 1.3 and
                       required("SM_Shelf_1.00").type == "MESH" and
                       required("SM_Pendant_Shade").type == "MESH"),
        "camera": (cam.type == "CAMERA" and cam.data.type == "PERSP" and
                   cam.data.lens == 30 and scene.camera == cam),
        "light": (key.type == practical.type == "LIGHT" and
                  key.data.color.b > key.data.color.r and
                  practical.data.color.r > practical.data.color.b),
        "delivery": ((scene.render.resolution_x, scene.render.resolution_y,
                      scene.render.fps, scene.frame_end) == (960, 540, 24, 72) and
                     scene.view_settings.view_transform == "AgX"),
    }
    if variant == 2:
        checks["finished_craft"] = (required("SM_Sofa_Back_Cushion_-1.63").type == "MESH" and
                                     required("SM_Wall_Art_Field").type == "MESH" and
                                     required("SM_Exterior_Building_Left").type == "MESH" and
                                     key.data.energy == 570 and practical.data.energy == 185 and
                                     bpy.data.materials["MAT_Brushed_Brass"].node_tree.nodes[
                                         "Principled BSDF"].inputs["Metallic"].default_value > 0.7)
    else:
        checks["greybox"] = (bpy.data.objects.get("SM_Sofa_Back_Cushion_-1.63") is None and
                              practical.data.energy == 0 and not cam.animation_data)
    poses = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
        poses[frame] = {"camera_xyz_m": [round(value, 3) for value in cam.location],
                        "vertical_alignment": round(up.z, 5)}
    checks["straight_verticals"] = all(item["vertical_alignment"] > 0.995
                                       for item in poses.values())
    if variant == 2:
        checks["inspection_push"] = (poses[72]["camera_xyz_m"][0] -
                                      poses[1]["camera_xyz_m"][0] >= 0.99 and
                                      poses[72]["camera_xyz_m"][1] -
                                      poses[1]["camera_xyz_m"][1] >= 0.59)
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Archviz invariants failed: " + ", ".join(failed))
    return {"variant": variant, "checks": checks, "poses": poses,
            "collection_sizes": {name: len(group.objects) for name, group in groups.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    blend, output = args.blend.resolve(strict=True), args.out.resolve()
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    result = audit()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Audited measured archviz variant {result['variant']} with {len(result['checks'])} checks")


if __name__ == "__main__":
    main()
