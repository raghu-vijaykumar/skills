"""Audit repeated empty pool bays, fluorescent motion, and water treatment."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing liminal pool object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    floor = required("SM_Pool_Hall_Floor")
    water = required("SM_Pool_Water")
    opening = required("SM_Pool_Far_Opening")
    cam = required("Liminal pool inspection camera")
    bays = [required(f"SM_Pool_Bay_{i}_Lintel") for i in range(5)]
    pillars = [required(f"SM_Pool_Bay_{i}_Pillar_{side}")
               for i in range(5) for side in (-1, 1)]
    tubes = [required(f"SM_Pool_Fluorescent_{i}") for i in range(5)]
    lights = [required(f"Pool fluorescent area {i}") for i in range(5)]
    glints = [required(f"Pool water glint {i}") for i in range(9)]
    variant = scene.get("liminal_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown poolrooms candidate")
    shader = bpy.data.materials["Poolrooms glossy shallow water"].node_tree.nodes[
        "Principled BSDF"]
    checks = {
        "empty_stage": floor.type == "MESH" and opening.type == "MESH" and
                       not any(obj.name.startswith(("Hand ", "Tape ", "Cosmic "))
                               for obj in scene.objects),
        "modular_bays": all(bay.get("repeated_module") == i for i, bay in
                            enumerate(bays)) and
                        all(pillar.get("repeated_module") is not None for pillar in pillars),
        "fluorescents": all(tube.get("fluorescent_bay") == i for i, tube in
                            enumerate(tubes)) and all(obj.type == "LIGHT" for obj in lights),
        "water": water.dimensions.x > 3 and
                 shader.inputs["Coat Weight"].default_value >= 0.6 and
                 shader.inputs["Transmission Weight"].default_value >= 0.1,
        "camera": cam.type == "CAMERA" and cam.data.type == "PERSP" and
                  abs(cam.data.lens - 34) < 0.01 and bool(cam.animation_data),
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
        "recipe": scene.get("liminal_recipe") ==
                  "empty modular poolrooms, repeated bays, fluorescent wrongness, endless opening",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Wrong liminal pool invariants: " + ", ".join(failed))
    if variant == 2 and (not lights[2].data.animation_data or
                         any(not glint.animation_data for glint in glints)):
        raise ValueError("The fluorescent or water glints are static")
    samples = {}
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        samples[frame] = {"camera_y": cam.location.y,
                          "bay_2_light_energy": lights[2].data.energy,
                          "first_glint_y": glints[0].location.y}
    if (samples[1]["camera_y"] >= samples[72]["camera_y"] or
            (variant == 2 and
             (samples[72]["camera_y"] <= -5.0 or
              samples[36]["bay_2_light_energy"] >= samples[1]["bay_2_light_energy"] or
              samples[72]["first_glint_y"] <= samples[1]["first_glint_y"]))):
        raise ValueError("Slow push, fluorescent failure, or glint travel changed")
    return {"variant": variant, "bay_lintels": len(bays),
            "bay_pillars": len(pillars), "fluorescent_tubes": len(tubes),
            "water_glints": len(glints), "people_or_props": 0,
            "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited empty modular pool, fluorescent failure, water glints, and camera push")


if __name__ == "__main__":
    main()
