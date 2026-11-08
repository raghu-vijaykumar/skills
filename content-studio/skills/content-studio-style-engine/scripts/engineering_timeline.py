"""Keyframe component emphasis and camera choreography in Blender 4."""
from mathutils import Vector
import bpy

def frame_at(seconds, fps, end):
    frame = 1 + round(float(seconds) * fps)
    if not 1 <= frame <= end:
        raise ValueError("Timeline event outside video duration")
    return frame

def meshes_under(root):
    return [root] if root.type == "MESH" else [o for o in root.children_recursive if o.type == "MESH"]

def isolate_materials(root):
    materials = []
    for obj in meshes_under(root):
        for slot in obj.material_slots:
            if slot.material:
                slot.material = slot.material.copy()
            else:
                mat = bpy.data.materials.new(obj.name + "_timeline")
                mat.diffuse_color = (0.3, 0.7, 0.9, 1)
                mat.use_nodes = True
                slot.material = mat
            mat = slot.material
            if not mat.use_nodes:
                mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                materials.append((mat, bsdf))
    return materials

def apply_events(spec, objects, camera, fps, end):
    """Events: {time_seconds, component, opacity?, highlight?} or camera {position?, target?, scale?}."""
    material_cache = {}
    for event in sorted(spec.get("timeline", []), key=lambda e: e["time_seconds"]):
        frame = frame_at(event["time_seconds"], fps, end)
        if event.get("type", "component") == "component":
            name = event["component"]
            if name not in objects:
                raise ValueError(f"Unknown timeline component: {name}")
            if name not in material_cache:
                material_cache[name] = isolate_materials(objects[name])
            for mat, bsdf in material_cache[name]:
                if "opacity" in event:
                    opacity = float(event["opacity"])
                    if not 0.05 <= opacity <= 1:
                        raise ValueError("opacity must be between 0.05 and 1")
                    mat.surface_render_method = "DITHERED"
                    socket = bsdf.inputs["Alpha"]
                    socket.default_value = opacity
                    socket.keyframe_insert(data_path="default_value", frame=frame)
                if "highlight" in event:
                    socket = bsdf.inputs["Emission Color"]
                    socket.default_value = (0.05, 0.6, 1.0, 1)
                    socket.keyframe_insert(data_path="default_value", frame=frame)
                    strength = bsdf.inputs["Emission Strength"]
                    strength.default_value = 1.8 if event["highlight"] else 0
                    strength.keyframe_insert(data_path="default_value", frame=frame)
        elif event["type"] == "camera":
            if "position" in event:
                camera.location = Vector(event["position"])
                camera.keyframe_insert(data_path="location", frame=frame)
            if "target" in event:
                direction = Vector(event["target"]) - camera.location
                if direction.length < 0.001:
                    raise ValueError("Camera target cannot equal position")
                camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
                camera.keyframe_insert(data_path="rotation_euler", frame=frame)
            if "scale" in event:
                scale = float(event["scale"])
                if not 1 <= scale <= 100:
                    raise ValueError("Camera scale outside range")
                camera.data.ortho_scale = scale
                camera.data.keyframe_insert(data_path="ortho_scale", frame=frame)
        else:
            raise ValueError("Unsupported timeline event type")
