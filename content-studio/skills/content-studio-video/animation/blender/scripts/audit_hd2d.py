"""Audit HD-2D pixel actors against their painted 3D bridge stage."""

import argparse
import json
from pathlib import Path
import sys

import bpy


def required(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"Missing HD-2D object: {name}")
    return obj


def location_held(obj):
    if not obj.animation_data:
        return False
    action = obj.animation_data.action
    if bpy.app.version >= (5, 0):
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves
    else:
        curves = action.fcurves
    location = [curve for curve in curves if curve.data_path == "location"]
    return bool(location) and all(key.interpolation == "CONSTANT"
                                  for curve in location for key in curve.keyframe_points)


def audit():
    scene = bpy.context.scene
    variant = scene.get("hd2d_variant")
    bridge = required("SM_HD2D_Stone_Bridge")
    deck = required("SM_HD2D_Painted_Deck")
    stream = required("SM_HD2D_Stream")
    actor = required("SM_HD2D_Pixel_Traveler")
    alt = required("HD2D traveler alternate")
    ctrl = required("HD2D traveler control")
    lamp = required("SM_HD2D_Bridge_Lantern")
    cam = required("HD2D tilted camera")
    image = bpy.data.images.get("HD2D hand-painted bridge albedo")
    deck_mat = deck.data.materials[0]
    tex = next((node for node in deck_mat.node_tree.nodes
                if node.bl_idname == "ShaderNodeTexImage"), None)
    if (image is None or tuple(image.size) != (128, 64) or not image.packed_file or
            tex is None or tex.image != image or tex.interpolation != "Linear" or
            not deck_mat.get("packed_painted_deck")):
        raise ValueError("Packed painted bridge albedo changed")
    if (bridge.type != "MESH" or stream.type != "MESH" or
            abs(bridge.get("bridge_span_m", 0) - 5.15) > 0.001 or
            actor.parent != ctrl or alt.parent != ctrl or not location_held(ctrl) or
            cam.data.type != "ORTHO" or abs(cam.data.ortho_scale - 7.8) > 0.001 or
            not cam.data.dof.use_dof or cam.data.dof.focus_object !=
            required("HD2D stage focus") or cam.data.dof.aperture_fstop > 3.3 or
            cam.rotation_euler.x == 0 or not lamp.get("lantern_side") or
            (scene.render.resolution_x, scene.render.resolution_y,
             scene.render.fps, scene.frame_end) != (960, 540, 24, 72) or
            scene.get("hd2d_recipe") !=
            "pixel billboard on painted 3D bridge, tilted orthographic camera, warm keys, depth of field"):
        raise ValueError("3D bridge, camera, light, or shot contract changed")
    lights = [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
    if (len(lights) != 3 or
            len([obj for obj in lights if obj.name.startswith("HD2D warm key")]) != 2):
        raise ValueError("Theatrical warm-key and cool-fill lighting changed")
    sprite_mats = [mat for mat in bpy.data.materials if mat.get("hd2d_pixel_fill")]
    if len(sprite_mats) != 6 or any({node.bl_idname for node in mat.node_tree.nodes} != {
            "ShaderNodeEmission", "ShaderNodeOutputMaterial"} for mat in sprite_mats):
        raise ValueError("The six flat pixel fills changed")
    pixel_parts = [obj for obj in bpy.data.objects if obj.get("sprite_pixel_faces")]
    if len(pixel_parts) < 10:
        raise ValueError("The two editable sprite poses lost color layers")
    for part in pixel_parts:
        if part.type != "MESH" or len(part.data.polygons) != part["sprite_pixel_faces"]:
            raise ValueError(f"Sprite pixel faces changed: {part.name}")
        for face in part.data.polygons:
            verts = [part.data.vertices[i].co for i in face.vertices]
            if (len(verts) != 4 or abs(max(v.x for v in verts)-min(v.x for v in verts)-0.052) > 0.0001 or
                    abs(max(v.z for v in verts)-min(v.z for v in verts)-0.052) > 0.0001):
                raise ValueError(f"Sprite lost square pixels: {part.name}")
    reeds = [obj for obj in bpy.data.objects if obj.name.startswith("HD2D near reed ")]
    ripples = [obj for obj in bpy.data.objects if obj.name.startswith("HD2D water ripple ")]
    if (variant == 1 and (reeds or ripples)) or (variant in (2, 3) and
            (len(reeds) != 4 or len(ripples) != 2)):
        raise ValueError("Candidate-specific stage detail changed")
    samples = {}
    for frame in (1, 7, 35, 72):
        scene.frame_set(frame)
        samples[frame] = {"traveler_x": ctrl.location.x,
                          "base_pose_visible": not actor.children[0].hide_render,
                          "alternate_pose_visible": not alt.children[0].hide_render}
    if (samples[1]["traveler_x"] >= samples[72]["traveler_x"] or
            not samples[1]["base_pose_visible"] or samples[1]["alternate_pose_visible"] or
            (variant == 1 and (not samples[7]["base_pose_visible"] or
                               samples[7]["alternate_pose_visible"])) or
            (variant in (2, 3) and (samples[7]["base_pose_visible"] or
                                    not samples[7]["alternate_pose_visible"]))):
        raise ValueError("Held sprite walk or frame timing changed")
    return {"variant": variant, "packed_painted_texture_px": list(image.size),
            "sprite_pixel_faces": sum(part["sprite_pixel_faces"] for part in pixel_parts),
            "warm_keys": 2, "cool_fill": 1, "orthographic_tilt_and_dof": True,
            "foreground_reeds": len(reeds), "water_ripples": len(ripples),
            "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    args.out.write_text(json.dumps(audit(), indent=2) + "\n", encoding="utf-8")
    print("Audited pixel actors, painted bridge, warm lights, tilted camera, and DOF")


if __name__ == "__main__":
    main()
