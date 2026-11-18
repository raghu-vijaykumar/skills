"""Audit the retrowave grid, striped sunset, chrome coupe, and travel."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing retrowave object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    car = required("SM_Retro_Chrome_Coupe_Rig")
    body = required("SM_Retro_Chrome_Coupe_Body")
    sun = required("SM_Retro_Striped_Sunset")
    gate = required("SM_Retro_Neon_Gate")
    cam = required("Retro highway follow camera")
    wheels = [required(f"SM_Retro_Coupe_Wheel_{side}_{fore}")
              for side in (-1, 1) for fore in (-1, 1)]
    variant = scene.get("retro_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown retrowave candidate")
    chrome = bpy.data.materials["Retro satin chrome coupe"]
    cyan = bpy.data.materials["Retro electric cyan grid"]
    pink = bpy.data.materials["Retro neon magenta lane"]
    checks = {
        "recipe": scene.get("retro_recipe") ==
                  "striped sunset, perspective cyan grid, chrome coupe, magenta gateway, dusk mountains",
        "grid_horizon": (required("SM_Retro_Grid_Ground").type == "MESH" and
                         all(required(f"Retro cyan longitudinal grid {i}").type == "MESH"
                             for i in range(-15, 16)) and
                         all(required(f"Retro cyan cross grid {i}").type == "MESH"
                             for i in range(23))),
        "sunset": sun.type == "MESH" and
                  all(required(f"Retro sunset dusk stripe {i}").type == "MESH"
                      for i in range(5)) and
                  required("Retro far mountain ridge").type == "MESH" and
                  required("Retro near mountain ridge").type == "MESH",
        "chrome_neon": (chrome.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value > 0.8 and
                        cyan.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value > 2 and
                        pink.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value > 2 and
                        gate.type == "MESH"),
        "coupe": body.parent == car and len(wheels) == 4 and
                 all(wheel.parent == car for wheel in wheels) and
                 all(required(f"Retro red rear light {side}").parent == car
                     for side in (-1, 1)),
        "lighting": all(required(name).type == "LIGHT" for name in
                        ("Retro coral sunset key", "Retro electric cyan car rim",
                         "Retro magenta horizon fill")),
        "camera": cam.type == "CAMERA" and bool(cam.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Retrowave invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        poses[frame] = {"car_y": car.location.y,
                        "wheel_rotation_x": wheels[0].rotation_euler.x,
                        "camera_y": cam.location.y}
    if variant == 2:
        if not (poses[36]["car_y"] > 3.5 and
                poses[72]["car_y"] > 7 and
                poses[72]["wheel_rotation_x"] > 9 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 0.7):
            raise ValueError("Car, wheel, or camera motion changed")
    elif poses[72]["car_y"] > 0.3:
        raise ValueError("Baseline car motion unexpectedly changed")
    return {"variant": variant, "longitudinal_grid": 31,
            "cross_grid": 23, "sun_stripes": 5, "wheels": 4,
            "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited retrowave grid, sun, chrome car, and motion")


if __name__ == "__main__":
    main()
