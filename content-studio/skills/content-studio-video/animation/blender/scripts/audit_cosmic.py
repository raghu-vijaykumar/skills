"""Audit the cosmic aperture's scale, disconnected geometry, and hidden motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing cosmic object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    witness = required("SM_Cosmic_Witness")
    aperture = required("SM_Cosmic_Broken_Aperture")
    core = required("SM_Cosmic_Void")
    slit = required("SM_Cosmic_Gold_Slit")
    cam = required("Cosmic impossible scale camera")
    slabs = [obj for obj in scene.objects if obj.name.startswith("Cosmic misregistered slab ")]
    monoliths = [obj for obj in scene.objects if obj.name.startswith("Cosmic floating monolith ")]
    shards = [obj for obj in scene.objects if obj.name.startswith("Cosmic detached orbit shard ")]
    bpy.context.view_layer.update()
    world_z = [(aperture.matrix_world @ Vector(corner)).z for corner in aperture.bound_box]
    aperture_height = max(world_z) - min(world_z)
    # Report the exact failed invariant so a saved scene can be repaired without guessing.
    checks = {
        "slabs": len(slabs) == 9,
        "monoliths": len(monoliths) == 8,
        "shards": len(shards) == 9,
        "void": bool(core.get("unknowable_form")),
        "witness": bool(witness.get("tiny_witness")),
        "scale": aperture_height >= witness.dimensions.z * 5,
        "camera": cam.data.type == "ORTHO" and abs(cam.data.ortho_scale - 17.8) <= 0.01,
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "recipe": scene.get("cosmic_recipe") ==
                  "tiny witness, detached geometry, abyssal blue, sickly gold, unshown void",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Wrong cosmic scene invariants: " + ", ".join(failed) +
                         f" (aperture_z={aperture_height:.2f}, "
                         f"witness_z={witness.dimensions.z:.2f})")
    variant = scene.get("cosmic_variant")
    iris = bpy.data.objects.get("Cosmic iris motion control")
    stars = [obj for obj in scene.objects if obj.name.startswith("Cosmic unreachable glint ")]
    tendrils = [obj for obj in scene.objects if obj.name.startswith("Cosmic partial silhouette ")]
    if ((variant == 1 and (iris is not None or stars or tendrils)) or
            (variant in (2, 3) and (iris is None or len(stars) != 22 or len(tendrils) != 2))):
        raise ValueError("Candidate-specific hidden form changed")
    if (not slit.animation_data or not cam.animation_data or
            (variant in (2, 3) and not iris.animation_data)):
        raise ValueError("The aperture or camera is static")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"slit_width_scale": slit.scale.x,
                          "camera_x": cam.location.x,
                          "iris_z_angle": iris.rotation_euler.z if iris else None}
    if (samples[1]["camera_x"] <= samples[72]["camera_x"] or
            (variant in (2, 3) and samples[1]["iris_z_angle"] >=
             samples[72]["iris_z_angle"])):
        raise ValueError("The inspection push or iris shift changed")
    if variant == 3:
        inner = required("Cosmic off-axis inner ring")
        orbit = required("Cosmic broken orbit control")
        if not inner.animation_data or not orbit.animation_data:
            raise ValueError("The moving inner ring or detached orbit is static")
    return {"variant": variant, "aperture_to_witness_ratio":
            aperture_height / witness.dimensions.z,
            "misregistered_slabs": len(slabs), "floating_monoliths": len(monoliths),
            "orbit_shards": len(shards), "unreachable_glints": len(stars),
            "partial_silhouettes": len(tendrils), "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited cosmic scale, detached architecture, hidden iris, and camera push")


if __name__ == "__main__":
    main()
