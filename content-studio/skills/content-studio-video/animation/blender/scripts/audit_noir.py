"""Audit noir silhouette, motivated light, wet street, rain and walk motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing noir object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    root = required("Noir detective root")
    coat = required("SM_Noir_Trench_Coat")
    brim = required("SM_Noir_Fedora_Brim")
    case = required("SM_Noir_Briefcase")
    arm = required("Noir case arm control")
    left = required("Noir left leg control")
    right = required("Noir right leg control")
    required("SM_Noir_Wet_Street")
    required("Noir back wall")
    haze = required("Noir alley haze")
    cam = required("Noir alley camera")
    cold_key = required("Noir hard window key")
    warm_key = required("Noir warm doorway practical")
    if (coat.parent != root or brim.parent != root or arm.parent != root or
            case.parent != arm or left.parent != root or right.parent != root or
            cam.data.type != "ORTHO" or cam.animation_data or
            scene.get("noir_palette") != "black, silver-blue, one warm practical"):
        raise ValueError("The noir silhouette, practical, or fixed camera changed")
    slats = [obj for obj in bpy.data.objects if obj.name.startswith("SM_Noir_Blinds_Light_")]
    rain = [obj for obj in bpy.data.objects if obj.name.startswith("Noir rain streak ")]
    reflections = [obj for obj in bpy.data.objects if obj.name.startswith("Noir wet reflection ")]
    ripples = [obj for obj in bpy.data.objects if obj.name.startswith("Noir puddle ripple ")]
    street = bpy.data.materials.get("Noir mirror wet asphalt")
    bsdf = street.node_tree.nodes.get("Principled BSDF") if street else None
    volume = next((node for node in haze.active_material.node_tree.nodes
                   if node.bl_idname == "ShaderNodeVolumePrincipled"), None)
    if (len(slats) != 6 or len(rain) != 18 or len(reflections) != 4 or
            len(ripples) not in (0, 3) or not street or
            not street.get("wet_street_mirror") or not bsdf or
            bsdf.inputs["Metallic"].default_value < 0.7 or
            bsdf.inputs["Roughness"].default_value > 0.11 or
            not volume or volume.inputs["Density"].default_value > 0.025 or
            cold_key.data.energy < 900 or cold_key.data.size > 0.5 or
            warm_key.data.energy > 300):
        raise ValueError("The hard noir keys, blinds, rain, haze, or wet street changed")
    samples = {}
    for frame in (1, 18, 36, 54, 72):
        scene.frame_set(frame)
        samples[frame] = {"root_x_m": root.location.x,
                          "left_leg_rad": left.rotation_euler.y,
                          "right_leg_rad": right.rotation_euler.y,
                          "case_swing_rad": arm.rotation_euler.y,
                          "ripple_scale": ripples[0].scale.x if ripples else None}
    if (not root.animation_data or not left.animation_data or
            not right.animation_data or not arm.animation_data or
            samples[72]["root_x_m"] - samples[1]["root_x_m"] < 2 or
            samples[18]["left_leg_rad"] < 0.25 or
            samples[18]["right_leg_rad"] > -0.25 or
            samples[36]["case_swing_rad"] > -0.1 or
            (ripples and samples[18]["ripple_scale"] <= samples[1]["ripple_scale"])):
        raise ValueError("The detective walk, case swing, or rain ripple changed")
    return {"blinds_light_slats": len(slats), "rain_streaks": len(rain),
            "wet_reflections": len(reflections), "animated_ripples": len(ripples),
            "street_metallic": bsdf.inputs["Metallic"].default_value,
            "street_roughness": bsdf.inputs["Roughness"].default_value,
            "haze_density": volume.inputs["Density"].default_value,
            "fixed_orthographic_camera": True, "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited noir silhouette, hard keys, wet street, rain and walk")


if __name__ == "__main__":
    main()
