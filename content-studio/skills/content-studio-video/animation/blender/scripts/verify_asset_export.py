"""Export the audited crate kit and test its hierarchy, materials, and motion."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy

# Blender's --python entry point does not put its script directory on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_game_asset import audit, triangles


TARGETS = {
    "generic": {"format": "GLB", "extension": ".glb"},
    "unity": {"format": "GLB", "extension": ".glb"},
    "unreal": {"format": "FBX", "extension": ".fbx"},
    "godot": {"format": "GLB", "extension": ".glb"},
}
EXPECTED = {f"SM_Crate_Export_LOD{index}": count
            for index, count in enumerate((264, 120, 72, 24))}
EXPECTED["UCX_SM_Crate_Export_01"] = 12
ANIMATED = "SM_Crate_Animated_Export"
ROOT = "ROOT_Crate_Export"
LOD_ROOT = "LODS_Crate_Export"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_hierarchy():
    """Add an export-only clip and shallow node tree without changing the scored shot."""
    scene = bpy.context.scene
    root = bpy.data.objects.new(ROOT, None)
    lod_root = bpy.data.objects.new(LOD_ROOT, None)
    scene.collection.objects.link(root)
    scene.collection.objects.link(lod_root)
    lod_root.parent = root
    for name in EXPECTED:
        bpy.data.objects[name].parent = (root if name.startswith("UCX_")
                                         else lod_root)
    source = bpy.data.objects["SM_Crate_Export_LOD0"]
    animated = bpy.data.objects.new(ANIMATED, source.data.copy())
    scene.collection.objects.link(animated)
    animated.parent = root
    animated["clip_role"] = "roundtrip turn, not gallery motion"
    for frame, angle in ((1, 0.0), (36, 0.38), (72, 0.0)):
        animated.rotation_euler.z = angle
        animated.keyframe_insert(data_path="rotation_euler", frame=frame)
    animated.animation_data.action.name = "AN_Crate_Turn"
    scene.frame_set(1)
    return [root, lod_root, animated]


def export_selected(target, path, helpers):
    bpy.ops.object.select_all(action="DESELECT")
    selected = [*(bpy.data.objects[name] for name in EXPECTED), *helpers]
    for obj in selected:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = selected[0]
    if target == "unreal":
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
                                 apply_unit_scale=True, global_scale=1.0,
                                 axis_forward="-Z", axis_up="Y",
                                 bake_anim=True, bake_anim_use_nla_strips=False,
                                 bake_anim_use_all_actions=False,
                                 use_custom_props=True,
                                 path_mode="COPY", embed_textures=True)
    else:
        bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB",
                                  use_selection=True, export_yup=True,
                                  export_apply=True, export_extras=True,
                                  export_animations=True)
    if not path.is_file() or path.stat().st_size < 1000:
        raise ValueError("Blender did not produce a useful export file")


def roundtrip(target, path, source_dimensions):
    # Reimport into an empty object set so a stale source object cannot satisfy checks.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    if target == "unreal":
        bpy.ops.import_scene.fbx(filepath=str(path))
    else:
        bpy.ops.import_scene.gltf(filepath=str(path))
    objects = {obj.name: obj for obj in bpy.context.scene.objects}
    imported = {name: obj for name, obj in objects.items() if obj.type == "MESH"}
    checks = {"named_meshes": set(EXPECTED).issubset(imported)}
    details = {}
    for name, expected in EXPECTED.items():
        obj = imported.get(name)
        if obj is None:
            continue
        count = triangles(obj)
        dimensions = [round(value, 3) for value in obj.dimensions]
        uv_layers = list(obj.data.uv_layers.keys())
        details[name] = {"triangles": count, "dimensions_m": dimensions,
                         "uv_layers": uv_layers,
                         "materials": [slot.material.name if slot.material else None
                                       for slot in obj.material_slots]}
        checks[f"triangles_{name}"] = count == expected
        checks[f"dimensions_{name}"] = all(abs(value - source) < 0.01
                                           for value, source in zip(dimensions,
                                                                    source_dimensions[name]))
        checks[f"uv_{name}"] = (not uv_layers if name.startswith("UCX_")
                                else len(uv_layers) >= 2)
    root, lod_root = objects.get(ROOT), objects.get(LOD_ROOT)
    animated = imported.get(ANIMATED)
    checks["named_hierarchy"] = bool(root and lod_root and lod_root.parent == root)
    checks["lod_parentage"] = bool(lod_root and all(
        imported.get(f"SM_Crate_Export_LOD{index}") and
        imported[f"SM_Crate_Export_LOD{index}"].parent == lod_root
        for index in range(4)))
    collision = imported.get("UCX_SM_Crate_Export_01")
    checks["collision_separate"] = bool(root and collision and
                                        collision.parent == root and
                                        len(collision.data.uv_layers) == 0 and
                                        triangles(collision) == 12)
    checks["animated_mesh"] = bool(animated and triangles(animated) == 264 and
                                   animated.parent == root)
    checks["animation_clip"] = bool(animated and animated.animation_data and
                                     animated.animation_data.action)
    if animated and animated.animation_data and animated.animation_data.action:
        bpy.context.scene.frame_set(1)
        start = animated.matrix_world.to_euler().z
        bpy.context.scene.frame_set(36)
        peak = animated.matrix_world.to_euler().z
        bpy.context.scene.frame_set(72)
        end = animated.matrix_world.to_euler().z
        checks["animation_motion"] = abs(peak - start) > 0.25 and abs(end - start) < 0.02
        details[ANIMATED] = {"triangles": triangles(animated),
                             "parent": animated.parent.name if animated.parent else None,
                             "clip": animated.animation_data.action.name,
                             "yaw_radians": [round(start, 3), round(peak, 3), round(end, 3)]}
    else:
        checks["animation_motion"] = False
    for name in EXPECTED:
        if name.startswith("UCX_"):
            continue
        obj = imported.get(name)
        if obj is None:
            checks[f"material_{name}"] = False
            continue
        materials = [slot.material for slot in obj.material_slots]
        wood = materials[0] if materials else None
        texture_names = {node.image.name.split(".")[0] for node in
                         wood.node_tree.nodes if node.type == "TEX_IMAGE" and node.image} \
            if wood and wood.node_tree else set()
        checks[f"material_{name}"] = (len(materials) == 2 and
                                      wood is not None and materials[1] is not None and
                                      wood.name.startswith("MAT_Crate_WoodAtlas") and
                                      materials[1].name.startswith("MAT_Crate_Metal") and
                                      "T_Crate_BaseColor" in texture_names and
                                      (target == "unreal" or "T_Crate_ORM" in texture_names))
    return checks, details


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", required=True, type=Path)
    parser.add_argument("--target", choices=TARGETS, required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    blend, out_dir = args.blend.resolve(strict=True), args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    preflight = audit()
    if preflight["variant"] != 2:
        raise ValueError("Only the scored textured candidate may be exported")
    target = TARGETS[args.target]
    output = out_dir / f"crate-{args.target}{target['extension']}"
    helpers = prepare_hierarchy()
    source_dimensions = {name: [round(value, 3) for value in bpy.data.objects[name].dimensions]
                         for name in EXPECTED}
    export_selected(args.target, output, helpers)
    checks, details = roundtrip(args.target, output, source_dimensions)
    failed = [name for name, passed in checks.items() if not passed]
    # FBX includes per-export metadata; hash the imported meaning separately
    # while retaining the exact raw-file digest for artifact integrity.
    semantic = {"checks": checks, "meshes": details}
    semantic_sha256 = hashlib.sha256(json.dumps(semantic, sort_keys=True,
                                               separators=(",", ":")).encode()).hexdigest()
    report = {"target": args.target, "format": target["format"],
              "source_blend_sha256": sha256(blend),
              "export": {"path": str(output), "sha256": sha256(output),
                         "bytes": output.stat().st_size},
              "preflight_triangles": preflight["triangles"],
              "export_hierarchy": [ROOT, LOD_ROOT, ANIMATED],
              "source_unit_system": "METRIC",
              "source_animation_clip": "AN_Crate_Turn",
              "source_dimensions_m": source_dimensions,
              "roundtrip_checks": checks, "roundtrip_meshes": details,
              "technical_score_percent": round(100 * (len(checks) - len(failed)) /
                                               len(checks)),
              "technical_score_basis": "Blender round-trip assertions; engine editor import pending",
              "roundtrip_semantic_sha256": semantic_sha256,
              "failed_checks": failed,
              "target_editor_import": "pending" if args.target != "generic" else "not applicable"}
    report_path = out_dir / f"crate-{args.target}-roundtrip.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{args.target} {target['format']} Blender roundtrip: "
          f"{len(checks) - len(failed)}/{len(checks)} checks")
    if failed:
        raise ValueError("Export roundtrip failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()
