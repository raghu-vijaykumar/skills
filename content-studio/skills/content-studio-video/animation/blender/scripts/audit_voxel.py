"""Verify that the voxel treatment uses grid geometry and stepped grid motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


VOXEL_M = 0.05


def on_grid(value, spacing):
    return abs(value / spacing - round(value / spacing)) < 1e-5


def audit():
    collection = bpy.data.collections.get("COL_Voxel_Prop")
    if not collection:
        raise ValueError("Voxel collection is missing")
    meshes = [obj for obj in collection.objects if obj.type == "MESH"]
    if len(meshes) < 7:
        raise ValueError("Voxel prop is missing its separate block components")
    cells = 0
    for obj in meshes:
        if obj.get("voxel_size_m") != VOXEL_M or obj.get("occupied_cells", 0) < 1:
            raise ValueError(f"Missing declared occupancy grid for {obj.name}")
        cells += obj["occupied_cells"]
        if any(not on_grid(value, VOXEL_M / 2) for vertex in obj.data.vertices
               for value in vertex.co):
            raise ValueError(f"Off-grid voxel vertex in {obj.name}")
        if any(poly.use_smooth or max(abs(axis) for axis in poly.normal) < 0.999
               for poly in obj.data.polygons):
            raise ValueError(f"Rounded or smoothed voxel face in {obj.name}")
        if obj.modifiers:
            raise ValueError(f"Voxel mesh has modifiers: {obj.name}")
    palette = {mat.name for obj in meshes for mat in obj.data.materials if mat}
    if len(palette) > 5:
        raise ValueError("Voxel prop exceeds its five-color palette")
    pivot = bpy.data.objects.get("Voxel head control")
    if not pivot or not pivot.animation_data or not pivot.animation_data.action:
        raise ValueError("Voxel head control needs stepped animation")
    scene = bpy.context.scene
    positions = []
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        position = tuple(round(value, 5) for value in pivot.location)
        if any(not on_grid(value, VOXEL_M) for value in position):
            raise ValueError(f"Voxel head leaves the occupancy grid at frame {frame}")
        positions.append(position)
    if len(set(positions)) < 3:
        raise ValueError("Voxel head did not complete two readable grid steps")
    return {"voxel_size_m": VOXEL_M, "prop_meshes": len(meshes),
            "occupied_cells": cells, "palette_materials": len(palette),
            "axis_aligned_flat_faces": True, "head_grid_positions": len(set(positions)),
            "source_frames_checked": len(positions)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Audited {report['occupied_cells']} cells across {report['source_frames_checked']} frames")


if __name__ == "__main__":
    main()
