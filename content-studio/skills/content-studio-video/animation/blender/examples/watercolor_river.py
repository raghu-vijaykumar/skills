"""Original scene-wide watercolor river with a drifting 2.5D sailboat."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, material, reset_scene


def blend(a, b, amount):
    return tuple(a[i] * (1 - amount) + b[i] * amount for i in range(3))


def paper_noise(x, y):
    # Deterministic pigment granulation, kept below the broad wash contrast.
    return (math.sin(x * 127.1 + y * 311.7) * 43758.5453) % 1 - 0.5


def canvas_paint():
    """Pack a complete 16:9 watercolor canvas with bleeds and paper tooth."""
    width, height = 512, 288
    image = bpy.data.images.new("Watercolor river pigment and paper", width, height,
                                alpha=True)
    pixels = []
    for y in range(height):
        v = y / (height - 1)
        for x in range(width):
            u = x / (width - 1)
            horizon = 0.45 + 0.015 * math.sin(u * 9)
            if v >= horizon:
                sky_t = min(1, (v - horizon) / 0.55)
                color = blend((0.91, 0.69, 0.57), (0.50, 0.63, 0.75), sky_t)
                for cx, cy, radius in ((0.20, 0.79, 0.19), (0.50, 0.67, 0.16),
                                        (0.84, 0.83, 0.15)):
                    band = abs(v - cy - 0.016 * math.sin(u * 16 + cx * 7))
                    length = abs(u - cx)
                    if band < 0.043 and length < radius:
                        color = blend(color, (0.96, 0.76, 0.69),
                                      0.25 * (1 - band / 0.043) * (1 - length / radius))
                # A diffuse sun edge belongs to the paint rather than a hard 3D disc.
                sun = math.hypot((u - 0.73) * 1.78, v - 0.73)
                if sun < 0.135:
                    color = blend(color, (1.0, 0.88, 0.61),
                                  min(1, (0.135 - sun) / 0.035))
            else:
                water_t = max(0, min(1, v / horizon))
                color = blend((0.23, 0.44, 0.52), (0.65, 0.60, 0.60), water_t)
                ripple = 0.5 + 0.5 * math.sin(v * 103 + u * 17 + 2 * math.sin(u * 12))
                band = max(0, ripple - 0.79) * (0.15 + 0.10 * water_t)
                color = blend(color, (0.94, 0.76, 0.61), band)
            # Uneven far-shore silhouette and wet bleed soften the sky/water join.
            hill = horizon + 0.065 * math.sin(u * 7 + 0.3) + 0.024 * math.sin(u * 21)
            if horizon - 0.035 < v < hill:
                edge = max(0, min(1, (hill - v) / 0.025))
                color = blend(color, (0.41, 0.51, 0.61), 0.55 * edge)
            grain = paper_noise(x, y) * 0.055
            streak = 0.016 * math.sin(x * 0.16 + y * 0.025)
            color = tuple(max(0, min(1, c + grain + streak)) for c in color)
            pixels.extend((*color, 1))
    image.pixels[:] = pixels
    image.pack()
    mat = bpy.data.materials.new("Watercolor paper canvas")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    nodes.new("ShaderNodeEmission")
    emission = nodes.get("Emission")
    mat.node_tree.links.new(tex.outputs["Color"], emission.inputs["Color"])
    mat.node_tree.links.new(emission.outputs["Emission"], out.inputs["Surface"])
    mat["pigment_washes"] = "sky, sun, far shore, river, paper granulation"
    return mat


def sail_paint():
    """A separate packed wash keeps the moving sail in the painted language."""
    image = bpy.data.images.new("Watercolor sail wash", 128, 128, alpha=True)
    pixels = []
    for y in range(128):
        for x in range(128):
            u, v = x / 127, y / 127
            waviness = 0.055 * math.sin(v * 18 + u * 9)
            base = (0.92, 0.82, 0.67)
            tint = 0.07 * v + waviness + paper_noise(x, y) * 0.035
            color = (base[0] - tint * 0.3, base[1] - tint * 0.5,
                     base[2] + tint * 0.2)
            # A broad diagonal pigment drag stays visible on the moving sail.
            stroke = abs(v - (0.34 + 0.30 * u + 0.035 * math.sin(u * 14)))
            if stroke < 0.11:
                color = blend(color, (0.71, 0.51, 0.48),
                              0.30 * (1 - stroke / 0.11))
            pixels.extend((*color, 1))
    image.pixels[:] = pixels
    image.pack()
    mat = material("Watercolor matte sail", (0.92, 0.82, 0.67), roughness=1)
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    mat.node_tree.links.new(tex.outputs["Color"],
                            mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])
    mat["pigment_sail"] = True
    return mat


def flat_shape(name, points, y, mat, uv_points=None):
    """Thin 3D relief cards are editable, and the background remains a packed canvas."""
    mesh = bpy.data.meshes.new(name + " painted geometry")
    mesh.from_pydata([(x, y, z) for x, z in points], [], [tuple(range(len(points)))])
    mesh.update()
    if uv_points:
        uv = mesh.uv_layers.new(name="Paint UV")
        for loop_index, coord in zip(mesh.polygons[0].loop_indices, uv_points):
            uv.data[loop_index].uv = coord
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def curve_stroke(name, points, radius, mat):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    line = curve.splines.new("BEZIER")
    line.bezier_points.add(len(points) - 1)
    for point, (x, y, z) in zip(line.bezier_points, points):
        point.co = (x, y, z)
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


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.62, 0.67, 0.68))
    canvas_mat = canvas_paint()
    sail_mat = sail_paint()
    hull_mat = material("Watercolor blue hull", (0.17, 0.35, 0.44), roughness=0.96)
    hull_highlight = material("Watercolor hull edge wash", (0.41, 0.60, 0.61), roughness=0.95)
    mast_mat = material("Watercolor umber mast", (0.38, 0.29, 0.26), roughness=1)
    reed_mat = material("Watercolor deep reed", (0.19, 0.36, 0.34), roughness=1)
    ripple_mat = material("Watercolor soft pigment ripple", (0.45, 0.57, 0.61), roughness=1)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 1.20, 0),
                                     rotation=(math.pi / 2, 0, 0))
    canvas = bpy.context.object
    canvas.name = "SM_Watercolor_Canvas"
    canvas.scale = (5.65, 3.18, 1)
    canvas.data.materials.append(canvas_mat)
    canvas["watercolor_canvas_px"] = [512, 288]

    # Pigment strokes in front of the packed river create a little real 2.5D depth.
    for index in range(12):
        row = index // 4
        col = index % 4
        x = -2.34 + col * 1.30 + 0.33 * math.sin(index * 1.61)
        z = -0.72 - row * 0.25 + 0.095 * math.sin(index * 4.3)
        length = 0.16 + 0.12 * (1 + math.sin(index * 2.3))
        flat_shape(f"Watercolor river stroke {index}",
                   [(x - length, z), (x - length * 0.62, z - 0.012),
                    (x + length * 0.52, z - 0.019), (x + length, z + 0.005),
                    (x + length * 0.70, z + 0.020),
                    (x - length * 0.65, z + 0.013)],
                   -0.18 - row * 0.04, ripple_mat if index % 5 else hull_highlight)

    bpy.ops.object.empty_add(location=(0, 0, 0))
    boat_control = bpy.context.object
    boat_control.name = "Watercolor boat control"
    hull = flat_shape("SM_Watercolor_Boat",
                      [(-0.50, -0.04), (0.51, -0.04), (0.35, -0.22),
                       (0.12, -0.27), (-0.32, -0.23)], -0.56, hull_mat)
    parent_keep_world(hull, boat_control)
    parent_keep_world(curve_stroke("Watercolor hull top brush",
                                   [(-0.49, -0.59, -0.04), (0, -0.59, -0.025),
                                    (0.50, -0.59, -0.04)], 0.017,
                                   hull_highlight), boat_control)
    mast = curve_stroke("Watercolor slender mast",
                        [(0, -0.60, -0.01), (0, -0.60, 0.40),
                         (0, -0.60, 0.81)], 0.014, mast_mat)
    parent_keep_world(mast, boat_control)
    sail = flat_shape("SM_Watercolor_Sail",
                      [(0.045, 0.06), (0.42, 0.13), (0.035, 0.77)], -0.61,
                      sail_mat, [(0.05, 0.05), (0.95, 0.10), (0.05, 0.95)])
    parent_keep_world(sail, boat_control)
    parent_keep_world(curve_stroke("Watercolor sail edge",
                                   [(0.04, -0.63, 0.06), (0.42, -0.63, 0.13),
                                    (0.04, -0.63, 0.77)], 0.009, hull_highlight),
                      boat_control)
    boat_control.scale = (1.18, 1.18, 1.18)
    for frame, x, bob, tilt in ((1, -1.25, -0.43, -0.02),
                                (36, 0.00, -0.39, 0.025),
                                (72, 1.25, -0.43, -0.01)):
        boat_control.location = (x, 0, bob)
        boat_control.rotation_euler.y = tilt
        boat_control.keyframe_insert(data_path="location", frame=frame)
        boat_control.keyframe_insert(data_path="rotation_euler", frame=frame)

    for index in range(8):
        side = -1 if index < 4 else 1
        x = side * (2.08 + (index % 4) * 0.13)
        base = -1.47 + 0.015 * (index % 4)
        bpy.ops.object.empty_add(location=(x, -0.72, base))
        pivot = bpy.context.object
        pivot.name = f"Watercolor reed control {index}"
        reed = curve_stroke(f"SM_Watercolor_Reed_{index}",
                            [(x, -0.72, base),
                             (x - side * 0.10, -0.72, base + 0.40),
                             (x - side * (0.25 + index % 3 * 0.05), -0.72,
                              base + 0.77 + 0.05 * (index % 3))],
                            0.015 + 0.003 * (index % 2), reed_mat)
        parent_keep_world(reed, pivot)
        for frame, angle in ((1, side * -0.08), (36, side * 0.06),
                             (72, side * -0.05)):
            pivot.rotation_euler.y = angle
            pivot.keyframe_insert(data_path="rotation_euler", frame=frame)

    camera("Watercolor fixed camera", (0, -6.2, 0),
           (0, 0, 0), ortho=5.55)
    area_light("Watercolor soft illustration light", (-2, -3, 4), 500, 5,
               target=(0, 0, 0))
    scene["painterly_sublook"] = "watercolor paper grain, pigment bleeds, diffuse sun, layered strokes"
    return scene
