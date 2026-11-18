"""Original low-resolution PSX-inspired corridor with nearest-sampled atlas and CRT."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, material, reset_scene


def to_collection(obj, collection):
    for previous in list(obj.users_collection):
        previous.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def limited_atlas():
    """Generate a tiny deterministic, nearest-sampled stain atlas without external art."""
    image = bpy.data.images.new("PSX 64px wall atlas", width=64, height=64)
    palette = ((0.07, 0.10, 0.08), (0.095, 0.125, 0.10),
               (0.12, 0.145, 0.11), (0.055, 0.08, 0.07))
    pixels = []
    for y in range(64):
        for x in range(64):
            blotch = ((x // 8) * 7 + (y // 7) * 11 + x * y * 3) % 23
            index = 3 if blotch < 3 else 2 if blotch < 8 else 1 if blotch < 15 else 0
            pixels.extend((*palette[index], 1))
    image.pixels[:] = pixels
    image.pack()
    mat = material("PSX nearest atlas wall", (0.1, 0.12, 0.1), roughness=1)
    nodes = mat.node_tree.nodes
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    mat.node_tree.links.new(tex.outputs["Color"],
                            nodes.get("Principled BSDF").inputs["Base Color"])
    return mat


def fog_material():
    mat = bpy.data.materials.new("PSX draw-distance fog")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (0.13, 0.19, 0.16, 1)
    volume.inputs["Density"].default_value = 0.025
    mat.node_tree.links.new(volume.outputs["Volume"], output.inputs["Volume"])
    return mat


def make_scene(spec, spec_dir=Path(".")):
    if int(spec.get("texture_size_px", 64)) != 64:
        raise ValueError("This authored PSX set uses a 64-pixel atlas")
    scene = reset_scene(spec, background=(0.002, 0.006, 0.004))
    scene.view_settings.view_transform = "Standard"
    scene.unit_settings.system = "METRIC"
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.04
    kit = bpy.data.collections.new("COL_PSX_Horror_Kit")
    scene.collection.children.link(kit)
    wall = limited_atlas()
    floor_mat = material("PSX dark floor", (0.035, 0.05, 0.04), roughness=0.98)
    iron = material("PSX dull iron", (0.08, 0.09, 0.075), metallic=0, roughness=0.9)
    yellow = material("PSX yellowed plastic", (0.32, 0.30, 0.2), roughness=0.95)
    phosphor = material("PSX green phosphor", (0.08, 0.24, 0.06), roughness=1,
                        emission=(0.16, 0.95, 0.22), emission_strength=0.1)
    practical_mat = material("PSX dim practical", (0.08, 0.18, 0.09), roughness=1,
                             emission=(0.28, 0.65, 0.34), emission_strength=0.5)

    # Keep a bare room chunk: the 64px atlas, low-poly boxes, and fog carry the look.
    to_collection(cube("SM_PSX_Floor", (0, 4, -0.07), (1.55, 10, 0.14), floor_mat), kit)
    to_collection(cube("SM_PSX_Ceiling", (0, 4, 2.23), (1.55, 10, 0.11), wall), kit)
    for side, x in (("Left", -0.775), ("Right", 0.775)):
        to_collection(cube(f"SM_PSX_{side}_Wall", (x, 4, 1.1),
                           (0.12, 10, 2.2), wall), kit)
    to_collection(cube("SM_PSX_End_Wall", (0, 8.8, 1.1),
                       (1.55, 0.13, 2.2), wall), kit)
    for bay in range(3):
        y = 1.5 + bay * 2.4
        to_collection(cube(f"SM_PSX_Ceiling_Strip_{bay}",
                           (0, y, 2.17), (0.12, 0.45, 0.02), iron), kit)

    # A single analog CRT is the narrative payoff rather than dense prop dressing.
    to_collection(cube("SM_PSX_Table", (0.0, 5.55, 0.72),
                       (0.9, 0.48, 0.055), iron), kit)
    for x in (-0.37, 0.37):
        to_collection(cube(f"SM_PSX_Table_Leg_{x}",
                           (x, 5.55, 0.34), (0.06, 0.06, 0.68), iron), kit)
    to_collection(cube("SM_PSX_CRT_Body", (0, 5.7, 1.05),
                       (0.61, 0.35, 0.54), yellow), kit)
    to_collection(cube("SM_PSX_CRT_Bezel", (0, 5.505, 1.07),
                       (0.53, 0.025, 0.43), iron), kit)
    screen = to_collection(cube("SM_PSX_CRT_Screen", (0, 5.486, 1.08),
                                (0.43, 0.01, 0.33), phosphor), kit)
    screen["analog_narrative_prop"] = True
    for x in (-0.19, -0.07, 0.05, 0.17):
        to_collection(cube(f"SM_PSX_Screen_Band_{x}",
                           (x, 5.477, 1.08), (0.014, 0.002, 0.27), iron), kit)
    emission = phosphor.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    for frame, value in ((1, 0.1), (24, 0.1), (31, 1.4), (33, 0.15),
                         (36, 2.2), (49, 0.25), (52, 2.7), (72, 3.4)):
        emission.default_value = value
        emission.keyframe_insert(data_path="default_value", frame=frame)

    practical = area_light("PSX lone fluorescent", (0, 2.3, 2.08),
                           68, 0.65, color=(0.32, 0.68, 0.43),
                           target=(0, 3.2, 0.4))
    to_collection(practical, kit)
    to_collection(cube("SM_PSX_Fluorescent_Tube", (0, 2.3, 2.16),
                       (0.06, 0.52, 0.02), practical_mat), kit)
    fog = to_collection(cube("PSX distance fog", (0, 4.8, 1.08),
                             (1.4, 8.4, 2.1), fog_material()), kit)
    fog.hide_select = True
    cam = camera("PSX eye camera", (0, -1.2, 1.5), (0, 5.7, 1.25), lens=32)
    for frame, x, y in ((1, 0, -1.2), (18, 0.025, -0.6),
                        (36, -0.025, 0.15), (54, 0.03, 0.85),
                        (72, 0, 1.5)):
        cam.location.x, cam.location.y = x, y
        cam.keyframe_insert(data_path="location", frame=frame)
    return scene
