"""Resume trusted Blender frame renders without discarding reviewed evidence."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

PIPELINE_VERSION = 1


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def signature(inputs_sha256, scene, blender_version):
    """Bind cached frames to all authored inputs and actual render settings."""
    payload = {"pipeline_version": PIPELINE_VERSION, "inputs_sha256": inputs_sha256,
               "blender": blender_version, "engine": scene.render.engine,
               "width": scene.render.resolution_x, "height": scene.render.resolution_y,
               "fps": scene.render.fps, "fps_base": scene.render.fps_base,
               "frames": [scene.frame_start, scene.frame_end],
               "color_transform": scene.view_settings.view_transform}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def atomic_json(path, payload):
    """A completed frame is reusable only after its hash reaches the manifest."""
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def append_log(path, message):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with Path(path).open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(f"{stamp} {message}\n")
        stream.flush()
        os.fsync(stream.fileno())


def frame_path(cache_dir, frame):
    return Path(cache_dir) / f"frame-{frame:06d}.png"


def verify_manifest(manifest, cache_dir, expected_signature, first, last):
    if (manifest.get("schema_version") != 1 or
            manifest.get("signature") != expected_signature or
            manifest.get("frame_range") != [first, last]):
        raise ValueError("Cached frame manifest differs from current inputs or scene")
    for key, record in manifest.get("frames", {}).items():
        if not key.isdecimal() or not first <= int(key) <= last:
            raise ValueError("Cached frame number is outside the shot")
        path = frame_path(cache_dir, int(key))
        if (not path.is_file() or not path.stat().st_size or
                record.get("sha256") != sha256(path)):
            raise ValueError(f"Cached frame {key} is missing or changed")


def disk_budget(cache_dir, width, height, remaining):
    """Reserve room for raw RGBA frames and the final encode before each batch."""
    free = shutil.disk_usage(cache_dir).free
    required = max(512 * 1024 * 1024, width * height * 4 * remaining + 256 * 1024 * 1024)
    if free < required:
        raise OSError(f"Insufficient render space: need {required} bytes, have {free} bytes")
    return free


def run(scene, output, blend, input_hashes, blender_version, fingerprint,
        probe_video, stop_after=None, batch_frames=48):
    """Render missing frames, encode once, and write a completion marker last."""
    import bpy

    if type(batch_frames) is not int or batch_frames < 1:
        raise ValueError("batch_frames must be positive")
    if stop_after is not None and (type(stop_after) is not int or stop_after < 1):
        raise ValueError("stop_after must be positive")
    output, blend = Path(output), Path(blend)
    cache_dir = output.with_name(output.stem + "-frames")
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cache_dir / "manifest.json"
    log_path = cache_dir / "render.log"
    marker = cache_dir / "complete.json"
    expected_signature = signature(input_hashes, scene, blender_version)
    first, last = scene.frame_start, scene.frame_end
    expected_count = last - first + 1
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        verify_manifest(manifest, cache_dir, expected_signature, first, last)
    else:
        if output.exists() or blend.exists() or any(cache_dir.iterdir()):
            raise FileExistsError("Use a new output path for a new resumable render")
        manifest = {"schema_version": 1, "signature": expected_signature,
                    "frame_range": [first, last], "frames": {}, "blend_sha256": None}
        atomic_json(manifest_path, manifest)
        append_log(log_path, f"START {expected_count} frames signature={expected_signature}")

    if marker.exists():
        completed = json.loads(marker.read_text(encoding="utf-8"))
        stream = probe_video(output) if output.is_file() else {}
        if (completed.get("signature") != expected_signature or not output.is_file() or
                completed.get("video_sha256") != sha256(output) or
                int(stream.get("nb_read_frames", -1)) != expected_count or
                [int(stream.get("width", -1)), int(stream.get("height", -1))] !=
                [scene.render.resolution_x, scene.render.resolution_y]):
            raise ValueError("Completion marker or delivered MP4 changed")
        return {"completed": True, "cache_dir": str(cache_dir), "manifest": manifest,
                "video_sha256": completed["video_sha256"]}

    if manifest.get("blend_sha256"):
        if not blend.is_file() or sha256(blend) != manifest["blend_sha256"]:
            raise ValueError("Cached editable Blender scene changed")
    else:
        if not blend.exists():
            bpy.ops.wm.save_as_mainfile(filepath=str(blend))
        manifest["blend_sha256"] = sha256(blend)
        atomic_json(manifest_path, manifest)

    if hasattr(scene.render.image_settings, "media_type"):
        scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_file_extension = True
    rendered_this_run = 0
    for frame in range(first, last + 1):
        key = str(frame)
        if key in manifest["frames"]:
            continue
        if rendered_this_run % batch_frames == 0:
            disk_budget(cache_dir, scene.render.resolution_x, scene.render.resolution_y,
                        expected_count - len(manifest["frames"]))
        scene.frame_set(frame)
        path = frame_path(cache_dir, frame)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        if not path.is_file() or not path.stat().st_size:
            raise RuntimeError(f"Blender did not write frame {frame}")
        manifest["frames"][key] = {"sha256": fingerprint(path), "bytes": path.stat().st_size}
        atomic_json(manifest_path, manifest)
        append_log(log_path, f"FRAME {frame}/{last} sha256={manifest['frames'][key]['sha256']}")
        rendered_this_run += 1
        if stop_after is not None and rendered_this_run >= stop_after:
            append_log(log_path, f"PAUSE after {rendered_this_run} new frames")
            return {"completed": False, "cache_dir": str(cache_dir), "manifest": manifest}

    if len(manifest["frames"]) != expected_count:
        raise RuntimeError("Frame cache is incomplete")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to encode resumable frames")
    partial = output.with_name(output.stem + ".partial.mp4")
    fps = scene.render.fps / scene.render.fps_base
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(fps),
               "-start_number", str(first), "-i", str(cache_dir / "frame-%06d.png"),
               "-frames:v", str(expected_count), "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", str(partial)]
    encoded = subprocess.run(command, capture_output=True, text=True)
    if encoded.returncode:
        raise RuntimeError("FFmpeg encode failed: " + encoded.stderr[-1200:])
    stream = probe_video(partial)
    if (int(stream.get("nb_read_frames", -1)) != expected_count or
            [int(stream["width"]), int(stream["height"])] !=
            [scene.render.resolution_x, scene.render.resolution_y]):
        raise RuntimeError("Encoded video differs from reviewed frame sequence")
    os.replace(partial, output)
    video_hash = sha256(output)
    atomic_json(marker, {"signature": expected_signature, "video_sha256": video_hash,
                         "frames": expected_count, "resolution":
                         [scene.render.resolution_x, scene.render.resolution_y]})
    append_log(log_path, f"COMPLETE mp4_sha256={video_hash}")
    return {"completed": True, "cache_dir": str(cache_dir), "manifest": manifest,
            "video_sha256": video_hash}
