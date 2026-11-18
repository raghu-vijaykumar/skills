"""Audit the comic panel's packed halftone, ink staging, rocket move and impact cue."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing comic object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    root = required("Comic rocket control")
    body = required("SM_Comic_Rocket_Body")
    nose = required("SM_Comic_Rocket_Nose")
    flame = required("SM_Comic_Flame")
    print_plane = required("SM_Comic_Halftone_Backdrop")
    burst = required("SM_Comic_Impact_Burst")
    letters = required("SM_Comic_Whoosh_Lettering")
    cam = required("Comic panel camera")
    required("SM_Comic_Rocket_Window")
    if body.parent != root or nose.parent != root or flame.parent != root:
        raise ValueError("The rocket pieces lost the editable hero control")
    if cam.data.type != "ORTHO" or not scene.render.use_freestyle:
        raise ValueError("Comic framing or ink contour is missing")
    outline = scene.view_layers[0].freestyle_settings.linesets[0].linestyle.thickness
    if outline < 2 or not scene.get("comic_print_language", "").startswith("ink contour"):
        raise ValueError("Graphic print language was removed")
    if len([obj for obj in bpy.data.objects if obj.name.startswith("Comic speed line")]) != 6:
        raise ValueError("The six printed speed lines are missing")
    if len([obj for obj in bpy.data.objects if obj.name.startswith(
            ("Comic panel vertical ink", "Comic panel horizontal ink"))]) != 4:
        raise ValueError("The panel border is incomplete")
    mat = print_plane.active_material
    tex = next((node for node in mat.node_tree.nodes
                if node.bl_idname == "ShaderNodeTexImage"), None)
    if (mat.get("print_dots") != 256 or not tex or not tex.image or
            tuple(tex.image.size) != (256, 256) or not tex.image.packed_file):
        raise ValueError("The 256-pixel halftone print must be packed")
    if letters.data.body != "WHOOSH!" or letters.data.fill_mode != "BOTH":
        raise ValueError("The action lettering is missing or hollow")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"rocket_x_m": root.location.x,
                          "rocket_z_m": root.location.z,
                          "flame_z_scale": flame.scale.z,
                          "burst_scale": burst.scale.x,
                          "burst_hidden": burst.hide_render,
                          "letters_hidden": letters.hide_render}
    if (not root.animation_data or not root.animation_data.action or
            samples[1]["rocket_x_m"] > -1 or
            samples[36]["rocket_x_m"] < -0.1 or
            samples[72]["rocket_x_m"] < 1 or
            not samples[1]["burst_hidden"] or samples[36]["burst_hidden"] or
            samples[36]["burst_scale"] < 0.5 or
            not samples[1]["letters_hidden"] or samples[36]["letters_hidden"] or
            samples[36]["flame_z_scale"] < samples[1]["flame_z_scale"] * 2):
        raise ValueError("Rocket, burst, lettering, or flame action failed")
    return {"outline_px": outline, "packed_halftone": list(tex.image.size),
            "speed_lines": 6, "panel_borders": 4,
            "burst_triangles": len(burst.data.polygons), "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited ink panel, packed halftone, rocket, burst and lettering")


if __name__ == "__main__":
    main()
