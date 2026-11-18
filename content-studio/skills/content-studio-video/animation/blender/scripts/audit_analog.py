"""Audit the training tape's recorded room, tracking damage, and implied reveal."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing analog tape object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    chair = required("SM_Tape_Empty_Chair")
    screen = required("SM_Tape_Monitor_Screen")
    figure = required("Tape implied figure control")
    torso = required("SM_Tape_Implied_Figure")
    head = required("Tape implied figure head")
    label = required("SM_Tape_Camera_Label")
    tracking = required("SM_Tape_Rolling_Tracking_Bar")
    cam = required("Tape locked security camera")
    light = required("Tape unreliable fluorescent")
    scanlines = [obj for obj in scene.objects if obj.name.startswith("Tape fixed scanline ")]
    variant = scene.get("analog_variant")
    if variant not in (1, 2, 3):
        raise ValueError("Unknown analog candidate")
    # Name the violated invariant so saved-scene failures are actionable.
    checks = {
        "room": chair.type == "MESH" and screen.type == "MESH",
        "figure": bool(figure.get("implied_only")),
        "label": label.parent == cam and label.type == "FONT" and
                 "CAM 03" in label.data.body,
        "tracking": tracking.parent == cam and bool(tracking.animation_data),
        "flicker": bool(light.data.animation_data),
        "camera": cam.data.type == "ORTHO" and abs(cam.data.ortho_scale - 9.0) <= 0.01,
        "scanlines": len(scanlines) == (18 if variant == 1 else 31),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "transform": scene.view_settings.view_transform == "Standard",
        "recipe": scene.get("analog_recipe") ==
                  "mundane training room, implied doorway, locked tape UI, scanlines, tracking",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Wrong analog scene invariants: " + ", ".join(failed))
    if variant >= 2 and (not cam.animation_data or not torso.animation_data or
                         not head.animation_data):
        raise ValueError("Security-camera jitter or implied reveal is static")
    glow = None
    signal = None
    orientation = None
    if variant == 3:
        signal = required("Tape monitor dead channel")
        orientation = required("Tape monitor orientation")
        glow = bpy.data.materials["Tape dead green phosphor"].node_tree.nodes[
            "Principled BSDF"].inputs["Emission Strength"]
        if (not signal.animation_data or not orientation.animation_data or
                not glow.id_data.animation_data):
            raise ValueError("The monitor does not lose its training signal")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"tracking_y": tracking.location.y,
                          "light_energy": light.data.energy,
                          "figure_visible": not torso.hide_render,
                          "camera_x": cam.location.x,
                          "screen_emission": glow.default_value if glow else None,
                          "dead_channel_visible": not signal.hide_render if signal else None}
    if (samples[1]["tracking_y"] <= samples[72]["tracking_y"] or
            samples[1]["light_energy"] == samples[36]["light_energy"] or
            samples[1]["figure_visible"] or
            (variant == 1 and samples[72]["figure_visible"]) or
            (variant >= 2 and not samples[72]["figure_visible"]) or
            (variant == 3 and
             (samples[1]["screen_emission"] <= samples[72]["screen_emission"] or
              samples[1]["dead_channel_visible"] or
              not samples[72]["dead_channel_visible"]))):
        raise ValueError("Tracking, fluorescent flicker, or doorway reveal changed")
    return {"variant": variant, "fixed_scanlines": len(scanlines),
            "camera_label": label.data.body, "screen": screen.name,
            "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited training room, tape UI, tracking, camera jitter, and doorway reveal")


if __name__ == "__main__":
    main()
