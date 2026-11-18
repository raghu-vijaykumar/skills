"""Original matte teacup with packed, brush-authored wildflower albedo."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene


def mix(a, b, amount):
    return tuple(a[i] * (1 - amount) + b[i] * amount for i in range(3))


def flower_value(u, v, center):
    """Layer broad petals and leaves on the UV canvas; avoid photographic noise."""
    du = ((u - center + 0.5) % 1) - 0.5
    value = (0.0, 0.0, 0.0)
    for petal in range(5):
        angle = petal * math.tau / 5
        px = du - 0.065 * math.cos(angle)
        py = v - 0.52 - 0.095 * math.sin(angle)
        along = px * math.cos(angle) + py * math.sin(angle)
        across = -px * math.sin(angle) + py * math.cos(angle)
        distance = (along / 0.075) ** 2 + (across / 0.036) ** 2
        strength = max(0, min(1, (1.08 - distance) * 2.5))
        if strength > value[0]:
            value = (strength, distance, petal)
    return value, du


def painted_albedo():
    """Pack a 256² UV painting with large strokes, not a noisy photo texture."""
    base = (0.87, 0.74, 0.55)
    blue = (0.12, 0.33, 0.36)
    leaf = (0.19, 0.43, 0.33)
    ochre = (0.74, 0.40, 0.19)
    image = bpy.data.images.new("Painted wildflower albedo", 256, 256, alpha=True)
    pixels = []
    for y in range(256):
        v = y / 255
        for x in range(256):
            u = x / 255
            # Wide, curved pigment washes give the ceramic value structure.
            wash = 0.84 + 0.13 * v + 0.038 * math.sin(u * 22 + v * 8)
            color = tuple(min(1, c * wash) for c in base)
            for index, height in enumerate((0.18, 0.33, 0.73)):
                path = height + 0.013 * math.sin(u * 19 + index * 1.4)
                distance = abs(v - path)
                if distance < 0.025:
                    width = 0.32 * (1 - distance / 0.025)
                    color = mix(color, ochre if index != 1 else blue, width)
            for center in (0.12, 0.45, 0.78):
                (strength, distance, petal), du = flower_value(u, v, center)
                if v < 0.45 and abs(du - 0.012 * math.sin(v * 14 + center * 10)) < 0.009:
                    color = mix(color, leaf, 0.78)
                for side in (-1, 1):
                    leaf_d = ((du - side * 0.050) / 0.040) ** 2 + ((v - 0.32) / 0.025) ** 2
                    if leaf_d < 1:
                        color = mix(color, leaf, (1 - leaf_d) * 0.9)
                if strength:
                    # Broad bristle bands run through each petal rather than a photo-noise overlay.
                    bristle = math.sin((u - center) * 125 + v * 68 + petal * 2.1)
                    shade = (0.72 if distance < 0.55 else 0.94) * (1 + 0.16 * bristle)
                    color = mix(color, tuple(c * shade for c in blue), strength)
                center_d = (du / 0.024) ** 2 + ((v - 0.52) / 0.024) ** 2
                if center_d < 1:
                    color = mix(color, ochre, 1 - center_d * 0.35)
            pixels.extend((*color, 1))
    image.pixels[:] = pixels
    image.pack()
    mat = material("Painted matte wildflower ceramic", base, roughness=0.94)
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    mat.node_tree.links.new(tex.outputs["Color"],
                            mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])
    mat["painted_albedo"] = "three broad flowers, stems, leaves, curved pigment washes"
    return mat


def painted_backdrop():
    """A subtle packed wash keeps the set in the same illustrated language."""
    image = bpy.data.images.new("Painted backdrop wash", 128, 128, alpha=True)
    pixels = []
    sage = (0.51, 0.59, 0.52)
    dusk = (0.35, 0.50, 0.51)
    warm = (0.70, 0.65, 0.51)
    for y in range(128):
        v = y / 127
        for x in range(128):
            u = x / 127
            color = sage
            band = v - (0.64 + 0.075 * math.sin(u * 8) + 0.025 * math.sin(u * 19))
            if abs(band) < 0.17:
                color = mix(color, dusk, 0.23 * (1 - abs(band) / 0.17))
            band2 = v - (0.26 + 0.04 * math.sin(u * 11 + 1.7))
            if abs(band2) < 0.15:
                color = mix(color, warm, 0.21 * (1 - abs(band2) / 0.15))
            pixels.extend((*color, 1))
    image.pixels[:] = pixels
    image.pack()
    mat = material("Painted background wash", sage, roughness=1)
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    mat.node_tree.links.new(tex.outputs["Color"],
                            mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])
    mat["brush_wash"] = True
    return mat


def cup_mesh(mat):
    """Use a simple UV lathe so the painting, not mesh microdetail, carries the design."""
    rings = ((0.43, 0.08), (0.50, 0.12), (0.55, 0.72),
             (0.59, 0.81), (0.51, 0.82), (0.47, 0.71), (0.41, 0.20))
    count = 48
    verts = [(radius * math.cos(i * math.tau / count),
              radius * math.sin(i * math.tau / count), z)
             for radius, z in rings for i in range(count)]
    faces = []
    for row in range(len(rings) - 1):
        for i in range(count):
            j = (i + 1) % count
            faces.append((row * count + i, row * count + j,
                          (row + 1) * count + j, (row + 1) * count + i))
    mesh = bpy.data.meshes.new("Painted cup UV lathe")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="Painted atlas UV")
    levels = (0.02, 0.10, 0.85, 0.98, 0.98, 0.85, 0.12)
    for face in mesh.polygons:
        row, index = divmod(face.index, count)
        u0, u1 = index / count, (index + 1) / count
        for loop_index, coord in zip(face.loop_indices,
                                     ((u0, levels[row]), (u1, levels[row]),
                                      (u1, levels[row + 1]), (u0, levels[row + 1]))):
            uv.data[loop_index].uv = coord
    obj = bpy.data.objects.new("SM_Painted_Cup", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj["uv_ring_segments"] = count
    return obj


def parent_keep_world(obj, parent):
    bpy.context.view_layer.update()
    transform = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = transform
    return obj


def steam_curve(name, x, offset, mat):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.025
    curve.bevel_resolution = 3
    line = curve.splines.new("BEZIER")
    line.bezier_points.add(3)
    for point, (dx, dz) in zip(line.bezier_points,
                              ((0, 0), (0.13, 0.30), (-0.08, 0.58), (0.07, 0.89))):
        point.co = (dx, 0, dz)
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    curve.materials.append(mat)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (x, -0.06 + offset, 0.89)
    return obj


def make_scene(spec, spec_dir=Path(".")):
    scene = reset_scene(spec, background=(0.55, 0.62, 0.58))
    scene.unit_settings.system = "METRIC"
    ceramic = painted_albedo()
    trim = material("Painted turquoise rim", (0.14, 0.36, 0.37), roughness=0.93)
    saucer_mat = material("Painted ochre saucer", (0.63, 0.38, 0.24), roughness=0.94)
    tea_mat = material("Painted warm tea", (0.34, 0.19, 0.09), roughness=0.87)
    steam_mat = material("Painted pale steam", (0.82, 0.91, 0.85), roughness=1)
    stage = material("Painted warm stage", (0.48, 0.55, 0.48), roughness=1)
    cube("Painted backdrop floor", (0, 0, -0.15), (5.5, 4.2, 0.20), stage)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 2.06, 1.36),
                                     rotation=(math.pi / 2, 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "Painted illustrated backdrop"
    backdrop.scale = (10.5, 3.25, 1)
    backdrop.data.materials.append(painted_backdrop())
    saucer = cylinder("SM_Painted_Saucer", (0, 0, 0.035), 0.90, 0.09,
                      saucer_mat, vertices=64, edge=0.035)
    saucer["diameter_m"] = 1.8
    cylinder("Painted saucer inset", (0, 0, 0.082), 0.67, 0.012,
             trim, vertices=64)
    cylinder("Painted saucer center", (0, 0, 0.09), 0.57, 0.010,
             saucer_mat, vertices=64)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    control = bpy.context.object
    control.name = "Painted cup turn control"
    cup = parent_keep_world(cup_mesh(ceramic), control)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.35, minor_radius=0.08,
                                     location=(0.71, 0, 0.47),
                                     rotation=(math.pi / 2, 0, 0))
    handle = bpy.context.object
    handle.name = "SM_Painted_Handle"
    handle.data.materials.append(trim)
    bpy.ops.object.shade_smooth()
    parent_keep_world(handle, control)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.020,
                                     location=(0, 0, 0.78))
    rim = bpy.context.object
    rim.name = "Painted thin rim"
    rim.data.materials.append(trim)
    parent_keep_world(rim, control)
    parent_keep_world(cylinder("Painted tea surface", (0, 0, 0.68),
                               0.46, 0.012, tea_mat, vertices=64), control)
    # A deliberate turn reveals the albedo artwork while preserving the matte look.
    for frame, angle in ((1, -0.46), (36, 0.10), (72, 0.80)):
        control.rotation_euler.z = angle
        control.keyframe_insert(data_path="rotation_euler", frame=frame)
    for index, (x, offset) in enumerate(((-0.22, 0.0), (0.0, 0.16), (0.24, -0.04))):
        curl = steam_curve(f"SM_Painted_Steam_{index}", x, offset, steam_mat)
        # Anchor each curl at the tea rim while its length grows into frame.
        for frame, z, size in ((1, 0.82, 0.001), (15 + index * 3, 0.82, 0.001),
                               (36, 0.82, 0.58), (72, 0.82, 1.0)):
            curl.location.z = z
            curl.scale = (size, size, size)
            curl.keyframe_insert(data_path="location", frame=frame)
            curl.keyframe_insert(data_path="scale", frame=frame)
    camera("Painted teacup camera", (2.7, -4.5, 2.4),
           (0, 0, 0.77), ortho=3.8)
    area_light("Painted warm key", (-2, -3, 4), 700, 2.6,
               color=(1.0, 0.84, 0.65), target=(0, 0, 0.7))
    area_light("Painted cool fill", (2, 1, 3), 280, 2.8,
               color=(0.72, 0.90, 1.0), target=(0, 0, 0.7))
    scene["hand_painted_rule"] = "packed brushwork albedo, matte ceramic, no photobashed texture"
    return scene
