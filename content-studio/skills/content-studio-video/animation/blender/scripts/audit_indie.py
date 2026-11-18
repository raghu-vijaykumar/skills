"""Audit one coherent forest-cabin indie horror lane and its failing practical light."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing indie cabin object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    floor = required("SM_Cabin_Forest_Floor")
    cabin = required("SM_Cabin_Timber_Shell")
    door = required("SM_Cabin_Closed_Door")
    pane = required("SM_Cabin_Window_Glow")
    window_light = required("SM_Cabin_Window_Light")
    cam = required("Forest cabin first-person camera")
    flashlight = required("SM_Cabin_Flashlight_Cone")
    fill = required("Cabin cool night fill")
    trees = [required(f"SM_Cabin_Fir_Trunk_{i}") for i in range(30)]
    marks = [required(f"SM_Cabin_Red_Trail_Marker_{i}") for i in range(8)]
    roof = [required(f"Cabin pitched roof side {s}") for s in (-1, 1)]
    variant = scene.get("indie_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown forest cabin candidate")
    checks = {
        "forest_lane": floor.type == "MESH" and cabin.get("forest_lane") == "cabin" and
                       all(tree.get("fir_index") == i for i, tree in enumerate(trees)),
        "cabin_craft": door.type == "MESH" and pane.type == "MESH" and
                       all(obj.type == "MESH" for obj in roof) and
                       len([obj for obj in scene.objects if obj.name.startswith("Cabin front weathered seam ")]) == 8,
        "trail": all(mark.get("route_index") == i for i, mark in enumerate(marks)),
        "first_person": cam.type == "CAMERA" and cam.data.type == "PERSP" and
                        abs(cam.data.lens - 38) < 0.01 and bool(cam.animation_data) and
                        flashlight.type == "LIGHT" and flashlight.data.type == "SPOT" and
                        flashlight.parent == cam and flashlight.data.energy >= 3000,
        "practicals": window_light.type == "LIGHT" and fill.type == "LIGHT" and
                      fill.data.energy >= 400,
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "recipe": scene.get("indie_recipe") ==
                  "first-person cabin forest lane, red path markers, fir silhouettes, failing window, handheld flashlight",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Wrong forest cabin invariants: " + ", ".join(failed))
    if variant == 2 and (not pane.animation_data or not window_light.data.animation_data):
        raise ValueError("The cabin window must fail")
    samples = {}
    for frame in (1, 45, 72):
        scene.frame_set(frame)
        samples[frame] = {"camera_y": cam.location.y,
                          "window_hidden": bool(pane.hide_render),
                          "window_energy": window_light.data.energy}
    if samples[72]["camera_y"] <= samples[1]["camera_y"] or (
            variant == 2 and
            (samples[72]["camera_y"] < -4.5 or
             not samples[45]["window_hidden"] or
             not samples[72]["window_hidden"] or
             samples[72]["window_energy"] > 1)):
        raise ValueError("Cabin approach or practical-light failure changed")
    return {"variant": variant, "fir_trunks": len(trees),
            "trail_markers": len(marks), "roof_slabs": len(roof),
            "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited forest cabin, first-person flashlight, red markers, and failing window")


if __name__ == "__main__":
    main()
