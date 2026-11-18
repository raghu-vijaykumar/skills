"""Render a project-authored Blender shot through the preview builder contract."""

import argparse
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

ENGINEERING_SCRIPTS = Path(__file__).resolve().parents[2] / "engineering-3d" / "scripts"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ENGINEERING_SCRIPTS))
from headless_preview import fingerprint, inspect_scene
from resume_render import run as run_resumable
from shot_spec import validate_scene, validate_spec


def probe_video(path):
    """Check the encoded artifact, since a Blender render call alone is not delivery proof."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required to validate the rendered MP4")
    result = subprocess.run(
        [ffprobe, "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,nb_read_frames", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    streams = json.loads(result.stdout).get("streams", [])
    if len(streams) != 1:
        raise ValueError("Rendered video must have one picture stream")
    return streams[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--builder", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--dependency", type=Path, action="append", default=[])
    parser.add_argument("--required-object", action="append", default=[])
    parser.add_argument("--size", type=int, nargs=2, metavar=("WIDTH", "HEIGHT"))
    parser.add_argument("--resumable", action="store_true")
    parser.add_argument("--batch-frames", type=int, default=48)
    parser.add_argument("--stop-after", type=int, help="Pause after this many new frames for a bounded run")
    if argv is None:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    if args.out.suffix.lower() != ".mp4":
        parser.error("--out must end in .mp4")
    if args.size and min(args.size) <= 0:
        parser.error("--size must contain positive dimensions")
    if args.stop_after is not None and not args.resumable:
        parser.error("--stop-after requires --resumable")

    import bpy

    builder = args.builder.resolve(strict=True)
    config = args.input.resolve(strict=True)
    output = args.out.resolve()
    spec = json.loads(config.read_text(encoding="utf-8-sig"))
    contract = validate_spec(spec, config.parent)
    # A changed renderer or validator must invalidate a resumable frame cache too.
    runtime_sources = [Path(__file__).resolve(), Path(__file__).resolve().parent / "resume_render.py",
                       Path(__file__).resolve().parent / "shot_spec.py",
                       ENGINEERING_SCRIPTS / "headless_preview.py"]
    dependencies = dict.fromkeys([builder, config, *(p.resolve(strict=True) for p in args.dependency),
                                  *(config.parent / name for name in contract["asset_hashes"]),
                                  *runtime_sources])
    inputs_sha256 = {str(p): fingerprint(p) for p in dependencies}
    required = list(dict.fromkeys([*contract["required_objects"], *args.required_object]))
    if any(not isinstance(name, str) or not name for name in required):
        raise ValueError("required_objects must contain nonempty object names")
    # Project builders may import trusted sibling geometry, material, and cue helpers.
    sys.path.insert(0, str(builder.parent))
    make_scene = runpy.run_path(str(builder)).get("make_scene")
    if not callable(make_scene):
        raise ValueError("The builder must define make_scene(spec, spec_dir)")
    scene = make_scene(spec, config.parent)
    inspect_scene(scene, required)
    validate_scene(scene, spec, contract)
    if scene.frame_end < scene.frame_start or scene.camera is None:
        raise ValueError("Invalid scene frame range or camera")
    if args.size:
        if contract["schema_version"] == 2 and args.size != [spec["width"], spec["height"]]:
            raise ValueError("A version 2 shot cannot override its reviewed dimensions")
        scene.render.resolution_x, scene.render.resolution_y = args.size
        scene.render.resolution_percentage = 100
    if scene.render.resolution_percentage != 100:
        raise ValueError("Full render requires 100% scene resolution")
    output.parent.mkdir(parents=True, exist_ok=True)
    blend = output.with_suffix(".blend")
    if not args.resumable and (output.exists() or blend.exists()):
        raise FileExistsError("Use a new output path for each reviewed render")
    if hasattr(scene.render.image_settings, "media_type"):
        scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.filepath = str(output)
    if args.resumable:
        result = run_resumable(scene, output, blend, inputs_sha256, bpy.app.version_string,
                               fingerprint, probe_video, args.stop_after, args.batch_frames)
        if not result["completed"]:
            print(f"Paused resumable shot with {len(result['manifest']['frames'])} cached frames")
            return
    else:
        # Save the editable project with the same output settings used for its evidence render.
        bpy.ops.wm.save_as_mainfile(filepath=str(blend))
        bpy.ops.render.render(animation=True, scene=scene.name)
    if not output.is_file() or not output.stat().st_size:
        raise RuntimeError("Blender did not create a nonempty MP4")
    stream = probe_video(output)
    expected = scene.frame_end - scene.frame_start + 1
    if int(stream.get("nb_read_frames", -1)) != expected:
        raise RuntimeError(f"Frame mismatch: expected {expected}, got {stream.get('nb_read_frames')}")
    if [int(stream["width"]), int(stream["height"])] != [scene.render.resolution_x, scene.render.resolution_y]:
        raise RuntimeError("Rendered dimensions differ from the authored scene")
    report = {
        "builder": str(builder), "input": str(config), "inputs_sha256": inputs_sha256,
        "blender": bpy.app.version_string, "renderer": scene.render.engine,
        "fps": scene.render.fps / scene.render.fps_base,
        "frames": expected, "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "required_objects": required,
        "shot_contract": contract,
        "render_mode": "resumable" if args.resumable else "direct",
        "frame_cache": result["cache_dir"] if args.resumable else None,
        "blend": {"path": str(blend), "sha256": fingerprint(blend)},
        "video": {"path": str(output), "sha256": fingerprint(output), "bytes": output.stat().st_size},
    }
    output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Rendered and validated {expected} frames: {output}")


if __name__ == "__main__":
    main()
