"""Audit the abandoned fuel stop's collapse, salvage, and moving hauler."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing wasteland object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    canopy = required("SM_Waste_Fuel_Canopy")
    broken = required("SM_Waste_Canopy_Broken_Column")
    brace = required("SM_Waste_Improvised_Brace")
    pump = required("SM_Waste_Fuel_Pump")
    sign = required("SM_Waste_Faded_Sign")
    road = required("SM_Waste_Cracked_Road")
    cart = required("SM_Waste_Scavenger_Cart_Rig")
    gust = required("SM_Waste_Dust_Gust_Rig")
    camera = required("Wasteland station inspection camera")
    wheels = [required(f"Waste cart tire {side} {fore}")
              for side in (-1, 1) for fore in (-1, 1)]
    hubs = [required(f"Waste cart iron hub {side} {fore}")
            for side in (-1, 1) for fore in (-1, 1)]
    supports = [required(f"Waste cart tarp support {side} {fore}")
                for side in (-1, 1) for fore in (-1, 1)]
    plates = [required(f"Waste cart repair plate {i}") for i in range(3)]
    dust = [required(f"Waste windblown dust streak {i}") for i in range(18)]
    variant = scene.get("apocalypse_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown apocalypse candidate")
    checks = {
        "collapse_lane": scene.get("apocalypse_recipe") ==
                         "post-apoc roadside collapse, faded fictional fuel sign, rust patches, improvised brace, scavenger cart, dust",
        "canopy": canopy.get("collapsed_station") is True and
                  broken.rotation_euler.y > 0.15 and brace.rotation_euler.y < -0.30 and
                  len([o for o in scene.objects if o.name.startswith(
                      "Waste roof rust patch ")]) == 5,
        "faded_brand": sign.type == "MESH" and
                       all(required(f"Waste erased sign mark {i}") for i in range(3)),
        "pump": pump.type == "MESH" and
                all(required(f"Waste pump hose segment {i}") for i in range(3)),
        "scavenged_cart": cart.get("scavenged_transport") ==
                           "patched four-wheel fuel hauler" and len(wheels) == 4 and
                           len(hubs) == 4 and len(supports) == 4 and
                           len(plates) == 3 and
                           all(obj.parent == cart for obj in wheels + hubs + supports + plates),
        "dust": len(dust) == 18 and all(obj.parent == gust for obj in dust),
        "material": bpy.data.materials["Wasteland oxidized steel"].node_tree.nodes[
                    "Principled BSDF"].inputs["Roughness"].default_value >= 0.85,
        "environment": road.type == "MESH" and
                       required("SM_Waste_Desert").type == "MESH",
        "camera": camera.type == "CAMERA" and bool(camera.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Wasteland station invariants failed: " + ", ".join(failed))
    positions = {}
    for frame in (1, 48, 72):
        scene.frame_set(frame)
        positions[frame] = {"cart_x": cart.location.x,
                            "dust_x": gust.location.x,
                            "camera_y": camera.location.y}
    if (positions[1]["cart_x"] >= positions[72]["cart_x"] or
            variant == 2 and (positions[72]["cart_x"] < 0.3 or
                              positions[72]["dust_x"] < 4.4 or
                              positions[72]["camera_y"] > -11.2)):
        raise ValueError("Scavenger crossing or wind sweep changed")
    return {"variant": variant, "cart_wheels": len(wheels),
            "tarp_supports": len(supports),
            "repair_plates": len(plates), "dust_streaks": len(dust),
            "positions": positions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited collapsed fuel stop, repair cart, faded mark, and wind sweep")


if __name__ == "__main__":
    main()
