"""Audit the era budget, procedural nearest atlas, CRT cue and camera push."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing PSX scene object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    if (scene.render.resolution_x, scene.render.resolution_y) != (320, 240):
        raise ValueError("PSX render must preserve its 320x240 source raster")
    if scene.view_settings.view_transform != "Standard":
        raise ValueError("PSX palette requires the authored Standard color transform")
    image = bpy.data.images.get("PSX 64px wall atlas")
    wall = bpy.data.materials.get("PSX nearest atlas wall")
    if not image or tuple(image.size) != (64, 64) or not image.packed_file or not wall:
        raise ValueError("The self-contained 64px atlas is missing")
    texture = next((node for node in wall.node_tree.nodes
                    if node.bl_idname == "ShaderNodeTexImage"), None)
    if not texture or texture.image != image or texture.interpolation != "Closest":
        raise ValueError("Wall atlas must use nearest filtering")
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH" and
              obj.name.startswith("SM_PSX_")]
    triangles = sum(len(poly.vertices) - 2 for obj in meshes for poly in obj.data.polygons)
    if triangles > 2000 or any(poly.use_smooth for obj in meshes
                               for poly in obj.data.polygons):
        raise ValueError("PSX room exceeds its flat low-poly budget")
    if any(mod.type in {"BEVEL", "SUBSURF"} for obj in meshes for mod in obj.modifiers):
        raise ValueError("Modern smoothing modifiers changed the PSX source geometry")
    crt = required("SM_PSX_CRT_Body")
    screen = required("SM_PSX_CRT_Screen")
    cam = required("PSX eye camera")
    fog = required("PSX distance fog")
    if not screen.get("analog_narrative_prop") or crt.type != "MESH":
        raise ValueError("The single analog CRT narrative prop is missing")
    volume = next((node for node in fog.data.materials[0].node_tree.nodes
                   if node.bl_idname == "ShaderNodeVolumePrincipled"), None)
    if not volume or volume.inputs["Density"].default_value <= 0:
        raise ValueError("Draw-distance fog is missing")
    emission = bpy.data.materials["PSX green phosphor"].node_tree.nodes.get(
        "Principled BSDF").inputs["Emission Strength"]
    samples = {}
    for frame in (1, 38, 72):
        scene.frame_set(frame)
        samples[frame] = {"camera_x": cam.location.x, "camera_y": cam.location.y,
                          "screen_emission": emission.default_value}
    if (samples[72]["camera_y"] - samples[1]["camera_y"] < 2.5 or
            samples[72]["screen_emission"] - samples[1]["screen_emission"] < 3 or
            abs(samples[38]["camera_x"]) < 0.01):
        raise ValueError("CRT reveal or handheld camera motion failed")
    return {"source_resolution": [320, 240], "atlas_size": list(image.size),
            "atlas_filter": texture.interpolation, "flat_mesh_triangles": triangles,
            "fog_density": volume.inputs["Density"].default_value,
            "crt_count": 1, "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    report = audit()
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Audited 64px atlas and {report['flat_mesh_triangles']} flat triangles")


if __name__ == "__main__":
    main()
