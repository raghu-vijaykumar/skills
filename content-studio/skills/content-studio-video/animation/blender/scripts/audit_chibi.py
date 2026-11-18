"""Audit the saved chibi head ratio, tiny limbs, postal prop and offer motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing chibi object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    root = required("Chibi courier root")
    head_control = required("Chibi head control")
    head = required("SM_Chibi_Head")
    torso = required("SM_Chibi_Torso")
    left_eye = required("SM_Chibi_Left_Eye")
    right_eye = required("SM_Chibi_Right_Eye")
    arm = required("Chibi offer arm control")
    envelope = required("SM_Chibi_Envelope")
    left_boot = required("Chibi left boot")
    right_boot = required("Chibi right boot")
    shadow = required("Chibi contact shadow")
    cam = required("Chibi portrait camera")
    if (cam.data.type != "ORTHO" or cam.animation_data or
            head_control.parent != root or head.parent != head_control or
            torso.parent != root or arm.parent != root or envelope.parent != arm or
            left_eye.parent != head_control or right_eye.parent != head_control or
            left_boot.parent != root or right_boot.parent != root or
            not torso.get("design_short_body") or
            envelope.get("story_prop") != "delivered letter"):
        raise ValueError("The editable chibi body, letter, or camera changed")
    scene.frame_set(1)
    bpy.context.view_layer.update()
    head_height = head.dimensions.z
    full_height = (head.matrix_world.translation.z + head_height / 2 -
                   min(boot.matrix_world.translation.z - boot.dimensions.z / 2
                       for boot in (left_boot, right_boot)))
    # Audit actual model dimensions, not just a descriptive custom property.
    ratio = head_height / full_height
    if not (0.50 <= ratio <= 0.67 and head_height > torso.dimensions.z * 1.7):
        raise ValueError(f"Chibi head and short-body ratio changed: {ratio:.3f}")
    if len([obj for obj in bpy.data.objects if "short leg" in obj.name]) != 2:
        raise ValueError("The tiny legs changed")
    enriched = bpy.data.objects.get("Chibi courier cap badge") is not None
    if enriched:
        for name in ("Chibi courier cap visor", "Chibi mail satchel strap",
                     "Chibi mail satchel", "Chibi postal stage roundel"):
            required(name)
    samples = {}
    for frame in (1, 23, 36, 60, 72):
        scene.frame_set(frame)
        samples[frame] = {"hop_m": root.location.z,
                          "offer_rad": arm.rotation_euler.y,
                          "head_tilt_rad": head_control.rotation_euler.z,
                          "left_eye_z": left_eye.scale.z,
                          "right_eye_z": right_eye.scale.z,
                          "shadow_width": shadow.scale.x}
    if (not root.animation_data or not arm.animation_data or
            not head_control.animation_data or not left_eye.animation_data or
            not right_eye.animation_data or
            samples[36]["hop_m"] < 0.70 or
            samples[36]["offer_rad"] > -1.0 or
            samples[23]["left_eye_z"] > 0.2 or
            samples[23]["right_eye_z"] > 0.2 or
            samples[36]["shadow_width"] >= samples[1]["shadow_width"] or
            abs(samples[72]["hop_m"]) > 0.001):
        raise ValueError("The hop, blink, letter offer, or contact shadow changed")
    return {"head_to_full_height": round(ratio, 4),
            "head_height_m": round(head_height, 4),
            "full_height_m": round(full_height, 4),
            "short_legs": 2, "postal_enrichment": enriched,
            "fixed_orthographic_camera": True, "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited chibi ratios, postal story props, blink, hop and offer")


if __name__ == "__main__":
    main()
