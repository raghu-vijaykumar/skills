"""Audit the ruined causeway, bonfire landmark, fog gate, and threat reveal."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing soulslike object: {name}")
    return obj


def local_height(obj):
    # Mesh-local height remains measurable while the concealed enemy rig is scaled to zero.
    return max(point[2] for point in obj.bound_box) - min(point[2] for point in obj.bound_box)


def audit():
    scene = bpy.context.scene
    variant = scene.get("soulslike_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown soulslike candidate")
    flame = required("SM_Soulslike_Bonfire_Flame")
    left = required("SM_Soulslike_Fog_Gate_Left")
    right = required("SM_Soulslike_Fog_Gate_Right")
    hero = required("SM_Soulslike_Traveler_Rig")
    enemy = required("SM_Soulslike_Red_Enemy_Rig")
    cam = required("Soulslike ruined-causeway camera")
    columns = [o for o in scene.objects if o.name.startswith(
        "SM_Soulslike_Broken_Column_")]
    checks = {
        "recipe": scene.get("soulslike_recipe") ==
                  "weathered monumental ruin, warm bonfire landmark, pale fog gate, clear crimson enemy silhouette",
        "causeway": required("SM_Soulslike_Ruined_Causeway").dimensions.x > 9.9,
        "monumental_ruin": (len(columns) == 3 and
                             all(o.dimensions.z > 3.4 for o in columns) and
                             required("SM_Soulslike_Monumental_Fog_Arch").location.z > 3.6),
        "bonfire": (required("SM_Soulslike_Bonfire_Hearth").type == "MESH" and
                     flame.type == "MESH" and
                     len([o for o in scene.objects if o.name.startswith(
                         "Soulslike bonfire wood")]) == 3),
        "fog_gate": (left.active_material == right.active_material and
                     required("Soulslike fog arch upright -1.48").type == "MESH" and
                     required("Soulslike fog arch upright 1.48").type == "MESH"),
        "lethal_silhouette": (required("SM_Soulslike_Red_Enemy_Torso").parent == enemy and
                              required("SM_Soulslike_Red_Enemy_Blade").parent == enemy and
                              required("SM_Soulslike_Traveler_Body").parent == hero and
                              local_height(required("SM_Soulslike_Red_Enemy_Torso")) >
                              local_height(required("SM_Soulslike_Traveler_Body"))),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Soulslike invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 42, 63, 72):
        scene.frame_set(frame)
        poses[frame] = {"hero_x": hero.location.x,
                        "gate_left_y": left.location.y,
                        "gate_right_y": right.location.y,
                        "enemy_scale": enemy.scale.x,
                        "fire_scale": flame.scale.x,
                        "camera_y": cam.location.y}
    if variant == 2:
        if not (poses[1]["enemy_scale"] < 0.05 and
                poses[42]["hero_x"] > 1.2 and
                poses[63]["gate_left_y"] < -1.5 and
                poses[63]["gate_right_y"] > 1.5 and
                poses[72]["hero_x"] > 4.5 and
                poses[72]["enemy_scale"] > 0.95 and
                poses[72]["camera_y"] > poses[1]["camera_y"] + 0.7):
            raise ValueError("Bonfire approach, fog opening, or enemy reveal changed")
    elif (poses[72]["hero_x"] > 0.2 or poses[72]["enemy_scale"] > 0.05 or
          poses[72]["gate_left_y"] < -0.8):
        raise ValueError("Baseline soulslike action unexpectedly changed")
    return {"variant": variant, "ruin_columns": 3, "bonfire_wood": 3,
            "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited soulslike ruin, landmark, gate, and threat reveal")


if __name__ == "__main__":
    main()
