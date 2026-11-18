"""Audit one coherent cyberpunk lane and its parcel-drone crossing."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing cyberpunk object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    towers = [required(f"SM_Cyber_Tower_{side}_{bay}")
              for side in (-1, 1) for bay in range(6)]
    spines = [required(f"Cyber facade neon spine {side} {bay}")
              for side in (-1, 1) for bay in range(6)]
    rails = [required(f"Cyber window rail {side} {bay} {level}")
             for side in (-1, 1) for bay in range(6) for level in range(3)]
    rotors = [required(f"Cyber drone rotor {side} {fore}")
              for side in (-1, 1) for fore in (-1, 1)]
    rig = required("SM_Cyber_Courier_Drone_Rig")
    parcel = required("Cyber courier parcel")
    camera = required("Cyberpunk alley inspection camera")
    sign = required("SM_Cyber_Suspended_Sign")
    street = required("SM_Cyber_Street")
    variant = scene.get("cyberpunk_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown cyberpunk candidate")
    checks = {
        "single_lane": scene.get("cyberpunk_recipe") ==
                       "single cyberpunk lane, wet charcoal street, cyan and magenta neon, courier drone",
        "street": street.type == "MESH" and
                  bpy.data.materials["Alley wet charcoal asphalt"].node_tree.nodes[
                      "Principled BSDF"].inputs["Roughness"].default_value <= 0.25,
        "architecture": len(towers) == 12 and len(spines) == 12 and len(rails) == 36 and
                        all(tower.get("cyber_bay") is not None for tower in towers),
        "neon": all(bpy.data.materials[name].node_tree.nodes[
                    "Principled BSDF"].inputs["Emission Strength"].default_value >= 3
                    for name in ("Alley cyan neon", "Alley magenta neon")),
        "courier": rig.get("courier_lane") == "cyberpunk" and
                   parcel.parent == rig and len(rotors) == 4 and
                   all(rotor.parent == rig for rotor in rotors),
        "sign": sign.type == "MESH" and all(required(f"Cyber sign glyph {i}")
                                               for i in range(5)),
        "camera": camera.type == "CAMERA" and bool(camera.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Cyberpunk lane invariants failed: " + ", ".join(failed))
    positions = {}
    for frame in (1, 48, 72):
        scene.frame_set(frame)
        positions[frame] = {"drone_x": rig.location.x,
                            "drone_z": rig.location.z,
                            "camera_y": camera.location.y}
    if (positions[1]["drone_x"] >= positions[72]["drone_x"] or
            variant == 2 and (positions[72]["drone_x"] < 2.0 or
                              positions[72]["camera_y"] > -9.6)):
        raise ValueError("Drone traverse or inspection push changed")
    return {"variant": variant, "towers": len(towers), "neon_spines": len(spines),
            "window_rails": len(rails), "drone_rotors": len(rotors),
            "positions": positions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited cyberpunk architecture, neon, courier drone, and motion")


if __name__ == "__main__":
    main()
