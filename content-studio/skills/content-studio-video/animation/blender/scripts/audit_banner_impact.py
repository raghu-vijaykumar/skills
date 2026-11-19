"""Audit cloth pre-roll, rigid-body transform bake, and timed mesh FX."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing banner impact object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("banner_impact_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown banner impact variant")
    banner = required("SM_Baked_Wind_Banner")
    orb = required("SM_Baked_Impact_Orb")
    plate = required("SM_Conductive_Impact_Plate")
    ring = required("FX_Impact_Ring")
    ribbons = [obj for obj in bpy.data.objects
               if obj.name.startswith("FX_Impact_Ribbon_")]
    checks = {
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "metric_stage": scene.unit_settings.system == "METRIC" and
                        required("Impact lab floor").type == "MESH",
        "separate_collections": all(bpy.data.collections.get(name) is not None for name in
                                    ("COL_Cloth_Banner", "COL_Physics_Impact",
                                     "COL_FX_Impact")),
        "camera": scene.camera == required("Banner impact camera") and
                  scene.camera.data.type == "ORTHO",
        "consistent_mesh": banner.type == orb.type == plate.type == "MESH" and
                           len(banner.data.vertices) == 117 and
                           all(len(poly.vertices) == 4 for poly in banner.data.polygons),
    }
    if variant == 2:
        cloth_source = required("SRC_Cloth_Banner")
        wind = required("SRC_Wind_Banner")
        rb_source = required("SRC_Rigidbody_Orb")
        cloth = next((mod for mod in cloth_source.modifiers if mod.type == "CLOTH"), None)
        pin = cloth_source.vertex_groups.get("PIN_Cloth")
        keys = banner.data.shape_keys
        world = scene.rigidbody_world
        impact = int(scene.get("impact_frame", -1))
        checks.update({
            "cloth_source_and_scale": cloth_source.hide_render and cloth is not None and
                                      not cloth.show_render and
                                      all(abs(scale - 1) < 0.0001
                                          for scale in cloth_source.scale),
            "pin_column": pin is not None and all(
                any(member.group == pin.index and member.weight >= 0.99
                    for member in cloth_source.data.vertices[row * 13].groups)
                for row in range(9)),
            "cloth_settings": cloth is not None and cloth.settings.quality == 8 and
                              cloth.settings.vertex_group_mass == "PIN_Cloth" and
                              cloth.point_cache.frame_start == 1 and
                              cloth.point_cache.frame_end == 92,
            "cloth_preroll_bake": scene.get("cloth_preroll") == 20 and
                                   scene.get("cloth_baked_frames") == 72 and
                                   keys is not None and len(keys.key_blocks) == 73 and
                                   keys.animation_data is not None,
            "wind_source": wind.field.type == "WIND" and
                           tuple(wind.get("baked_strength_range", [])) == (8, 24) and
                           wind.field.strength == 0,
            "mast_collider": any(mod.type == "COLLISION" for mod in
                                 required("Banner mast").modifiers),
            "active_passive_pair": rb_source.hide_render and
                                   rb_source.rigid_body is not None and
                                   rb_source.rigid_body.type == "ACTIVE" and
                                   rb_source.rigid_body.collision_shape == "SPHERE" and
                                   plate.rigid_body is not None and
                                   plate.rigid_body.type == "PASSIVE" and
                                   plate.rigid_body.collision_shape == "BOX",
            "rigid_world": world is not None and world.substeps_per_frame == 120 and
                           world.point_cache.frame_end == 72 and
                           scene.get("physics_baked_frames") == 72 and
                           orb.animation_data is not None,
            "impact_timing": 12 <= impact <= 24,
            "bounded_fx": len(ribbons) == 12 and all(
                obj.get("fx_kind") == "timed emissive mesh ribbon" and
                obj.animation_data is not None and len(obj.data.polygons) == 1
                for obj in ribbons),
            "emissive_fx": all(bpy.data.materials.get(name) is not None and
                               bpy.data.materials[name].node_tree.nodes["Principled BSDF"]
                               .inputs["Emission Strength"].default_value >= 6
                               for name in ("MAT_FX_Cyan", "MAT_FX_Amber")),
            "fx_ring": ring.animation_data is not None and not ring.hide_render,
        })
        scene.frame_set(1)
        first_tip = banner.data.shape_keys.key_blocks["Cloth_001"].data[-1].co.copy()
        start_z = orb.location.z
        scene.frame_set(impact + 1)
        checks["impact_pose"] = (orb.location.z < start_z - 1 and
                                 ribbons[0].scale.x > 0.9 and ring.scale.x > 0.9)
        scene.frame_set(36)
        checks["cloth_changes_shape"] = (
            banner.data.shape_keys.key_blocks["Cloth_036"].data[-1].co -
            first_tip).length > 0.10
        checks["shape_key_frame"] = abs(
            banner.data.shape_keys.key_blocks["Cloth_036"].value - 1) < 0.001
        scene.frame_set(72)
        checks["fx_tail_ends"] = ribbons[0].scale.x < 0.01 and ring.scale.x <= 0.011
        checks["held_rigid_pose"] = orb.location.z >= 0.45
    else:
        checks["static_baseline"] = (banner.data.shape_keys is None and
                                     banner.animation_data is None and
                                     orb.rigid_body is None and
                                     orb.animation_data is None and
                                     plate.rigid_body is None and
                                     ring.hide_render and
                                     all(obj.hide_render for obj in ribbons))
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Banner impact audit failed: " + ", ".join(failed))
    return {"variant": variant, "checks": checks,
            "cloth_vertices": len(banner.data.vertices),
            "fx_ribbons": len(ribbons),
            "impact_frame": scene.get("impact_frame")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Audited banner impact variant {report['variant']} with {len(report['checks'])} checks")


if __name__ == "__main__":
    main()
