"""Audit paired PS1-like and PS5-like render constraints and matched motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing console-era object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("era_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown console-era candidate")
    retro = required("SM_Era_PS1_Ship_Rig")
    modern = required("SM_Era_PS5_Ship_Rig")
    retro_vertices = sum(len(obj.data.vertices) for obj in retro.children
                         if obj.type == "MESH")
    modern_vertices = sum(len(obj.data.vertices) for obj in modern.children
                          if obj.type == "MESH")
    retro_mat = bpy.data.materials.get("Era PS1 nearest texture")
    modern_mat = bpy.data.materials.get("Era PS5 PBR hull")
    nearest = next((node for node in retro_mat.node_tree.nodes
                    if node.type == "TEX_IMAGE" and node.name == "PS1 nearest texels"),
                   None)
    pbr = modern_mat.node_tree.nodes.get("Principled BSDF")
    checks = {
        "recipe": scene.get("era_recipe") ==
                  "PS1 low polygon nearest texture and scanlines beside PS5 smooth PBR flight",
        "shared_silhouette": required("PS1 hull").parent == retro and
                             required("PS5 beveled hull").parent == modern,
        "poly_budget": retro_vertices < 100 and modern_vertices > 1000 and
                       modern_vertices > retro_vertices * 10,
        "texture_filter": nearest is not None and nearest.interpolation == "Closest" and
                          tuple(nearest.image.size) == (16, 16),
        "pbr": pbr is not None and pbr.inputs["Metallic"].default_value > 0.7 and
               pbr.inputs["Roughness"].default_value < 0.3,
        "post_cue": all(required(f"PS1 CRT scanline {i}") for i in range(14)),
        "labels": required("PS1 era label").data.body == "PS1" and
                  required("PS5 era label").data.body == "PS5",
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Console-era invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 55, 72):
        scene.frame_set(frame)
        poses[frame] = {"retro_z": retro.location.z,
                        "modern_z": modern.location.z,
                        "retro_y": retro.location.y,
                        "modern_y": modern.location.y}
    if variant == 2:
        if not (poses[1]["retro_z"] == 0 and
                poses[55]["retro_z"] > 0.6 and
                poses[72]["modern_z"] > 0.6 and
                abs(poses[72]["retro_z"] - poses[72]["modern_z"]) < 0.001):
            raise ValueError("Paired launch motion changed")
    elif poses[72]["retro_z"] != 0 or poses[72]["modern_z"] != 0:
        raise ValueError("Baseline comparison unexpectedly launches")
    return {"variant": variant, "retro_vertices": retro_vertices,
            "modern_vertices": modern_vertices, "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited matching silhouettes, era topology, texels, PBR, scanlines, and launch")


if __name__ == "__main__":
    main()
