"""Audit the oversized toy, empty play space, impossible door, and dream actions."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing dream playground object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    field = required("SM_Dream_Empty_Playground")
    block = required("SM_Dream_Giant_Alphabet_Block")
    label = required("SM_Dream_Block_Letter_A")
    chair = required("SM_Dream_Empty_Chair_Seat")
    door = required("SM_Dream_Impossible_Door")
    void = required("SM_Dream_Sky_Door_Void")
    control = required("Dream alphabet block float control")
    hinge = required("Dream sky door hinge")
    cam = required("Dream playground camera")
    walls = [required(f"Dream isolated nursery wall {i}") for i in range(4)]
    stars = [required(f"Dream impossible hanging star {i}") for i in range(8)]
    variant = scene.get("dream_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown dream candidate")
    checks = {
        "empty_play_space": field.type == "MESH" and chair.type == "MESH" and
                            len(walls) == 4 and len(stars) == 8,
        "oversized_childhood_object": block.get("childhood_scale_exaggerated") is True and
                                      min(block.dimensions) > 2 and label.type == "FONT" and
                                      label.data.body == "A",
        "unsupported_door": door.get("unsupported_sky_door") is True and
                            void.type == "MESH" and door.matrix_world.translation.z > 2,
        "camera": cam.type == "CAMERA" and bool(cam.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "recipe": scene.get("dream_recipe") ==
                  "pastel childhood block, empty toy chair, disconnected nursery, unsupported sky door",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Wrong dream playground invariants: " + ", ".join(failed))
    if not control.animation_data or not hinge.animation_data:
        raise ValueError("Dream objects have no keyed actions")
    samples = {}
    for frame in (1, 50, 72):
        scene.frame_set(frame)
        samples[frame] = {"block_z": control.location.z,
                          "door_open_radians": hinge.rotation_euler.z,
                          "camera_y": cam.location.y}
    if (samples[72]["block_z"] <= samples[1]["block_z"] or
            samples[72]["door_open_radians"] <= samples[1]["door_open_radians"] or
            variant == 2 and (samples[72]["block_z"] < 2 or
                              samples[72]["door_open_radians"] < 1)):
        raise ValueError("Levitation or impossible door reveal changed")
    return {"variant": variant, "disconnected_walls": len(walls),
            "hanging_stars": len(stars), "oversized_blocks": 1,
            "empty_chair": 1, "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited empty play space, oversized toy, sky door, and keyed levitation")


if __name__ == "__main__":
    main()
