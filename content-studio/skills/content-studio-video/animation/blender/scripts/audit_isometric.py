"""Audit the locked true-iso camera, tile kit, and readable lamp motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


TILE_M = 0.8


def audit():
    scene = bpy.context.scene
    kit = bpy.data.collections.get("COL_Iso_One_Tile_Kit")
    tile = bpy.data.objects.get("SM_Iso_Tile")
    top = bpy.data.objects.get("SM_Iso_Tile_Top")
    cam = bpy.data.objects.get("CAM_Iso_Lamp")
    pivot = bpy.data.objects.get("Iso lamp pivot")
    if not kit or not tile or not top or not cam or not pivot:
        raise ValueError("Isometric tile kit is incomplete")
    if (abs(tile.get("tile_size_m", 0) - TILE_M) > 1e-6 or
            list(tile.get("footprint_cells", [])) != [1, 1] or
            tile.get("pivot_rule") != "center" or
            any(abs(value - TILE_M) > 1e-6 for value in tile.dimensions[:2])):
        raise ValueError("Tile footprint or center-pivot rule changed")
    if tile.data.materials[0] == top.data.materials[0]:
        raise ValueError("Tile top and edge need visible material contrast")
    if (cam.data.type != "ORTHO" or cam.animation_data or
            not cam.get("locked_for_kit") or
            abs(cam.get("tile_size_m", 0) - TILE_M) > 1e-6):
        raise ValueError("The orthographic camera must be locked for the kit")
    forward = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    # Equal absolute direction components are the true-iso axis condition.
    if max(abs(value) for value in forward) - min(abs(value) for value in forward) > 1e-4:
        raise ValueError("Camera is not at the true-isometric axis angle")
    if not pivot.animation_data or not pivot.animation_data.action:
        raise ValueError("Lamp pivot has no animated action")
    poses = []
    for frame in (1, 38, 72):
        scene.frame_set(frame)
        poses.append(pivot.rotation_euler.y)
    if max(poses) - min(poses) < 0.35:
        raise ValueError("Lamp movement is too small for the isometric view")
    required = {"SM_Iso_Lamp_Base", "SM_Iso_Lamp_Shade", "SM_Iso_Notebook"}
    if any(name not in kit.objects for name in required):
        raise ValueError("The tile lacks a readable lamp or notebook")
    return {"tile_size_m": TILE_M, "footprint_cells": [1, 1],
            "pivot_rule": "center", "camera_type": cam.data.type,
            "camera_locked": True, "true_iso_direction": list(forward),
            "tile_edge_contrast": True, "pivot_rotation_range_rad": max(poses) - min(poses),
            "review_frames": [1, 38, 72]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Audited locked 1x1 true-iso tile and animated lamp")


if __name__ == "__main__":
    main()
