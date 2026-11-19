"""A reversible beauty grade and restrained fog glow on the scored neon alley."""

from pathlib import Path

import bpy

import cyberpunk_alley


def make_scene(spec, spec_dir: Path):
    variant = int(spec.get("variant", 2))
    if variant not in (1, 2):
        raise ValueError("Unknown compositor comparison candidate")
    # Keep base geometry, camera, lights, and drone action identical so the
    # before/after render isolates what the compositor graph contributes.
    base_spec = {**spec, "variant": 2}
    scene = cyberpunk_alley.make_scene(base_spec, spec_dir)
    scene["composite_variant"] = variant
    scene.view_layers[0].use_pass_mist = True
    scene.use_nodes = True
    tree = bpy.data.node_groups.new("NG_Cyber_Beauty_Composite", "CompositorNodeTree")
    scene.compositing_node_group = tree
    # Blender 5 replaced the Composite node with a color Group Output socket.
    tree.interface.new_socket(name="Image", in_out="OUTPUT",
                              socket_type="NodeSocketColor")
    nodes, links = tree.nodes, tree.links
    source = nodes.new("CompositorNodeRLayers")
    source.name = "IN_Cyber_Combined"
    source.location = (-600, 0)
    output = nodes.new("NodeGroupOutput")
    output.name = "OUT_Cyber_Beauty"
    output.location = (450, 0)
    if variant == 1:
        links.new(source.outputs["Image"], output.inputs["Image"])
        return scene
    exposure = nodes.new("CompositorNodeExposure")
    exposure.name = "Exposure correction"
    exposure.inputs["Exposure"].default_value = -0.10
    exposure.location = (-350, 0)
    hue = nodes.new("CompositorNodeHueSat")
    hue.name = "Neon saturation trim"
    hue.inputs["Saturation"].default_value = 1.06
    hue.location = (-100, 0)
    glare = nodes.new("CompositorNodeGlare")
    glare.name = "Practical-neon fog glow"
    glare.inputs["Type"].default_value = "Fog Glow"
    glare.inputs["Threshold"].default_value = 0.70
    glare.inputs["Strength"].default_value = 1.0
    glare.inputs["Size"].default_value = 0.85
    glare.location = (150, 0)
    links.new(source.outputs["Image"], exposure.inputs["Image"])
    links.new(exposure.outputs["Image"], hue.inputs["Image"])
    links.new(hue.outputs["Image"], glare.inputs["Image"])
    links.new(glare.outputs["Image"], output.inputs["Image"])
    scene["composite_recipe"] = "AgX view, -0.10 exposure, 1.06 saturation, fog glow threshold 0.70 strength 1.0"
    return scene
