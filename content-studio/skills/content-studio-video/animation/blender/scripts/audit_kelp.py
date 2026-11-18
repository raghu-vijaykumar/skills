"""Audit underwater biome density, fish school, bubble motion, and palette."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing kelp biome object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    bed = required("SM_Kelp_Silt_Bed")
    school = required("SM_Kelp_Fish_School_Rig")
    bubbles = required("SM_Kelp_Bubble_Rig")
    camera = required("Kelp forest inspection camera")
    kelp = [required(f"SM_Kelp_Blades_Rig_{i}") for i in range(24)]
    blades = [required(f"Kelp blade segment {i} {level}")
              for i in range(24) for level in range(3)]
    coral = [required(f"Kelp orange coral stalk {i}") for i in range(11)]
    fish = [required(f"Kelp amber fish body {i}") for i in range(7)]
    eyes = [required(f"Kelp fish eye {i}") for i in range(7)]
    bubbles_mesh = [required(f"Kelp bubble {i}") for i in range(17)]
    rocks = [required(f"Kelp algae rock {i}") for i in range(14)]
    variant = scene.get("biome_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown kelp biome candidate")
    checks = {
        "climate_recipe": scene.get("biome_recipe") ==
                          "underwater kelp forest, blue filtered light, dense swaying blades, algae rocks, fish, rising bubbles",
        "seabed": bed.type == "MESH" and len(rocks) == 14 and
                  all(rock.type == "MESH" for rock in rocks),
        "plant_density": len(kelp) == 24 and len(blades) == 72 and
                         all(root.get("kelp_stand") == i
                             for i, root in enumerate(kelp)) and
                         all(blades[i * 3 + j].parent == kelp[i]
                             for i in range(24) for j in range(3)),
        "coral": len(coral) == 11,
        "school": school.get("school_count") == 7 and len(fish) == 7 and
                  len(eyes) == 7 and
                  all(obj.parent == school for obj in fish + eyes),
        "bubbles": len(bubbles_mesh) == 17 and
                   all(obj.parent == bubbles for obj in bubbles_mesh),
        "blue_lighting": all(required(name).type == "LIGHT" for name in
                             ("Kelp cyan shallow-water fill", "Kelp filtered-sun shaft")),
        "camera": camera.type == "CAMERA" and bool(camera.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Kelp biome invariants failed: " + ", ".join(failed))
    positions = {}
    for frame in (1, 48, 72):
        scene.frame_set(frame)
        positions[frame] = {"fish_x": school.location.x,
                            "bubble_z": bubbles.location.z,
                            "camera_y": camera.location.y,
                            "kelp_sway": kelp[0].rotation_euler.y}
    if (positions[1]["fish_x"] >= positions[72]["fish_x"] or
            variant == 2 and (positions[72]["fish_x"] < 1.5 or
                              positions[72]["bubble_z"] < 1.1 or
                              positions[72]["camera_y"] > -8.5 or
                              abs(positions[72]["kelp_sway"] -
                                  positions[48]["kelp_sway"]) < 0.1)):
        raise ValueError("Fish, bubbles, kelp, or camera motion changed")
    return {"variant": variant, "kelp_stands": len(kelp),
            "kelp_segments": len(blades), "fish": len(fish),
            "bubbles": len(bubbles_mesh), "positions": positions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited underwater kelp biome, fish, bubbles, and camera glide")


if __name__ == "__main__":
    main()
