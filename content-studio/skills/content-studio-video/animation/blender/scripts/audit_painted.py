"""Audit the painted teacup's packed albedo, restrained materials and motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing painted teacup object: {name}")
    return obj


def image_texture(mat, size):
    tex = next((node for node in mat.node_tree.nodes
                if node.bl_idname == "ShaderNodeTexImage"), None)
    if (not tex or not tex.image or not tex.image.packed_file or
            tuple(tex.image.size) != size):
        raise ValueError(f"The packed brush albedo is missing: {mat.name}")
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if (not bsdf or bsdf.inputs["Metallic"].default_value > 0 or
            bsdf.inputs["Roughness"].default_value < 0.85 or
            not bsdf.inputs["Base Color"].is_linked):
        raise ValueError(f"The painted albedo or matte finish changed: {mat.name}")
    return tex.image


def audit():
    scene = bpy.context.scene
    cup = required("SM_Painted_Cup")
    handle = required("SM_Painted_Handle")
    control = required("Painted cup turn control")
    saucer = required("SM_Painted_Saucer")
    camera = required("Painted teacup camera")
    backdrop = bpy.data.objects.get("Painted illustrated backdrop")
    steam = [required(f"SM_Painted_Steam_{index}") for index in range(3)]
    if (cup.parent != control or handle.parent != control or
            camera.data.type != "ORTHO" or camera.animation_data or
            cup.get("uv_ring_segments") != 48 or not cup.data.uv_layers or
            saucer.get("diameter_m") != 1.8):
        raise ValueError("The cup geometry, pivot, saucer, or fixed camera changed")
    if not scene.get("hand_painted_rule", "").startswith("packed brushwork albedo"):
        raise ValueError("The hand-painted material direction is missing")
    albedo = image_texture(cup.active_material, (256, 256))
    backdrop_image = image_texture(backdrop.active_material, (128, 128)) if backdrop else None
    if (not cup.active_material.get("painted_albedo") or
            (backdrop and not backdrop.active_material.get("brush_wash"))):
        raise ValueError("The painted surface or background wash lost its recipe marker")
    # Sample across the atlas to catch a blank replacement without baking a pixel copy.
    data = albedo.pixels[:]
    colors = {tuple(round(data[(y * 256 + x) * 4 + channel], 2)
                    for channel in range(3))
              for y in range(0, 256, 16) for x in range(0, 256, 16)}
    if len(colors) < 50:
        raise ValueError("The cup albedo no longer has layered painted values")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"cup_turn_rad": control.rotation_euler.z,
                          "steam_scale": [item.scale.x for item in steam],
                          "steam_root_z": [item.location.z for item in steam]}
    if (not control.animation_data or
            samples[72]["cup_turn_rad"] - samples[1]["cup_turn_rad"] < 1.2 or
            any(size > 0.01 for size in samples[1]["steam_scale"]) or
            any(size < 0.95 for size in samples[72]["steam_scale"]) or
            any(abs(z - 0.82) > 0.01 for z in samples[72]["steam_root_z"])):
        raise ValueError("The cup turn or rim-anchored steam growth failed")
    return {"cup_uv_segments": cup["uv_ring_segments"],
            "packed_cup_albedo": list(albedo.size),
            "packed_backdrop_wash": list(backdrop_image.size) if backdrop_image else None,
            "sampled_albedo_colors": len(colors),
            "cup_roughness": cup.active_material.node_tree.nodes.get(
                "Principled BSDF").inputs["Roughness"].default_value,
            "steam_curls": len(steam), "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited packed painted albedo, UVs, matte finish and steam motion")


if __name__ == "__main__":
    main()
