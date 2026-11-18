"""Original cut-paper butterfly with visible layers and held stop-motion poses."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def paper_texture(name, base, accent):
    """Pack visible paper fiber and broad pigment irregularity inside the blend."""
    image = bpy.data.images.new(name + " packed fibers", 128, 128, alpha=True)
    pixels = []
    for y in range(128):
        for x in range(128):
            broad = 0.055 * math.sin(x * 0.14 + 1.8 * math.sin(y * 0.08))
            fiber_hash = (math.sin(x * 127.1 + y * 311.7) * 43758.5453) % 1
            fiber = 0.045 if fiber_hash > 0.94 else 0
            fold = 0.12 if abs(x - (39 + 4 * math.sin(y * 0.09))) < 2 else 0
            color = tuple(max(0, min(1, base[i] + broad + fiber +
                                      (accent[i] - base[i]) * fold)) for i in range(3))
            pixels.extend((*color, 1))
    image.pixels[:] = pixels
    image.pack()
    mat = material(name, base, roughness=0.96)
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    mat.node_tree.links.new(tex.outputs["Color"],
                            mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])
    mat["craft_fiber"] = True
    return mat


def wing_piece(name, side, points, y, mat):
    """Keep a slightly uneven cut edge and real thickness instead of a perfect decal."""
    vertices = [(side * x, y, z) for x, z in points]
    mesh = bpy.data.meshes.new(name + " cut edge")
    mesh.from_pydata(vertices, [], [tuple(range(len(vertices)))])
    mesh.update()
    uv = mesh.uv_layers.new(name="Paper fiber UV")
    for loop_index, (x, z) in zip(mesh.polygons[0].loop_indices, points):
        uv.data[loop_index].uv = (x / 1.15, (z + 0.7) / 1.55)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    solid = obj.modifiers.new("Physical paper thickness", "SOLIDIFY")
    solid.thickness = 0.025
    obj["cut_paper_layer"] = True
    return obj


def stroke(name, coords, radius, mat):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    line = curve.splines.new("BEZIER")
    line.bezier_points.add(len(coords) - 1)
    for point, coord in zip(line.bezier_points, coords):
        point.co = coord
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    curve.materials.append(mat)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def parent_keep_world(obj, parent):
    bpy.context.view_layer.update()
    transform = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = transform
    return obj


def hold_keys(obj, paths):
    """Every transform channel holds until the next hand-positioned pose."""
    action = obj.animation_data.action
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves
    else:
        curves = action.fcurves
    for curve in curves:
        if curve.data_path in paths:
            for point in curve.keyframe_points:
                point.interpolation = "CONSTANT"


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.67, 0.62, 0.55))
    scene.unit_settings.system = "METRIC"
    coral = paper_texture("Paper coral wing stock", (0.78, 0.32, 0.25),
                          (0.51, 0.19, 0.18))
    ochre = paper_texture("Paper ochre wing stock", (0.91, 0.61, 0.25),
                          (0.59, 0.33, 0.18))
    cream = paper_texture("Paper cream applique", (0.94, 0.78, 0.57),
                          (0.70, 0.51, 0.35))
    ink = material("Paper charcoal fold ink", (0.09, 0.07, 0.07), roughness=1)
    brown = material("Paper rolled body", (0.24, 0.15, 0.12), roughness=0.98)
    mat = material("Paper sage cutting mat", (0.42, 0.55, 0.49), roughness=1)
    grid = material("Paper cutting grid", (0.53, 0.64, 0.58), roughness=1)
    tape = material("Paper masking tape", (0.79, 0.72, 0.55), roughness=0.99)
    backdrop_mat = paper_texture("Paper warm backdrop stock", (0.61, 0.53, 0.47),
                                 (0.43, 0.37, 0.34))
    shadow_mat = material("Paper puppet shadow", (0.34, 0.44, 0.39), roughness=1)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 1.52, 1.28),
                                     rotation=(math.pi / 2, 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "Paper stock backdrop"
    backdrop.scale = (5.8, 3.3, 1)
    backdrop.data.materials.append(backdrop_mat)
    table = cube("SM_Paper_Craft_Table", (0, 0, -0.10), (4.6, 2.8, 0.18), mat)
    table["real_table_m"] = [4.6, 2.8, 0.18]
    for index in range(-5, 6):
        x = index * 0.38
        cube(f"Paper grid vertical {index}", (x, 0, -0.004),
             (0.009, 2.68, 0.005), grid)
    for index in range(-3, 4):
        y = index * 0.38
        cube(f"Paper grid horizontal {index}", (0, y, -0.003),
             (4.45, 0.009, 0.005), grid)
    for index, x in enumerate((-1.70, 1.65)):
        tape_piece = cube(f"Paper masking tape {index}", (x, 0.85, 0.012),
                          (0.45, 0.20, 0.012), tape)
        tape_piece.rotation_euler.z = (-0.12 if index == 0 else 0.17)
    shadow = sphere("SM_Paper_Butterfly_Shadow", (-0.55, -0.12, 0.008),
                    0.4, shadow_mat, segments=32, rings=12,
                    scale=(1.5, 0.75, 0.045))

    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    root.name = "Paper butterfly root"
    body = cylinder("SM_Paper_Butterfly_Body", (0, -0.15, 0.85),
                    0.085, 0.92, brown, vertices=16)
    body["rolled_paper"] = True
    parent_keep_world(body, root)
    # A visible roll seam and two paper fasteners explain the physical assembly.
    parent_keep_world(stroke("Paper rolled body seam",
                             [(0.075, -0.235, 0.43),
                              (0.075, -0.235, 0.86),
                              (0.075, -0.235, 1.26)], 0.006, ink), root)
    for side in (-1, 1):
        parent_keep_world(cylinder("Paper wing fastener",
                                   (side * 0.10, -0.270, 0.87), 0.055, 0.025,
                                   tape, vertices=16,
                                   rotation=(math.pi / 2, 0, 0)), root)
    for side, label in ((-1, "Left"), (1, "Right")):
        bpy.ops.object.empty_add(location=(side * 0.08, -0.15, 0.87))
        hinge = bpy.context.object
        hinge.name = f"Paper {label.lower()} wing hinge"
        parent_keep_world(hinge, root)
        upper = wing_piece(f"SM_Paper_{label}_Upper_Wing", side,
                           [(0.07, 0.93), (0.31, 1.20), (0.75, 1.49),
                            (1.03, 1.42), (0.96, 1.14), (1.08, 0.96),
                            (0.84, 0.82), (0.47, 0.91), (0.09, 0.78)],
                           -0.19, coral)
        lower = wing_piece(f"Paper {label.lower()} lower wing", side,
                           [(0.08, 0.81), (0.45, 0.86), (0.82, 0.65),
                            (0.80, 0.37), (0.56, 0.30), (0.27, 0.46),
                            (0.08, 0.58)], -0.20, ochre)
        parent_keep_world(upper, hinge)
        parent_keep_world(lower, hinge)
        # A second cream paper patch and a dark seam expose the layered assembly.
        patch = wing_piece(f"Paper {label.lower()} applique", side,
                           [(0.30, 1.08), (0.66, 1.32), (0.84, 1.24),
                            (0.69, 1.03), (0.42, 0.99)], -0.23, cream)
        parent_keep_world(patch, hinge)
        fold = stroke(f"Paper {label.lower()} fold seam",
                      [(side * 0.12, -0.25, 0.77),
                       (side * 0.20, -0.25, 1.05),
                       (side * 0.32, -0.25, 1.27)], 0.012, ink)
        parent_keep_world(fold, hinge)
        for frame, angle in ((1, 0), (7, side * 0.42), (13, side * 0.88),
                             (19, side * 0.43), (25, 0), (31, side * 0.50),
                             (37, side * 0.92), (43, side * 0.42),
                             (49, 0), (55, side * 0.45),
                             (61, side * 0.84), (67, side * 0.37), (72, 0)):
            hinge.rotation_euler.z = angle
            hinge.keyframe_insert(data_path="rotation_euler", frame=frame)
        hold_keys(hinge, {"rotation_euler"})
    for side in (-1, 1):
        parent_keep_world(stroke("Paper wire antenna", [(side * 0.035, -0.14, 1.29),
                              (side * 0.13, -0.13, 1.53),
                              (side * 0.24, -0.12, 1.58)], 0.010, ink), root)

    # The entire puppet moves only at hand-placed six-frame positions.
    for frame, x, z in ((1, -0.55, 0), (13, -0.36, 0.05),
                         (25, -0.12, 0.09), (37, 0.17, 0.12),
                         (49, 0.42, 0.08), (61, 0.57, 0.03), (72, 0.68, 0)):
        root.location = (x, 0, z)
        root.keyframe_insert(data_path="location", frame=frame)
        # The flat table shadow follows x while staying on the craft mat.
        shadow.location.x = x
        shadow.keyframe_insert(data_path="location", frame=frame)
    hold_keys(root, {"location"})
    hold_keys(shadow, {"location"})
    camera("Paper butterfly camera", (0, -5.0, 2.48),
           (0, 0, 0.69), ortho=4.20)
    area_light("Paper practical warm lamp", (-2, -3, 4), 850, 2.8,
               color=(1.0, 0.82, 0.67), target=(0, 0, 0.65))
    area_light("Paper table bounce", (2, 1, 3), 200, 3.0,
               color=(0.76, 0.88, 1.0), target=(0, 0, 0.65))
    scene["craft_sublook"] = "cut paper, layered applique, fiber stock, fold seam, held poses"
    return scene
