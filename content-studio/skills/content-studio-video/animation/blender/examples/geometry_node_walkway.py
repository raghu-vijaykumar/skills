"""A Geometry Nodes walkway kit assembled into a short drone traversal shot."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, material, reset_scene, sphere


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def place(obj, collection):
    # Explicit outliner ownership keeps the modular kit separate from hero motion.
    for owner in tuple(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def node_group(name, count, post_mat, glow_mat):
    group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    group.interface.new_socket(name="Geometry", in_out="INPUT",
                               socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry", in_out="OUTPUT",
                               socket_type="NodeSocketGeometry")
    nodes = group.nodes
    links = group.links
    output = nodes.new("NodeGroupOutput")
    line = nodes.new("GeometryNodeMeshLine")
    line.name = "Parametric post line"
    line.inputs["Count"].default_value = count
    line.inputs["Offset"].default_value = (0.82, 0, 0)
    body = nodes.new("GeometryNodeMeshCube")
    body.name = "Modular post master"
    body.inputs["Size"].default_value = (0.16, 0.16, 1.03)
    body_mat = nodes.new("GeometryNodeSetMaterial")
    body_mat.inputs["Material"].default_value = post_mat
    links.new(body.outputs["Mesh"], body_mat.inputs["Geometry"])
    light = nodes.new("GeometryNodeMeshCube")
    light.name = "Modular cyan cap"
    light.inputs["Size"].default_value = (0.25, 0.25, 0.13)
    transform = nodes.new("GeometryNodeTransform")
    transform.inputs["Translation"].default_value = (0, 0, 0.58)
    links.new(light.outputs["Mesh"], transform.inputs["Geometry"])
    light_mat = nodes.new("GeometryNodeSetMaterial")
    light_mat.inputs["Material"].default_value = glow_mat
    links.new(transform.outputs["Geometry"], light_mat.inputs["Geometry"])
    join = nodes.new("GeometryNodeJoinGeometry")
    links.new(body_mat.outputs["Geometry"], join.inputs["Geometry"])
    links.new(light_mat.outputs["Geometry"], join.inputs["Geometry"])
    instance = nodes.new("GeometryNodeInstanceOnPoints")
    links.new(line.outputs["Mesh"], instance.inputs["Points"])
    links.new(join.outputs["Geometry"], instance.inputs["Instance"])
    realize = nodes.new("GeometryNodeRealizeInstances")
    links.new(instance.outputs["Instances"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], output.inputs["Geometry"])
    return group


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown node walkway candidate")
    scene = reset_scene(spec, background=(0.025, 0.044, 0.068))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.48
    stage_mat = material("GN slate stage", (0.07, 0.10, 0.15), roughness=0.82)
    deck_mat = material("GN steel walkway", (0.23, 0.29, 0.33),
                        metallic=0.32, roughness=0.55)
    post_mat = material("GN dark post master", (0.10, 0.15, 0.20),
                        metallic=0.34, roughness=0.52)
    cyan = material("GN cyan post cap", (0.06, 0.69, 0.92),
                    emission=(0.02, 0.67, 0.91), emission_strength=1.15)
    amber = material("GN amber drone", (0.91, 0.51, 0.13),
                     metallic=0.37, roughness=0.35)
    gate_mat = material("GN gate blue steel", (0.18, 0.39, 0.50),
                        metallic=0.46, roughness=0.46)
    collections = {}
    for suffix in ("Stage", "Procedural", "Hero", "Lights"):
        col = bpy.data.collections.new(f"COL_GN_Walkway_{suffix}")
        scene.collection.children.link(col)
        collections[suffix] = col
    place(cube("SM_GN_Walkway_Stage", (0, 0, -0.25),
               (10.2, 5.0, 0.48), stage_mat, edge=0.10), collections["Stage"])
    place(cube("SM_GN_Walkway_Deck", (0, 0, 0.02),
               (9.38, 2.14, 0.10), deck_mat, edge=0.035), collections["Stage"])
    for y in (-1.72, 1.72):
        bpy.ops.mesh.primitive_cube_add(size=0.02, location=(-3.69, y, 0.51))
        obj = bpy.context.object
        obj.name = f"SM_GN_Post_Row_{'near' if y < 0 else 'far'}"
        modifier = obj.modifiers.new("Procedural repeated post kit", "NODES")
        modifier.node_group = node_group(f"GN_Post_Kit_{'near' if y < 0 else 'far'}",
                                         4 if variant == 1 else 10,
                                         post_mat, cyan)
        place(obj, collections["Procedural"])
    # A two-leaf gate makes the traversal beat readable beyond the repeated kit.
    for side in (-1, 1):
        y = side * 0.47
        door = place(cube(f"SM_GN_Gate_Door_{side}", (4.35, y, 0.75),
                          (0.23, 0.90, 1.43), gate_mat, edge=0.04),
                     collections["Stage"])
        if variant == 2:
            # Retraction reads as an opening from the nearly top-down overview.
            key(door, "scale", ((1, (1, 1, 1)),
                                  (41, (1, 1, 1)),
                                  (62, (1, 0.08, 0.08)),
                                  (72, (1, 0.08, 0.08))))
    place(cube("GN gate lintel", (4.35, 0, 1.59),
               (0.36, 2.80, 0.15), gate_mat, edge=0.03), collections["Stage"])
    drone = place(sphere("SM_GN_Traveler_Drone", (-3.50, 0, 0.73),
                         0.36, amber, segments=20, rings=12,
                         scale=(1.35, 0.76, 0.55)), collections["Hero"])
    place(cube("GN drone cyan eye", (-3.07, -0.03, 0.75),
               (0.07, 0.30, 0.16), cyan, edge=0.02), collections["Hero"])
    if variant == 2:
        key(drone, "location", ((1, (-3.50, 0, 0.73)),
                                (38, (0.12, 0, 0.73)),
                                (70, (3.43, 0, 0.73)),
                                (72, (3.43, 0, 0.73))))
        eye = bpy.data.objects["GN drone cyan eye"]
        key(eye, "location", ((1, (-3.07, -0.03, 0.75)),
                              (38, (0.55, -0.03, 0.75)),
                              (70, (3.86, -0.03, 0.75)),
                              (72, (3.86, -0.03, 0.75))))
    key_light = area_light("GN walkway warm key", (-3.6, -4.2, 6), 1100, 4.0,
                           color=(1.0, 0.75, 0.48), target=(0, 0, 0.6))
    fill_light = area_light("GN walkway cool fill", (4.2, 2.8, 5.8), 890, 4.4,
                            color=(0.42, 0.76, 1.0), target=(2.0, 0, 0.7))
    place(key_light, collections["Lights"])
    place(fill_light, collections["Lights"])
    place(camera("GN walkway overview camera", (0, -8.9, 7.8),
                 (0, 0, 0.45), ortho=10.6), collections["Lights"])
    scene["gn_recipe"] = "reusable geometry-node post kit in organized walkway collections with a gate traversal"
    scene["gn_variant"] = variant
    return scene
