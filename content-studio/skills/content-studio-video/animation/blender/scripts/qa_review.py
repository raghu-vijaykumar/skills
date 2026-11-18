"""Capture scene evidence and give a reproducible Blender asset QA verdict."""

import argparse
import bmesh
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import bpy
from mathutils import Vector


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def video_stream(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,nb_read_frames", "-of", "json", str(path)],
        check=True, capture_output=True, text=True)
    streams = json.loads(result.stdout).get("streams", [])
    if len(streams) != 1:
        raise ValueError("QA needs one decoded video stream")
    return {key: int(streams[0][key]) for key in ("width", "height", "nb_read_frames")}


def geometry(obj):
    if obj.type != "MESH":
        raise ValueError("The QA hero must be a mesh")
    # Count evaluated geometry so a subdivision or array cannot evade the budget.
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        triangles = len(mesh.loop_triangles)
        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            loose = sum(1 for vertex in bm.verts if not vertex.link_edges)
            boundary = sum(1 for edge in bm.edges if not edge.is_manifold)
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    dimensions = [round(max(point[i] for point in corners) -
                        min(point[i] for point in corners), 4) for i in range(3)]
    return {"triangles": triangles, "loose_vertices": loose,
            "nonmanifold_edges": boundary, "dimensions_m": dimensions,
            "material_slots": [slot.material.name if slot.material else None
                               for slot in obj.material_slots]}


def capture_angles(scene, hero, out_dir):
    """Render isolated geometry views without changing the saved authoring scene."""
    out_dir.mkdir(parents=True, exist_ok=True)
    old_camera, old_engine = scene.camera, scene.render.engine
    old_path = scene.render.filepath
    old_media = scene.render.image_settings.media_type
    old_format = scene.render.image_settings.file_format
    old_size = (scene.render.resolution_x, scene.render.resolution_y,
                scene.render.resolution_percentage)
    hidden = {obj.name: obj.hide_render for obj in scene.objects}
    scene.frame_set((scene.frame_start + scene.frame_end) // 2)
    corners = [hero.matrix_world @ Vector(corner) for corner in hero.bound_box]
    center = sum(corners, Vector()) / len(corners)
    radius = max((point - center).length for point in corners)
    if radius <= 0:
        raise ValueError("QA hero has no measurable extent")
    camera_data = bpy.data.cameras.new("QA temporary camera")
    camera = bpy.data.objects.new("QA temporary camera", camera_data)
    scene.collection.objects.link(camera)
    captures = {}
    try:
        for obj in scene.objects:
            if obj != hero and obj != camera:
                obj.hide_render = True
        hero.hide_render = False
        scene.camera = camera
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x = 640
        scene.render.resolution_y = 480
        scene.render.resolution_percentage = 100
        scene.render.image_settings.media_type = "IMAGE"
        scene.render.image_settings.file_format = "PNG"
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "MATERIAL"
        scene.display.shading.show_shadows = True
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = radius * 3.1
        for name, offset in (
                ("hero-three-quarter", Vector((1.0, -1.3, 0.8))),
                ("profile", Vector((1.5, 0.0, 0.1)))):
            camera.location = center + offset.normalized() * radius * 4
            camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
            target = out_dir / f"{name}.png"
            scene.render.filepath = str(target)
            bpy.ops.render.render(write_still=True)
            captures[name] = {"path": str(target), "sha256": digest(target)}
    finally:
        scene.camera, scene.render.engine, scene.render.filepath = old_camera, old_engine, old_path
        scene.render.image_settings.media_type = old_media
        scene.render.image_settings.file_format = old_format
        (scene.render.resolution_x, scene.render.resolution_y,
         scene.render.resolution_percentage) = old_size
        for obj in scene.objects:
            if obj.name in hidden:
                obj.hide_render = hidden[obj.name]
        bpy.data.objects.remove(camera, do_unlink=True)
        bpy.data.cameras.remove(camera_data)
    return captures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", required=True, type=Path)
    parser.add_argument("--hero-object", required=True)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--gif", required=True, type=Path)
    parser.add_argument("--beauty", required=True, type=Path)
    parser.add_argument("--expected-video-sha", required=True)
    parser.add_argument("--expected-gif-sha", required=True)
    parser.add_argument("--triangle-budget", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--visual-verdict", choices=("SHIP", "SHIP WITH NOTES", "NO-SHIP"))
    parser.add_argument("--visual-note")
    parser.add_argument("--major", action="append", default=[])
    parser.add_argument("--minor", action="append", default=[])
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if args.triangle_budget < 1 or bool(args.visual_verdict) != bool(args.visual_note):
        parser.error("A positive budget and a paired visual verdict and note are required")
    # Opening a .blend may change Blender's working directory, so freeze all paths first.
    for name in ("blend", "video", "gif", "beauty", "out"):
        setattr(args, name, getattr(args, name).resolve())
    for path in (args.blend, args.video, args.gif, args.beauty):
        if not path.is_file():
            raise FileNotFoundError(path)
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    scene = bpy.context.scene
    hero = bpy.data.objects.get(args.hero_object)
    if hero is None:
        raise ValueError(f"Missing QA hero: {args.hero_object}")
    mesh = geometry(hero)
    video = video_stream(args.video)
    checks = {
        "video_hash": digest(args.video) == args.expected_video_sha,
        "gif_hash": digest(args.gif) == args.expected_gif_sha,
        "video_frames": video["nb_read_frames"] == scene.frame_end - scene.frame_start + 1,
        "video_size": [video["width"], video["height"]] ==
                      [scene.render.resolution_x, scene.render.resolution_y],
        "triangle_budget": mesh["triangles"] <= args.triangle_budget,
        "closed_mesh": mesh["nonmanifold_edges"] == 0 and mesh["loose_vertices"] == 0,
        "material_assignment": bool(mesh["material_slots"]) and
                               all(mesh["material_slots"]),
        "metric_scale": scene.unit_settings.system == "METRIC",
    }
    captures = capture_angles(scene, hero, args.out.parent / (args.out.stem + "-angles"))
    blockers = [name for name, passed in checks.items() if not passed]
    # Technical checks cannot approve visual quality; an inspected beauty and angles are required.
    verdict = ("NO-SHIP" if blockers or args.major or args.visual_verdict == "NO-SHIP" else
               args.visual_verdict if args.visual_verdict else "REVIEW")
    report = {"verdict": verdict, "hero": hero.name, "source_blend": str(args.blend),
              "source_sha256": digest(args.blend), "video": str(args.video),
              "video_sha256": digest(args.video), "gif": str(args.gif),
              "gif_sha256": digest(args.gif), "beauty": {"path": str(args.beauty),
              "sha256": digest(args.beauty)}, "angles": captures, "geometry": mesh,
              "triangle_budget": args.triangle_budget, "video_stream": video,
              "checks": checks, "blockers": blockers,
              "major_defects": args.major, "minor_defects": args.minor,
              "visual_note": args.visual_note or "Awaiting inspection of captured angles and beauty frame"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"QA verdict: {verdict}; {mesh['triangles']} triangles; {len(blockers)} blockers")
    if verdict == "NO-SHIP":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
