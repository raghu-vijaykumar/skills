"""Audit felt craft, plastic gaze, children's-show stage, and sick-light performance."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing puppet object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    body = required("SM_Puppet_Felt_Body")
    head = required("SM_Puppet_Felt_Head")
    pupils = [required(f"SM_Puppet_Black_Pupil_{s}") for s in (-1, 1)]
    eyes = [required(f"SM_Puppet_Plastic_Eye_{s}") for s in (-1, 1)]
    curtains = [required(f"SM_Puppet_Curtain_{s}") for s in (-1, 1)]
    banner = required("SM_Puppet_Show_Banner")
    light = required("SM_Puppet_Sick_Light")
    warm = required("Puppet cheerful key")
    cam = required("Puppet stage camera")
    root = required("Puppet Pip pose control")
    variant = scene.get("puppet_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown puppet candidate")
    felt = bpy.data.materials["Pip golden felt"]
    plastic = bpy.data.materials["Pip hard plastic eyes"]
    checks = {
        "felt_foam": body.type == "MESH" and head.type == "MESH" and
                     felt.get("felt_fiber") is True and
                     len([o for o in scene.objects if o.name.startswith("SM_Puppet_Foam_Arm_")]) == 2,
        "plastic_eyes": all(obj.type == "MESH" for obj in pupils + eyes) and
                        plastic.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value < 0.2,
        "fixed_smile": len([o for o in scene.objects if o.name.startswith("Puppet smile stitch ")]) == 9,
        "show_stage": all(obj.type == "MESH" for obj in curtains) and
                      banner.type == "FONT" and banner.data.body == "PIP SAYS HELLO!",
        "light_cues": light.type == "LIGHT" and warm.type == "LIGHT",
        "camera": cam.type == "CAMERA" and bool(cam.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "recipe": scene.get("puppet_recipe") ==
                  "felt foam friend, hard plastic eyes, cheerful children show, sick green shift",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Wrong puppet invariants: " + ", ".join(failed))
    if variant == 2 and (not pupils[1].animation_data or
                         not light.data.animation_data or not warm.data.animation_data):
        raise ValueError("The wrong gaze or sick light is static")
    samples = {}
    for frame in (1, 43, 72):
        scene.frame_set(frame)
        samples[frame] = {"pupil_x": pupils[1].location.x,
                          "sick_energy": light.data.energy,
                          "warm_energy": warm.data.energy,
                          "head_turn": root.rotation_euler.z,
                          "camera_y": cam.location.y}
    if variant == 2 and (samples[72]["pupil_x"] <= samples[1]["pupil_x"] + 0.10 or
                         samples[72]["sick_energy"] <= samples[1]["sick_energy"] + 400 or
                         samples[72]["warm_energy"] >= samples[1]["warm_energy"] or
                         samples[72]["head_turn"] <= 0.1):
        raise ValueError("The cheerful stage does not turn wrong")
    return {"variant": variant, "felt_body_and_head": 2,
            "plastic_eyes": len(eyes), "curtains": len(curtains),
            "smile_stitches": 9, "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited felt puppet, plastic eyes, show set, fixed smile, and sick light")


if __name__ == "__main__":
    main()
