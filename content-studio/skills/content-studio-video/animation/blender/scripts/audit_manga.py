"""Audit the monochrome manga close-up, packed screentone and gaze emphasis."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing manga object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    face_control = required("Manga face control")
    face = required("SM_Manga_Face")
    eye = required("SM_Manga_Eye_White")
    iris = required("SM_Manga_Iris")
    gaze = required("Manga gaze control")
    tone = required("SM_Manga_Screentone")
    glyph = required("SM_Manga_Exclamation")
    cam = required("Manga panel camera")
    required("SM_Manga_Hair")
    if (face.parent != face_control or eye.parent != face_control or
            gaze.parent != face_control or iris.parent != gaze):
        raise ValueError("The face or gaze controls lost their editability")
    if cam.data.type != "ORTHO" or not scene.render.use_freestyle:
        raise ValueError("The manga panel camera or ink outline is missing")
    outline = scene.view_layers[0].freestyle_settings.linesets[0].linestyle.thickness
    if outline < 2 or not scene.get("manga_value_language", "").startswith("grayscale"):
        raise ValueError("The monochrome print direction was removed")
    manga_mats = [mat for mat in bpy.data.materials if mat.name.startswith("Manga ")]
    if len(manga_mats) < 5 or any(max(mat.diffuse_color[:3]) - min(
            mat.diffuse_color[:3]) > 0.005 for mat in manga_mats):
        raise ValueError("A colored material broke the grayscale design")
    mat = tone.active_material
    tex = next((node for node in mat.node_tree.nodes
                if node.bl_idname == "ShaderNodeTexImage"), None)
    if (not mat.get("monochrome_print") or not tex or not tex.image or
            tuple(tex.image.size) != (256, 256) or not tex.image.packed_file):
        raise ValueError("The 256-pixel manga screentone must be packed")
    if len([obj for obj in bpy.data.objects if obj.name.startswith("Manga emphasis line")]) != 7:
        raise ValueError("The seven action lines are missing")
    if len([obj for obj in bpy.data.objects if obj.name.startswith(
            ("Manga panel vertical border", "Manga panel horizontal border"))]) != 4:
        raise ValueError("The ink panel border is incomplete")
    if glyph.data.body != "!":
        raise ValueError("The ink emphasis glyph is missing")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"gaze_world_x": gaze.matrix_world.translation.x,
                          "iris_scale": gaze.scale.x,
                          "face_tilt_rad": face_control.rotation_euler.z,
                          "glyph_hidden": glyph.hide_render}
    if (not gaze.animation_data or not gaze.animation_data.action or
            samples[36]["gaze_world_x"] - samples[1]["gaze_world_x"] < 0.5 or
            samples[36]["iris_scale"] <= samples[1]["iris_scale"] * 1.4 or
            not samples[1]["glyph_hidden"] or samples[36]["glyph_hidden"]):
        raise ValueError("The gaze snap, dilation, or emphasis cue failed")
    return {"outline_px": outline, "grayscale_materials": len(manga_mats),
            "packed_screentone": list(tex.image.size),
            "emphasis_lines": 7, "border_bars": 4,
            "face_closeup_scale": face_control.scale.x, "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited grayscale panel, packed screentone, gaze and ink emphasis")


if __name__ == "__main__":
    main()
