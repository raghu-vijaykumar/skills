"""Audit the station plate, sole interaction cue, rain, and letter lift."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing station object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("narrative_variant")
    if variant not in (1, 2, 3):
        raise ValueError("Unknown narrative candidate")
    letter = required("SM_Narrative_Sealed_Letter")
    seal = required("Station letter seal")
    cue = required("SM_Narrative_Letter_Cue")
    camera = required("Station letter emotional camera")
    drops = [o for o in scene.objects if o.name.startswith("Station rain streak ")]
    checks = {
        "recipe": scene.get("narrative_recipe") ==
                  "rain window plate, lone witness, sealed letter, one late interaction cue, emotional camera push",
        "plate": required("Station wall right").dimensions.x > 4
                 and required("SM_Narrative_Rain_Window").dimensions.x > 4,
        "witness": required("SM_Narrative_Lone_Witness").type == "MESH"
                   and required("Station witness suitcase").type == "MESH",
        "seated_witness": variant != 3 or all(required(f"Station witness {part} {side}").type == "MESH"
                                               for part in ("arm", "leg")
                                               for side in (-1, 1)),
        "bench": required("SM_Narrative_Bench").dimensions.x > 3.7,
        "rain": len(drops) == 8,
        "single_cue": len([o for o in scene.objects if o.name.startswith(
            "SM_Narrative_Letter_Cue")]) == 1 and cue.type == "MESH",
        "letter": letter.type == "MESH" and seal.type == "MESH",
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Narrative invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 42, 72):
        scene.frame_set(frame)
        poses[frame] = {"letter_z": letter.location.z,
                        "seal_z": seal.location.z,
                        "cue_scale": cue.scale.x,
                        "rain_z": drops[0].location.z,
                        "camera_y": camera.location.y}
    if variant in (2, 3):
        if not (poses[1]["cue_scale"] < 0.05 and
                poses[42]["cue_scale"] > 0.75 and
                poses[72]["letter_z"] > poses[1]["letter_z"] + 0.4 and
                abs((poses[72]["seal_z"] - poses[1]["seal_z"]) -
                    (poses[72]["letter_z"] - poses[1]["letter_z"])) < 0.01 and
                poses[72]["rain_z"] < poses[1]["rain_z"] - 0.45 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 1):
            raise ValueError("Station cue, rain, camera, or letter motion changed")
    elif (poses[72]["letter_z"] > poses[1]["letter_z"] + 0.02 or
          poses[72]["cue_scale"] > 0.05):
        raise ValueError("Baseline station candidate unexpectedly changed")
    return {"variant": variant, "rain_streaks": len(drops), "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited narrative station plate, cue, letter, rain, and camera")


if __name__ == "__main__":
    main()
