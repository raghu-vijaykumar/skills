"""Audit circuit lanes, stadium kit, team vehicles, and finish order."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing circuit object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("circuit_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown circuit candidate")
    blue = required("SM_Circuit_Cyan_Car_Rig")
    red = required("SM_Circuit_Red_Car_Rig")
    bays = [o for o in scene.objects if o.name.startswith("Circuit grandstand bay ")]
    squares = [o for o in scene.objects if o.name.startswith("Circuit checker ")]
    checks = {
        "recipe": scene.get("circuit_recipe") ==
                  "clear track edges, checker finish, seven modular stands, pit landmark, cyan and red teams",
        "track": required("SM_Circuit_Track").dimensions.x > 10.5,
        "finish": len(squares) == 8 and required("SM_Circuit_Finish_Marker").location.z > 2.5,
        "stadium": len(bays) == 7 and required("SM_Circuit_Grandstand").type == "MESH"
                   and required("SM_Circuit_Pit_Tower").type == "MESH",
        "edges": required("Circuit yellow track edge -2.43").type == "MESH"
                 and required("Circuit yellow track edge 1.37").type == "MESH",
        "wheels": all(len([o for o in scene.objects if o.name.startswith(
            name + " wheel ") and o.parent == rig]) == 4
            for name, rig in (("SM_Circuit_Cyan_Car_Rig", blue),
                              ("SM_Circuit_Red_Car_Rig", red))),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Circuit invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 42, 56, 57, 58, 60, 72):
        scene.frame_set(frame)
        poses[frame] = {"cyan_center_x": -4.10 + blue.location.x,
                        "red_center_x": -3.52 + red.location.x}
    if variant == 2:
        # Check the crossing state, not only an end frame after both cars finish.
        if not (poses[1]["cyan_center_x"] < poses[1]["red_center_x"] and
                poses[42]["cyan_center_x"] > poses[42]["red_center_x"] and
                poses[57]["cyan_center_x"] > 2.55 and
                poses[57]["red_center_x"] < 2.55 and
                poses[72]["cyan_center_x"] > poses[72]["red_center_x"]):
            raise ValueError(f"Cyan overtaking and first finish changed: {poses}")
    elif (poses[72]["cyan_center_x"] > -3.7 or
          poses[72]["red_center_x"] > -3.2):
        raise ValueError("Baseline circuit action unexpectedly changed")
    return {"variant": variant, "grandstand_bays": len(bays),
            "checker_squares": len(squares), "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited circuit, cars, stands, and finish order")


if __name__ == "__main__":
    main()
