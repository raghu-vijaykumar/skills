"""Audit the guardian's sculpt, static retopo cage, and hair-card groom."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing guardian object: {name}")
    return obj


def evaluated_faces(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return len(mesh.polygons)
    finally:
        evaluated.to_mesh_clear()


def audit():
    scene = bpy.context.scene
    variant = scene.get("guardian_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown guardian variant")
    high = required("SM_Guardian_High_Sculpt")
    low = required("SM_Guardian_Low_Retopo")
    base = required("SM_Guardian_Clean_Base")
    reference = required("SM_Guardian_High_Reference")
    cards = [obj for obj in bpy.data.objects if obj.name.startswith("SM_HairCard_Guardian_")]
    quad_ratio = sum(len(face.vertices) == 4 for face in low.data.polygons) / len(low.data.polygons)
    checks = {
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "metric_stage": scene.unit_settings.system == "METRIC" and
                        all(bpy.data.objects.get(name) for name in
                            ("Guardian sculpt pedestal", "Guardian retopo pedestal")),
        "clean_base": base.hide_render and base.get("before_surface_sculpt") is True,
        "hidden_high_reference": reference.hide_render and reference.type == "MESH",
        "named_forms": high.type == low.type == "MESH" and
                       high.name in bpy.data.collections["COL_Guardian_High"].objects and
                       low.name in bpy.data.collections["COL_Guardian_Low"].objects,
        "camera": scene.camera == required("Guardian craft comparison camera") and
                  scene.camera.data.type == "ORTHO",
    }
    if variant == 2:
        multires = [mod for mod in high.modifiers if mod.type == "MULTIRES"]
        pores = [mod for mod in high.modifiers if mod.type == "DISPLACE"]
        wrap = [mod for mod in low.modifiers if mod.type == "SHRINKWRAP"]
        cage = required("SM_Guardian_Retopo_Cage_Display")
        atlas = bpy.data.images.get("T_Hair_Guardian_RGBA")
        hair_mat = bpy.data.materials.get("MAT_Guardian_HairCards")
        checks.update({
            "editable_multires": len(multires) == 1 and multires[0].total_levels == 2,
            "small_pore_displacement": len(pores) == 1 and
                                       abs(pores[0].strength - 0.025) < 0.0001 and
                                       pores[0].texture.type == "CLOUDS",
            "sculpt_density": evaluated_faces(high) > 8 * evaluated_faces(low),
            "static_quad_cage": quad_ratio >= 0.85 and len(low.data.polygons) <= 500,
            "shrinkwrap_reference": len(wrap) == 1 and wrap[0].target == reference and
                                    abs(wrap[0].offset - 0.012) < 0.0001,
            "visible_cage": any(mod.type == "WIREFRAME" for mod in cage.modifiers),
            "packed_rgba_atlas": atlas is not None and tuple(atlas.size) == (256, 256) and
                                 bool(atlas.packed_file) and atlas.channels == 4 and
                                 atlas.pixels[(128 * 256 + 32) * 4 + 3] > 0.9 and
                                 atlas.pixels[(128 * 256 + 0) * 4 + 3] < 0.1,
            "atlas_alpha_material": hair_mat is not None and
                                    hair_mat.surface_render_method == "DITHERED" and
                                    any(node.type == "TEX_IMAGE" and node.image == atlas
                                        for node in hair_mat.node_tree.nodes),
            "scalp_cap": required("SM_Guardian_ScalpCap").type == "MESH",
            "tapered_uv_cards": len(cards) == 32 and all(
                len(obj.data.polygons) == 4 and len(obj.data.vertices) == 10 and
                (obj.data.vertices[9].co - obj.data.vertices[8].co).length <
                0.3 * (obj.data.vertices[1].co - obj.data.vertices[0].co).length and
                obj.data.uv_layers.active is not None and
                all(0 <= uv.uv.x <= 1 and 0 <= uv.uv.y <= 1
                    for uv in obj.data.uv_layers.active.data) and
                obj.get("flow_region") == "forehead-to-temple fan"
                for obj in cards),
            "hair_breeze": len(cards) == 32 and all(
                obj.data.shape_keys is not None and
                obj.data.shape_keys.key_blocks.get("Breeze") is not None and
                obj.data.shape_keys.animation_data is not None
                for obj in cards),
            "camera_push": scene.camera.animation_data is not None,
        })
        for frame, expected in ((1, 0), (36, 1), (72, 0)):
            scene.frame_set(frame)
            checks[f"breeze_frame_{frame}"] = all(
                abs(obj.data.shape_keys.key_blocks["Breeze"].value - expected) < 0.001
                for obj in cards)
    else:
        checks["static_blockout"] = (not high.modifiers and not low.modifiers and
                                     not cards and scene.camera.animation_data is None)
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Guardian craft audit failed: " + ", ".join(failed))
    return {"variant": variant, "checks": checks,
            "high_evaluated_faces": evaluated_faces(high),
            "low_evaluated_faces": evaluated_faces(low),
            "low_quad_ratio": round(quad_ratio, 3), "hair_card_count": len(cards)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Audited guardian variant {report['variant']} with {len(report['checks'])} checks")


if __name__ == "__main__":
    main()
