"""Import externally authored 3D models into a Blender scene.
Use from a Blender Python script: from model_assets import load_component
"""
from pathlib import Path
import bpy

SUPPORTED = {".glb", ".gltf", ".fbx"}

def load_component(asset_path, name, base_dir=None):
    path = Path(asset_path).expanduser()
    if not path.is_absolute():
        path = Path(base_dir or ".") / path
    path = path.resolve()
    if not path.is_file() or path.suffix.lower() not in SUPPORTED:
        raise ValueError(f"Unsupported or missing 3D model: {path}")
    before = set(bpy.data.objects)
    if path.suffix.lower() in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(path))
    else:
        bpy.ops.import_scene.fbx(filepath=str(path))
    imported = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    if not imported:
        raise ValueError(f"No mesh objects in model: {path}")
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    for obj in imported:
        world = obj.matrix_world.copy()
        obj.parent = root
        obj.matrix_world = world
    return root, imported
