"""Audit the repeated Geometry Nodes kit, collection layout, and gate traversal."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing node-walkway object: {name}")
    return obj


def audit():
    scene = bpy.context.scene
    variant = scene.get("gn_variant")
    if variant not in (1, 2):
        raise ValueError("Unknown node-walkway candidate")
    rows = [required(f"SM_GN_Post_Row_{name}") for name in ("near", "far")]
    counts = []
    node_checks = []
    for row in rows:
        modifier = next((m for m in row.modifiers if m.type == "NODES"), None)
        if modifier is None or modifier.node_group is None:
            raise ValueError("Missing Geometry Nodes post kit")
        nodes = modifier.node_group.nodes
        line = next((n for n in nodes if n.bl_idname == "GeometryNodeMeshLine"), None)
        counts.append(int(line.inputs["Count"].default_value) if line else 0)
        node_checks.append({n.bl_idname for n in nodes} >= {
            "GeometryNodeMeshLine", "GeometryNodeInstanceOnPoints",
            "GeometryNodeRealizeInstances", "GeometryNodeSetMaterial"})
    drone = required("SM_GN_Traveler_Drone")
    eye = required("GN drone cyan eye")
    doors = [required(f"SM_GN_Gate_Door_{side}") for side in (-1, 1)]
    expected_collections = {f"COL_GN_Walkway_{name}" for name in
                            ("Stage", "Procedural", "Hero", "Lights")}
    checks = {
        "recipe": scene.get("gn_recipe") ==
                  "reusable geometry-node post kit in organized walkway collections with a gate traversal",
        "node_graph": all(node_checks) and counts == [4 if variant == 1 else 10] * 2,
        "assembly": expected_collections <= {c.name for c in scene.collection.children} and
                    all(any(c.name == "COL_GN_Walkway_Procedural"
                            for c in row.users_collection) for row in rows) and
                    any(c.name == "COL_GN_Walkway_Hero"
                        for c in drone.users_collection),
        "stage": required("SM_GN_Walkway_Deck").dimensions.x > 9 and
                 len(doors) == 2 and eye.type == "MESH",
        "delivery": (scene.render.resolution_x, scene.render.resolution_y,
                     scene.render.fps, scene.frame_end) == (960, 540, 24, 72),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError("Node-walkway invariants failed: " + ", ".join(failed))
    poses = {}
    for frame in (1, 38, 72):
        scene.frame_set(frame)
        poses[frame] = {"drone_x": drone.location.x,
                        "gate_scale_y": doors[0].scale.y}
    if variant == 2:
        if not (poses[1]["drone_x"] < -3.4 and
                abs(poses[38]["drone_x"]) < 0.2 and
                poses[72]["drone_x"] > 3.3 and
                poses[1]["gate_scale_y"] == 1 and
                poses[72]["gate_scale_y"] < 0.1):
            raise ValueError("Drone traversal or gate retraction changed")
    elif (poses[72]["drone_x"] > -3.4 or
          poses[72]["gate_scale_y"] < 0.9):
        raise ValueError("Baseline node walkway unexpectedly animates")
    return {"variant": variant, "post_counts": counts,
            "collections": sorted(expected_collections), "poses": poses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited Geometry Nodes instances, outliner assembly, drone, and gate")


if __name__ == "__main__":
    main()
