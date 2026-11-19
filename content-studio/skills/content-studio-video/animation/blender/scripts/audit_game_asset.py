"""Audit crate UVs, packed maps, LOD budgets, collision, and export copies."""

import argparse
import bmesh
import json
import math
from pathlib import Path
import sys

import bpy


COUNTS = [264, 120, 72, 24]


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing pipeline object: {name}")
    return obj


def triangles(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def mesh_health(obj):
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        return {"nonmanifold_edges": sum(not edge.is_manifold for edge in bm.edges),
                "loose_vertices": sum(not vert.link_edges for vert in bm.verts)}
    finally:
        bm.free()


def uv_rects(mesh, layer):
    rects = []
    for polygon in mesh.polygons:
        points = [layer.data[index].uv for index in polygon.loop_indices]
        rects.append((min(point.x for point in points), max(point.x for point in points),
                      min(point.y for point in points), max(point.y for point in points)))
    return rects


def rectangles_overlap(left, right):
    return (min(left[1], right[1]) - max(left[0], right[0]) > 0.0001 and
            min(left[3], right[3]) - max(left[2], right[2]) > 0.0001)


def audit():
    scene = bpy.context.scene
    variant = scene.get("pipeline_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown pipeline candidate")
    lods = [required(f"SM_Crate_LOD{index}") for index in range(4)]
    copies = [required(f"SM_Crate_Export_LOD{index}") for index in range(4)]
    collision = required("UCX_SM_Crate_Export_01")
    groups = {name: bpy.data.collections.get(name) for name in
              ("COL_LODs_Crate", "COL_Export_Crate", "COL_Collision_Crate")}
    if any(group is None for group in groups.values()):
        raise ValueError("Missing LOD, export, or collision collection")
    counts = [triangles(obj) for obj in lods]
    export_counts = [triangles(obj) for obj in copies]
    ratios = [round(count / counts[0], 3) for count in counts]
    check = {
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "metric_scale": scene.unit_settings.system == "METRIC",
        "lod_counts": counts == COUNTS and list(scene["lod_triangles"]) == COUNTS,
        "lod_ratios": (0.40 <= ratios[1] <= 0.60 and 0.15 <= ratios[2] <= 0.30
                       and 0.05 <= ratios[3] <= 0.10),
        "lod_names": all(obj.name in groups["COL_LODs_Crate"].objects
                         for obj in lods),
        "mesh_health": all(mesh_health(obj) ==
                           {"nonmanifold_edges": 0, "loose_vertices": 0}
                           for obj in lods),
        "material_budget": all(len(obj.data.materials) == 2 for obj in lods),
        "screen_sizes": all((obj["screen_size_min"], obj["screen_size_max"]) ==
                            ((0.50, 0.25, 0.10, 0.0)[index],
                             (1.0, 0.50, 0.25, 0.10)[index])
                            for index, obj in enumerate(lods)),
        "export_copies": (export_counts == COUNTS and
                          all(obj.name in groups["COL_Export_Crate"].objects and
                              obj.hide_render and not obj.animation_data and
                              obj.location.length < 0.0001 and
                              all(abs(value - 1.0) < 0.0001 for value in obj.scale)
                              for obj in copies)),
        "collision": (collision.name in groups["COL_Collision_Crate"].objects and
                      triangles(collision) == 12 and
                      mesh_health(collision) ==
                      {"nonmanifold_edges": 0, "loose_vertices": 0} and
                      all(abs(value - 1.02) < 0.0001 for value in collision.dimensions) and
                      len(collision.data.materials) == 0 and collision.hide_render),
    }
    uv_report = {}
    for index, obj in enumerate(lods):
        texture = obj.data.uv_layers.get("UVMap")
        lightmap = obj.data.uv_layers.get("LightmapUV")
        if not texture or not lightmap:
            raise ValueError(f"LOD{index} lacks texture or lightmap UVs")
        main = uv_rects(obj.data, texture)
        secondary = uv_rects(obj.data, lightmap)
        inside = all(0 <= value <= 1 for rect in main + secondary for value in rect)
        unique_lightmap = not any(rectangles_overlap(a, b)
                                  for i, a in enumerate(secondary)
                                  for b in secondary[i + 1:])
        body_occupancy = sum((rect[1] - rect[0]) * (rect[3] - rect[2])
                             for rect in main[:6])
        distinct_body = not any(rectangles_overlap(a, b)
                                for i, a in enumerate(main[:6])
                                for b in main[i + 1:6])
        uv_report[f"LOD{index}"] = {"body_occupancy": round(body_occupancy, 3),
                                  "lightmap_faces": len(secondary),
                                  "inside_zero_one": inside,
                                  "lightmap_unique": unique_lightmap}
        check[f"uv_lod{index}"] = (inside and unique_lightmap and distinct_body and
                                    body_occupancy > 0.85)
    if variant == 2:
        base = bpy.data.images.get("T_Crate_BaseColor")
        orm = bpy.data.images.get("T_Crate_ORM")
        wood = bpy.data.materials.get("MAT_Crate_WoodAtlas")
        check["packed_textures"] = (base is not None and orm is not None and
                                    base.size[:] == orm.size[:] == (256, 256) and
                                    base.packed_file is not None and
                                    orm.packed_file is not None and
                                    base.colorspace_settings.name == "sRGB" and
                                    orm.colorspace_settings.name == "Non-Color")
        check["texture_nodes"] = (wood is not None and wood.use_nodes and
                                  wood.node_tree.nodes.get("Crate base-color atlas") is not None and
                                  wood.node_tree.nodes.get("Crate AO-roughness-metallic atlas")
                                  is not None and wood.get("orm_red_is_ao") is True)
        check["material_names"] = all(
            [slot.name for slot in obj.data.materials] ==
            ["MAT_Crate_WoodAtlas", "MAT_Crate_Metal"] for obj in lods)
        control = required("Collision view control")
        locations = {}
        for frame in (1, 40, 72):
            scene.frame_set(frame)
            locations[frame] = round(control.location.z, 3)
        check["motion"] = (all(obj.animation_data for obj in lods) and
                           locations[1] == locations[40] == 2.17 and
                           locations[72] == 0.87 and
                           len([obj for obj in bpy.data.objects
                                if obj.name.startswith("Collision edge")]) == 12)
    else:
        check["greybox"] = (bpy.data.images.get("T_Crate_BaseColor") is None and
                            bpy.data.objects.get("Collision view control") is None and
                            all(not obj.animation_data for obj in lods))
    failed = [name for name, passed in check.items() if not passed]
    if failed:
        raise ValueError("Pipeline asset invariants failed: " + ", ".join(failed))
    return {"variant": variant, "checks": check, "triangles": counts,
            "ratios": ratios, "uv": uv_report,
            "collision_triangles": triangles(collision)}


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
    print(f"Audited pipeline asset variant {result['variant']} with {len(result['checks'])} checks")


if __name__ == "__main__":
    main()
