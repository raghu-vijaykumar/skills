"""Audit packed watercolor pigment, scene-wide composition and boat motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing watercolor scene object: {name}")
    return obj


def packed_image(mat, expected):
    tex = next((node for node in mat.node_tree.nodes
                if node.bl_idname == "ShaderNodeTexImage"), None)
    if (not tex or not tex.image or not tex.image.packed_file or
            tuple(tex.image.size) != expected):
        raise ValueError(f"The packed watercolor image changed: {mat.name}")
    return tex.image


def audit():
    scene = bpy.context.scene
    canvas = required("SM_Watercolor_Canvas")
    boat = required("SM_Watercolor_Boat")
    control = required("Watercolor boat control")
    sail = required("SM_Watercolor_Sail")
    cam = required("Watercolor fixed camera")
    reeds = [required(f"SM_Watercolor_Reed_{index}") for index in range(8)]
    ripples = [obj for obj in bpy.data.objects
               if obj.name.startswith("Watercolor river stroke ")]
    if (cam.data.type != "ORTHO" or cam.animation_data or
            boat.parent != control or sail.parent != control or
            any(reed.parent is None for reed in reeds) or
            list(canvas.get("watercolor_canvas_px", [])) != [512, 288] or
            not scene.get("painterly_sublook", "").startswith("watercolor")):
        raise ValueError("The painterly camera, controls, or canvas contract changed")
    canvas_mat = canvas.active_material
    image = packed_image(canvas_mat, (512, 288))
    sail_image = packed_image(sail.active_material, (128, 128))
    if (not canvas_mat.get("pigment_washes") or not sail.active_material.get("pigment_sail") or
            not canvas_mat.node_tree.nodes.get("Emission")):
        raise ValueError("The paper, pigment, or washed sail recipe changed")
    data = image.pixels[:]
    colors = {tuple(round(data[(y * 512 + x) * 4 + channel], 2)
                    for channel in range(3))
              for y in range(0, 288, 16) for x in range(0, 512, 32)}
    if len(colors) < 100:
        raise ValueError("The sky, river, sun, and paper pigment lost variation")
    if len(ripples) < 12 or any(reed.type != "CURVE" for reed in reeds) or any(
            ripple.type != "MESH" for ripple in ripples):
        raise ValueError("Layered brush strokes or reeds are missing")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"boat_x_m": control.location.x,
                          "boat_z_m": control.location.z,
                          "reed_turn_rad": required("Watercolor reed control 0").rotation_euler.y}
    if (not control.animation_data or
            samples[72]["boat_x_m"] - samples[1]["boat_x_m"] < 2.5 or
            abs(samples[36]["reed_turn_rad"] - samples[1]["reed_turn_rad"]) < 0.1):
        raise ValueError("The boat drift or foreground reed sway failed")
    return {"packed_canvas": list(image.size), "packed_sail": list(sail_image.size),
            "sampled_pigment_colors": len(colors), "ripple_strokes": len(ripples),
            "foreground_reeds": len(reeds), "fixed_orthographic_camera": True,
            "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited packed watercolor canvas, pigment strokes, boat and reeds")


if __name__ == "__main__":
    main()
