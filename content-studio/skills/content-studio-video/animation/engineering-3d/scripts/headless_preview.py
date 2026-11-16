"""Render selected frames of a code-authored Blender scene and record a benchmark."""

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import statistics
import sys
import time


def select_frames(requested, span, first, last):
    if span:
        start, end = span
        if not first <= start <= end <= last:
            raise ValueError(f"Preview range must be within the scene's {first}–{last} frames")
        return range(start, end + 1)
    if len(set(requested)) != len(requested) or any(not first <= frame <= last for frame in requested):
        raise ValueError(f"Use unique frame numbers within the scene's {first}–{last} frames")
    return requested


def fingerprint(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inspect_scene(scene, required):
    if scene.camera is None:
        raise ValueError("The builder must assign a render camera")
    missing = [name for name in required if name not in scene.objects]
    if missing:
        raise ValueError(f"Required scene objects missing: {', '.join(missing)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--builder", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path, help="Project JSON read by make_scene")
    parser.add_argument("--dependency", type=Path, action="append", default=[],
                        help="Record an additional authored source file in the manifest")
    parser.add_argument("--out", required=True, type=Path, help="A new output directory")
    parser.add_argument("--size", type=int, nargs=2, metavar=("WIDTH", "HEIGHT"))
    parser.add_argument("--required-object", action="append", default=[])
    frames = parser.add_mutually_exclusive_group(required=True)
    frames.add_argument("--frame", type=int, action="append")
    frames.add_argument("--range", type=int, nargs=2, metavar=("FIRST", "LAST"))
    if argv is None:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    if args.size and min(args.size) <= 0:
        parser.error("Supply positive preview dimensions")

    import bpy

    builder, config = args.builder.resolve(), args.input.resolve()
    out = args.out.resolve()
    dependencies = dict.fromkeys([builder, config, *(path.resolve() for path in args.dependency)])
    digests = {str(path): fingerprint(path) for path in dependencies}
    spec = json.loads(config.read_text(encoding="utf-8-sig"))
    # Project builders may import their own sibling mesh, material, and cue helpers.
    sys.path.insert(0, str(builder.parent))
    make_scene = runpy.run_path(str(builder)).get("make_scene")
    if not callable(make_scene):
        raise ValueError("The builder must define make_scene(spec, spec_dir)")
    scene = make_scene(spec, config.parent)
    inspect_scene(scene, args.required_object)
    selection = select_frames(args.frame, args.range, scene.frame_start, scene.frame_end)
    if args.size:
        scene.render.resolution_x, scene.render.resolution_y = args.size
        scene.render.resolution_percentage = 100
    if hasattr(scene.render.image_settings, "media_type"):
        scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_file_extension = True
    out.mkdir(parents=True, exist_ok=False)
    samples = []
    for frame_number in selection:
        scene.frame_set(frame_number)
        path = out / f"frame-{frame_number:06d}.png"
        scene.render.filepath = str(path)
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True, scene=scene.name)
        elapsed = time.perf_counter() - started
        if not path.is_file() or not path.stat().st_size:
            raise RuntimeError(f"Blender did not write {path.name}")
        samples.append({"frame": frame_number, "file": path.name, "seconds": elapsed,
                        "bytes": path.stat().st_size, "sha256": fingerprint(path)})
    elapsed = [sample["seconds"] for sample in samples]
    report = {
        "blender": bpy.app.version_string,
        "renderer": scene.render.engine,
        "fps": scene.render.fps / scene.render.fps_base,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "resolution_percentage": scene.render.resolution_percentage,
        "required_objects": args.required_object,
        "inputs_sha256": digests,
        "samples": samples,
        "first_render_seconds": elapsed[0],
        "warm_median_seconds": statistics.median(elapsed[1:]) if len(elapsed) > 1 else None,
    }
    (out / "preview.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Rendered {len(samples)} samples to {out}")


if __name__ == "__main__":
    main()
