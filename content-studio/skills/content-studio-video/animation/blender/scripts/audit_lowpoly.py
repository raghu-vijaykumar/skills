"""Verify a low-poly scene has genuinely faceted geometry and a bounded prop budget."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def audit():
    collection = bpy.data.collections.get("COL_Lowpoly_Prop")
    if collection is None:
        raise ValueError("Low-poly prop collection is missing")
    meshes = [obj for obj in collection.objects if obj.type == "MESH"]
    if len(meshes) < 6:
        raise ValueError("Low-poly silhouette needs independently editable parts")
    triangles = sum(sum(len(face.vertices) - 2 for face in obj.data.polygons) for obj in meshes)
    if not 50 <= triangles <= 500:
        raise ValueError(f"Low-poly prop exceeds its 50–500 triangle tier: {triangles}")
    if any(face.use_smooth for obj in meshes for face in obj.data.polygons):
        raise ValueError("Faceted surfaces must remain flat shaded")
    forbidden = {"SUBSURF", "BEVEL", "WEIGHTED_NORMAL"}
    if any(mod.type in forbidden for obj in meshes for mod in obj.modifiers):
        raise ValueError("Low-poly prop has smoothing or micro-bevel modifiers")
    mats = {mat for obj in meshes for mat in obj.data.materials if mat}
    if len(mats) > 6 or any(node.type == "TEX_IMAGE" for mat in mats
                            if mat.use_nodes for node in mat.node_tree.nodes):
        raise ValueError("Low-poly treatment uses too many or high-detail materials")
    if bpy.context.scene.camera.data.type != "ORTHO":
        raise ValueError("Low-poly showcase needs its tested gameplay-distance camera")
    pivot = bpy.data.objects.get("Lowpoly lamp pivot")
    if not pivot or not pivot.animation_data or not pivot.animation_data.action:
        raise ValueError("Low-poly lamp head must animate")
    return {"prop_triangles": triangles, "prop_meshes": len(meshes),
            "materials": len(mats), "flat_shaded": True,
            "forbidden_modifiers": 0, "camera": "ORTHO", "head_animated": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Audited flat-shaded {report['prop_triangles']}-triangle prop")


if __name__ == "__main__":
    main()
