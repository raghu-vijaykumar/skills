"""Audit Blender 5's reversible beauty compositor against the unchanged alley."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def linked(tree, source, target):
    return any(link.from_node.name == source and link.to_node.name == target
               for link in tree.links)


def audit():
    scene = bpy.context.scene
    variant = scene.get("composite_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown compositor comparison variant")
    tree = scene.compositing_node_group
    if tree is None:
        raise ValueError("No Blender 5 compositor node group")
    nodes = tree.nodes
    source = nodes.get("IN_Cyber_Combined")
    output = nodes.get("OUT_Cyber_Beauty")
    checks = {
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "agx_view": scene.view_settings.view_transform == "AgX",
        "compositing_enabled": scene.render.use_compositing,
        "beauty_output": (tree.bl_idname == "CompositorNodeTree" and
                          source is not None and output is not None and
                          output.bl_idname == "NodeGroupOutput" and
                          "Image" in output.inputs),
        "mist_pass_available": scene.view_layers[0].use_pass_mist,
        "same_scene_action": (scene.get("cyberpunk_variant") == 2 and
                              bpy.data.objects.get("SM_Cyber_Courier_Drone_Rig")
                              is not None and scene.camera.name ==
                              "Cyberpunk alley inspection camera"),
    }
    if variant == 1:
        checks["raw_chain"] = (len(nodes) == 2 and
                               linked(tree, "IN_Cyber_Combined",
                                      "OUT_Cyber_Beauty"))
    else:
        exposure = nodes.get("Exposure correction")
        hue = nodes.get("Neon saturation trim")
        glare = nodes.get("Practical-neon fog glow")
        if not all((exposure, hue, glare)):
            raise ValueError("Missing exposure, saturation, or glare node")
        checks["reversible_chain"] = (len(nodes) == 5 and
                                      linked(tree, "IN_Cyber_Combined",
                                             "Exposure correction") and
                                      linked(tree, "Exposure correction",
                                             "Neon saturation trim") and
                                      linked(tree, "Neon saturation trim",
                                             "Practical-neon fog glow") and
                                      linked(tree, "Practical-neon fog glow",
                                             "OUT_Cyber_Beauty"))
        checks["bounded_grade"] = (abs(exposure.inputs["Exposure"].default_value
                                       + 0.10) < 0.0001 and
                                   abs(hue.inputs["Saturation"].default_value
                                       - 1.06) < 0.0001)
        checks["fog_glow"] = (glare.inputs["Type"].default_value == "Fog Glow" and
                              abs(glare.inputs["Threshold"].default_value
                                  - 0.70) < 0.0001 and
                              abs(glare.inputs["Strength"].default_value
                                  - 1.0) < 0.0001 and
                              abs(glare.inputs["Size"].default_value
                                  - 0.85) < 0.0001)
        checks["look_record"] = "fog glow threshold 0.70" in scene.get(
            "composite_recipe", "")
    failed = [key for key, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Compositor audit failed: " + ", ".join(failed))
    return {"variant": variant, "checks": checks,
            "nodes": [node.name for node in nodes],
            "links": [[link.from_node.name, link.to_node.name]
                      for link in tree.links]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    result = audit()
    output = args.out.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Audited compositor variant {result['variant']} with {len(result['checks'])} checks")


if __name__ == "__main__":
    main()
