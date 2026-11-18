"""Audit the cartoon mascot's graphic silhouette and keyed squash/stretch jump."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing cartoon object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    root = required("Cartoon bounce control")
    body = required("SM_Cartoon_Body")
    eye = required("SM_Cartoon_Left_Eye")
    mitt = required("SM_Cartoon_Left_Mitt")
    shadow = required("SM_Cartoon_Shadow")
    cam = required("Cartoon mascot camera")
    for name in ("SM_Cartoon_Right_Eye", "SM_Cartoon_Right_Mitt",
                 "Cartoon Left rubber arm", "Cartoon Right rubber arm",
                 "Cartoon broad smile"):
        required(name)
    if cam.data.type != "ORTHO" or not scene.render.use_freestyle:
        raise ValueError("The graphic cartoon camera or outline is missing")
    outline = scene.view_layers[0].freestyle_settings.linesets[0].linestyle.thickness
    if outline < 2.5 or not scene.get("cartoon_shape_language", "").startswith("friendly circular"):
        raise ValueError("The bold circular shape direction is missing")
    if body.parent != root or eye.parent != root or mitt.parent != root:
        raise ValueError("Face and mitts must follow the squash/stretch control")
    mitt_to_eye = mitt.dimensions.x / eye.dimensions.x
    if mitt_to_eye < 1.2:
        raise ValueError("The mitts lost their expressive exaggeration")
    if not root.animation_data or not root.animation_data.action:
        raise ValueError("The mascot needs pose keys")
    samples = {}
    for frame in (1, 15, 36, 44, 62, 72):
        scene.frame_set(frame)
        samples[frame] = {"height_m": root.location.z,
                          "horizontal_scale": root.scale.x,
                          "vertical_scale": root.scale.z,
                          "shadow_width": shadow.scale.x}
    if (samples[15]["vertical_scale"] >= 0.8 or
            samples[15]["horizontal_scale"] <= 1.1 or
            samples[36]["height_m"] < 0.8 or
            samples[36]["vertical_scale"] < 1.15 or
            samples[44]["shadow_width"] >= samples[1]["shadow_width"] or
            samples[62]["vertical_scale"] >= 0.8 or
            abs(samples[72]["vertical_scale"] - 1) > 0.01):
        raise ValueError("Squash, jump, contact shadow, or recovery timing failed")
    return {"outline_px": outline, "mitt_to_eye_width": mitt_to_eye,
            "shape_language": scene["cartoon_shape_language"], "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited cartoon silhouette, squash/stretch, jump and shadow")


if __name__ == "__main__":
    main()
