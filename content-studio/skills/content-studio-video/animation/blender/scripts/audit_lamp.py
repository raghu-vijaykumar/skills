"""Audit the desk-lamp benchmark's editable modeling and prop structure."""

import argparse
import json
from pathlib import Path
import sys

import bmesh
import bpy


def audit():
    scene = bpy.context.scene
    blockout = bpy.data.collections.get("COL_Blockout")
    geometry = bpy.data.collections.get("COL_Geo")
    if not blockout or not geometry:
        raise ValueError("Lamp needs separate blockout and final geometry collections")
    proxy = bpy.data.objects.get("SM_Lamp_Blockout")
    if not proxy or proxy.name not in blockout.objects or not proxy.hide_render:
        raise ValueError("Preserved scale blockout must stay outside final renders")
    meshes = [obj for obj in geometry.objects if obj.type == "MESH"]
    if len(meshes) < 10 or any(not obj.name.startswith("SM_") for obj in meshes):
        raise ValueError("Final prop needs named, separately editable mesh parts")
    if any(any(abs(scale - 1) > 1e-5 for scale in obj.scale) for obj in meshes):
        raise ValueError("Final mesh scale must be applied before handoff")
    if scene.unit_settings.system != "METRIC" or scene.unit_settings.scale_length != 1:
        raise ValueError("Prop must retain meter scale")
    base = bpy.data.objects["SM_Lamp_Base"]
    if not 0.34 <= base.dimensions.x <= 0.38:
        raise ValueError("Lamp base must remain a plausible 0.36 m tabletop diameter")
    pivot = bpy.data.objects["Lamp head pivot"]
    moving = ("SM_Lamp_Upper_Arm", "SM_Lamp_Shade", "SM_Lamp_Diffuser", "Lamp task light")
    if any(bpy.data.objects[name].parent != pivot for name in moving):
        raise ValueError("Upper assembly must follow its editable head pivot")
    if not pivot.animation_data or not pivot.animation_data.action:
        raise ValueError("Adjustable head has no keyframed pose")
    for name in ("SM_Lamp_Base", "SM_Lamp_Shade"):
        if not any(mod.type == "BEVEL" and mod.show_render for mod in bpy.data.objects[name].modifiers):
            raise ValueError(f"Non-destructive edge refinement is missing from {name}")
    # Evaluate the unmodified meshes so cleanup is visible before export adapters run.
    open_edges = {}
    triangles = 0
    for obj in meshes:
        mesh = bmesh.new()
        mesh.from_mesh(obj.data)
        bad = sum(not edge.is_manifold for edge in mesh.edges)
        if bad:
            open_edges[obj.name] = bad
        triangles += sum(len(face.verts) - 2 for face in mesh.faces)
        mesh.free()
    if open_edges:
        raise ValueError(f"Final prop has open or non-manifold edges: {open_edges}")
    return {"collections": [blockout.name, geometry.name], "final_meshes": len(meshes),
            "source_triangles": triangles, "manifold": True,
            "base_diameter_m": round(base.dimensions.x, 4),
            "moving_parts": list(moving), "blockout_preserved": True,
            "non_destructive_bevel": ["SM_Lamp_Base", "SM_Lamp_Shade"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Audited {report['final_meshes']} manifold mesh parts and preserved blockout")


if __name__ == "__main__":
    main()
