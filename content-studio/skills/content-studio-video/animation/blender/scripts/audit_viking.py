"""Audit the Viking lane's period cues, hull, sail, and crossing motion."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing Viking object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    ship = required("SM_Viking_Longship_Rig")
    hull = required("SM_Viking_Clinker_Hull")
    sail = required("SM_Viking_Wool_Square_Sail")
    mast = required("SM_Viking_Timber_Mast")
    sea = required("SM_Viking_Fjord_Water")
    cam = required("Viking fjord inspection camera")
    shields = [required(f"Viking round shield {side} {i}")
               for side in (-1, 1) for i in range(6)]
    oars = [required(f"Viking rowing oar {side} {i}")
            for side in (-1, 1) for i in range(4)]
    strakes = [required(f"Viking clinker strake {side} {level}")
               for side in (-1, 1) for level in range(3)]
    stripes = [required(f"Viking red sail stripe {i}") for i in range(4)]
    variant = scene.get("historical_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown Viking candidate")
    checks = {
        "period": scene.get("historical_period") ==
                  "circa ninth to eleventh century Scandinavia" and
                  scene.get("historical_recipe") ==
                  "Viking longship with narrow keel, clinker strakes, round shields, oars, wool square sail",
        "hull": hull.get("period_hull") == "raised-end narrow-keel longship" and
                hull.parent == ship and len(hull.data.vertices) >= 12 and
                len(strakes) == 6 and all(s.parent == ship for s in strakes),
        "sail": sail.parent == ship and mast.parent == ship and
                len(stripes) == 4 and all(panel.parent == ship for panel in stripes),
        "shield_line": len(shields) == 12 and all(shield.parent == ship for shield in shields),
        "rowing": len(oars) == 8 and all(oar.parent == ship for oar in oars),
        "materials": all(bpy.data.materials[name].node_tree.nodes[
                     "Principled BSDF"].inputs["Roughness"].default_value >= 0.85
                     for name in ("Viking tarred oak timber", "Viking undyed wool sail",
                                  "Viking madder dyed wool")),
        "environment": sea.type == "MESH" and
                       len([o for o in scene.objects if o.name.startswith(
                           "Viking distant rocky shore ")]) == 7,
        "camera": cam.type == "CAMERA" and bool(cam.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "no_horned_helmet": not any("helmet" in o.name.lower() for o in scene.objects),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Viking historical lane invariants failed: " + ", ".join(failed))
    positions = {}
    for frame in (1, 48, 72):
        scene.frame_set(frame)
        positions[frame] = {"ship_x": ship.location.x,
                            "camera_y": cam.location.y,
                            "camera_heading": cam.rotation_euler.z}
    if (positions[1]["ship_x"] >= positions[72]["ship_x"] or
            variant == 2 and (positions[72]["ship_x"] < 1.5 or
                              positions[72]["camera_y"] > -9.4 or
                              abs(positions[72]["camera_heading"] -
                                  positions[1]["camera_heading"]) < 0.05)):
        raise ValueError("Longship crossing or camera follow changed")
    return {"variant": variant, "shields": len(shields), "oars": len(oars),
            "strakes": len(strakes), "sail_stripes": len(stripes),
            "positions": positions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited Viking longship period, hull, sail, shields, and crossing")


if __name__ == "__main__":
    main()
