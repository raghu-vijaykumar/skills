"""Export the audited crate kit, reimport in Blender, and report target limits."""

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


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_selected(target, path):
    bpy.ops.object.select_all(action="DESELECT")
    selected = [bpy.data.objects[name] for name in EXPECTED]
    for obj in selected:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = selected[0]
    if target == "unreal":
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
                                 apply_unit_scale=True, global_scale=1.0,
                                 axis_forward="-Z", axis_up="Y",
                                 bake_anim=False, use_custom_props=True,
                                 path_mode="COPY", embed_textures=True)
    else:
        bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB",
                                  use_selection=True, export_yup=True,
                                  export_apply=True, export_extras=True,
                                  export_animations=False)
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
    imported = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == "MESH"}
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
    source_dimensions = {name: [round(value, 3) for value in bpy.data.objects[name].dimensions]
                         for name in EXPECTED}
    export_selected(args.target, output)
    checks, details = roundtrip(args.target, output, source_dimensions)
    failed = [name for name, passed in checks.items() if not passed]
    report = {"target": args.target, "format": target["format"],
              "source_blend_sha256": sha256(blend),
              "export": {"path": str(output), "sha256": sha256(output),
                         "bytes": output.stat().st_size},
              "preflight_triangles": preflight["triangles"],
              "source_dimensions_m": source_dimensions,
              "roundtrip_checks": checks, "roundtrip_meshes": details,
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
