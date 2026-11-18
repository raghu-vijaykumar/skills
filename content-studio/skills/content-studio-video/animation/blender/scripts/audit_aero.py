"""Audit the glossy aqua card, nature cue, bubble motion, and candidate differences."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing Aero object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    card = required("SM_Aero_Aqua_Card")
    outer = required("SM_Aero_Glass_Bubble")
    core = required("Aero bubble inner core")
    float_control = required("Aero bubble float control")
    leaf = required("SM_Aero_Leaf")
    hinge = required("Aero leaf hinge")
    sweep = required("Aero sweep key")
    cam = required("Aero optimism camera")
    glass = bpy.data.materials.get("Aero glass bubble skin")
    aqua = bpy.data.materials.get("Aero luminous aqua shell")
    if glass is None or aqua is None:
        raise ValueError("Aqua or glass material missing")
    glass_shader = glass.node_tree.nodes.get("Principled BSDF")
    aqua_shader = aqua.node_tree.nodes.get("Principled BSDF")
    if (glass_shader is None or aqua_shader is None or
            glass_shader.inputs["Transmission Weight"].default_value < 0.25 or
            glass_shader.inputs["Coat Weight"].default_value < 0.9 or
            aqua_shader.inputs["Transmission Weight"].default_value < 0.15 or
            not glass.get("aero_gloss_stack") or not aqua.get("aero_gloss_stack")):
        raise ValueError("The glossy layered aqua surface changed")
    if (not card.get("skeuomorphic_panel") or
            len([obj for obj in bpy.data.objects if obj.name.startswith("Aero soft UI pill ")]) != 3 or
            len([obj for obj in bpy.data.objects if obj.name.startswith("Aero header dot ")]) != 3 or
            len([obj for obj in bpy.data.objects if obj.get("aero_cloud")]) != 3 or
            outer.parent != float_control or core.parent != float_control or
            leaf.parent != hinge or hinge.parent != float_control or
            not leaf.get("nature_cue") or
            cam.data.type != "ORTHO" or abs(cam.data.ortho_scale - 6.6) > 0.001 or
            (scene.render.resolution_x, scene.render.resolution_y,
             scene.render.fps, scene.frame_end) != (960, 540, 24, 72) or
            scene.get("aero_recipe") !=
            "glossy aqua card, glass bubbles, spring greens, leaf and soft UI motion"):
        raise ValueError("The aqua UI, bubble, leaf, or camera contract changed")
    lights = [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
    if len(lights) != 3 or sweep.type != "LIGHT":
        raise ValueError("The three-light softbox and sweep rig changed")
    variant = scene.get("aero_variant")
    bubbles = [obj for obj in bpy.data.objects if obj.name.startswith("SM_Aero_Bubble_")]
    vein = bpy.data.objects.get("Aero pale leaf vein")
    if ((variant == 1 and (len(bubbles) != 2 or vein is not None)) or
            (variant == 2 and (len(bubbles) != 5 or vein is None or vein.parent != hinge))):
        raise ValueError("The candidate bubble trail or leaf vein changed")
    if not all(obj.animation_data for obj in [float_control, hinge, sweep, *bubbles]):
        raise ValueError("Aero float, leaf, sweep, or bubble motion missing")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"bubble_z": float_control.location.z,
                          "leaf_y_angle": hinge.rotation_euler.y,
                          "first_bubble_z": bubbles[0].location.z,
                          "sweep_x": sweep.location.x}
    if (samples[1]["bubble_z"] >= samples[36]["bubble_z"] or
            samples[1]["first_bubble_z"] >= samples[72]["first_bubble_z"] or
            samples[1]["sweep_x"] >= samples[72]["sweep_x"] or
            (variant == 1 and abs(samples[1]["leaf_y_angle"] -
                                  samples[72]["leaf_y_angle"]) > 0.01) or
            (variant == 2 and samples[1]["leaf_y_angle"] >=
                              samples[72]["leaf_y_angle"])):
        raise ValueError("Bubble rise, leaf opening, or highlight sweep changed")
    return {"variant": variant, "glossy_transmission": True,
            "skeuomorphic_ui_pills": 3, "soft_clouds": 3,
            "floating_bubbles": len(bubbles), "leaf_vein": vein is not None,
            "lights": len(lights), "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited glossy aqua UI, bubble trail, leaf, light sweep, and camera")


if __name__ == "__main__":
    main()
