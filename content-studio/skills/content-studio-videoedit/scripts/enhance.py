#!/usr/bin/env python3
"""Diagnosis-first video enhancement analysis, planning, and selective rendering.

The analyzer deliberately uses FFmpeg + NumPy + Pillow so it works on Windows
without OpenCV, PySceneDetect, or a GPU. Reflection removal is never automatic:
strong reflections are routed to UNSUPPORTED or REVIEW until a licensed backend
has been benchmarked. Color corrections are temporal and quality-gated.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image
import yaml

SCHEMA_VERSION = 1
ANALYSIS_VERSION = "1"
SCENE_THRESHOLD = 0.35
SAMPLE_WIDTH = 160
SAMPLES_PER_SCENE = 3
ACTIONS = ("SKIP", "FIX", "REVIEW", "UNSUPPORTED")


class EnhanceError(RuntimeError):
    pass


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise EnhanceError((result.stderr or result.stdout)[-3000:])
    return result


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_video(path: Path) -> dict:
    data = json.loads(run(["ffprobe", "-v", "error", "-show_streams",
                           "-show_format", "-of", "json", str(path)]).stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise EnhanceError(f"no video stream: {path}")
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    rotation = 0
    for side in video.get("side_data_list", []):
        if "rotation" in side:
            rotation = int(side["rotation"])
    return {
        "duration_seconds": float(data.get("format", {}).get("duration") or 0),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "rotation": rotation,
        "fps": video.get("avg_frame_rate") or video.get("r_frame_rate"),
        "codec": video.get("codec_name"),
        "pix_fmt": video.get("pix_fmt"),
        "color_transfer": video.get("color_transfer"),
        "has_audio": audio is not None,
    }


def detect_scenes(path: Path, duration: float) -> list[tuple[float, float]]:
    """Use FFmpeg scene scores, then fill long gaps with analysis chunks."""
    cuts: list[float] = []
    try:
        result = subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "info",
             "-i", str(path), "-filter:v", f"select='gt(scene,{SCENE_THRESHOLD})',showinfo",
             "-an", "-f", "null", os.devnull],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        for line in (result.stderr or "").splitlines():
            if "pts_time:" in line:
                try:
                    cuts.append(float(line.split("pts_time:")[1].split()[0]))
                except (ValueError, IndexError):
                    continue
    except OSError:
        cuts = []
    bounds = [0.0]
    for cut in sorted(c for c in cuts if 0.5 < c < duration - 0.5):
        if cut - bounds[-1] >= 1.0:
            bounds.append(round(cut, 3))
    bounds.append(round(duration, 3))
    scenes = []
    for start, end in zip(bounds, bounds[1:]):
        # Split a long scene into analysis chunks so corrections stay selective.
        cursor = start
        while end - cursor > 12.0:
            scenes.append((round(cursor, 3), round(cursor + 12.0, 3)))
            cursor += 12.0
        if end - cursor >= 0.4:
            scenes.append((round(cursor, 3), round(end, 3)))
    return scenes or [(0.0, round(duration, 3))]


def extract_frame(path: Path, at: float, width: int = SAMPLE_WIDTH) -> np.ndarray:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{max(0.0, at):.3f}",
         "-i", str(path), "-frames:v", "1", "-vf", f"scale={width}:-2",
         "-f", "image2pipe", "-vcodec", "png", "-"],
        capture_output=True)
    if result.returncode or not result.stdout:
        raise EnhanceError(f"cannot sample frame at {at:.3f}s: {path}")
    image = Image.open(io.BytesIO(result.stdout)).convert("RGB")
    return np.asarray(image, dtype=np.float32) / 255.0


def frame_metrics(rgb: np.ndarray) -> dict:
    luma = (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2])
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    saturation = np.divide(maximum - minimum, maximum,
                           out=np.zeros_like(maximum), where=maximum > 1e-5)
    gray = rgb.mean(axis=2)
    laplacian = (np.abs(4 * gray[1:-1, 1:-1] - gray[:-2, 1:-1] - gray[2:, 1:-1]
                        - gray[1:-1, :-2] - gray[1:-1, 2:]))
    glare = (luma > 0.94) & (saturation < 0.20)
    return {
        "luma_mean": float(luma.mean()),
        "luma_std": float(luma.std()),
        "luma_p05": float(np.percentile(luma, 5)),
        "luma_p50": float(np.percentile(luma, 50)),
        "luma_p95": float(np.percentile(luma, 95)),
        "luma_p99": float(np.percentile(luma, 99)),
        "clip_low": float((luma < 0.02).mean()),
        "clip_high": float((luma > 0.98).mean()),
        "saturation_mean": float(saturation.mean()),
        "channel_r": float(rgb[:, :, 0].mean()),
        "channel_g": float(rgb[:, :, 1].mean()),
        "channel_b": float(rgb[:, :, 2].mean()),
        "glare_fraction": float(glare.mean()),
        "sharpness": float(laplacian.mean()),
    }


def aggregate(samples: list[dict]) -> dict:
    keys = samples[0].keys()
    result = {}
    for key in keys:
        values = sorted(float(sample[key]) for sample in samples)
        result[key] = round(values[len(values) // 2], 5)
    result["glare_fraction"] = round(max(float(s["glare_fraction"]) for s in samples), 5)
    return result


def make_issue(issue_id: str, kind: str, detected: bool, confidence: float,
               severity: str, action: str, **extra) -> dict:
    return {"id": issue_id, "kind": kind, "detected": detected,
            "confidence": round(float(confidence), 3), "severity": severity,
            "action": action, **extra}


def analyze_scene(path: Path, scene_id: str, start: float, end: float,
                  work: Path) -> dict:
    duration = max(0.4, end - start)
    samples = []
    evidence = []
    for index, fraction in enumerate((0.2, 0.5, 0.8), 1):
        at = start + duration * fraction
        rgb = extract_frame(path, at)
        samples.append(frame_metrics(rgb))
        evidence_path = work / "evidence" / f"{scene_id}-{index}.jpg"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray((rgb * 255).astype(np.uint8)).save(evidence_path, quality=88)
        evidence.append(str(evidence_path))
    metrics = aggregate(samples)
    cast = max(metrics["channel_r"], metrics["channel_g"], metrics["channel_b"]) - \
        min(metrics["channel_r"], metrics["channel_g"], metrics["channel_b"])
    issues = {}

    if metrics["luma_mean"] < 0.20:
        confidence = min(0.99, (0.20 - metrics["luma_mean"]) / 0.15)
        action = "FIX" if metrics["luma_mean"] < 0.14 and metrics["luma_p95"] < 0.80 else "REVIEW"
        issues["color"] = make_issue(
            "color", "color", True, confidence,
            "high" if metrics["luma_mean"] < 0.10 else "moderate", action,
            type="underexposure",
            parameters={"brightness": round(min(0.12, (0.42 - metrics["luma_mean"]) * 0.35), 4)})
    elif metrics["luma_p99"] > 0.985 or metrics["clip_high"] > 0.02:
        issues["exposure"] = make_issue(
            "exposure", "exposure", True, 0.9, "high", "REVIEW",
            type="highlight_clipping",
            parameters={"reason": "clipped highlights cannot be reconstructed safely"})
    elif cast > 0.12:
        gains = color_gains(metrics)
        cool_cast = metrics["channel_b"] >= metrics["channel_r"]
        action = ("FIX" if cool_cast and cast > 0.16 and metrics["luma_mean"] < 0.75
                  else "REVIEW")
        issues["white_balance"] = make_issue(
            "white_balance", "color", True, min(0.95, cast / 0.25),
            "high" if cast > 0.18 else "moderate", action,
            type="color_cast", parameters={"gains": gains})
    if metrics["luma_std"] < 0.10:
        issues["contrast"] = make_issue(
            "contrast", "color", True, 0.85, "moderate",
            "FIX" if metrics["luma_std"] < 0.06 else "REVIEW",
            type="low_contrast",
            parameters={"contrast": round(min(1.15, 1.0 + (0.12 - metrics["luma_std"]) * 0.8), 4)})
    if metrics["saturation_mean"] < 0.08 or metrics["saturation_mean"] > 0.80:
        low = metrics["saturation_mean"] < 0.08
        saturation = (1.0 + (0.22 - metrics["saturation_mean"]) * 0.6
                      if low else 1.0 - (metrics["saturation_mean"] - 0.80) * 0.4)
        action = "FIX" if low and metrics["saturation_mean"] < 0.03 else "REVIEW"
        issues["saturation"] = make_issue(
            "saturation", "color", True, 0.8, "moderate", action,
            type="low_saturation" if low else "oversaturation",
            parameters={"saturation": round(max(0.85, min(1.18, saturation)), 4)})
    if metrics["glare_fraction"] > 0.015:
        strong = metrics["glare_fraction"] > 0.06
        issues["reflection"] = make_issue(
            "reflection", "reflection", True,
            min(0.98, 0.55 + metrics["glare_fraction"] * 4),
            "high" if strong else "moderate",
            "UNSUPPORTED" if strong else "REVIEW",
            type="strong_reflection" if strong else "glare",
            parameters={"glare_fraction": metrics["glare_fraction"],
                        "reason": ("licensed reflection-separation backend not configured"
                                   if strong else "conservative highlight review required")})

    actions = [issue["action"] for issue in issues.values()]
    if "FIX" in actions:
        decision = "FIX"
    elif "REVIEW" in actions:
        decision = "REVIEW"
    elif "UNSUPPORTED" in actions:
        decision = "UNSUPPORTED"
    else:
        decision = "SKIP"
    corrections = [correction_filter(issue) for issue in issues.values()
                   if issue["action"] == "FIX" and issue["kind"] == "color"]
    return {
        "id": scene_id,
        "start_seconds": round(start, 3),
        "end_seconds": round(end, 3),
        "metrics": metrics,
        "issues": issues,
        "decision": decision,
        "corrections": [item for item in corrections if item],
        "evidence": evidence,
        "review": {"status": "pending", "preview": None},
    }


def color_gains(metrics: dict) -> dict:
    channels = {"r": metrics["channel_r"], "g": metrics["channel_g"], "b": metrics["channel_b"]}
    target = sum(channels.values()) / 3.0
    return {key: round(max(0.88, min(1.12, target / max(value, 1e-4))), 4)
            for key, value in channels.items()}


def correction_filter(issue: dict) -> str | None:
    params = issue.get("parameters", {})
    if issue["kind"] != "color":
        return None
    parts = []
    if "brightness" in params:
        parts.append(f"eq=brightness={params['brightness']}:contrast=1.02:saturation=1.0")
    if "contrast" in params:
        parts.append(f"eq=contrast={params['contrast']}:brightness=0.0:saturation=1.0")
    if "saturation" in params:
        parts.append(f"eq=saturation={params['saturation']}:brightness=0.0:contrast=1.0")
    if "gains" in params:
        gains = params["gains"]
        parts.append("colorchannelmixer="
                     f"rr={gains['r']}:gg={gains['g']}:bb={gains['b']}")
    return ",".join(parts) if parts else None


def write_contact_sheet(paths: list[Path], target: Path, columns: int = 3) -> None:
    images = []
    for path in paths:
        if path.is_file():
            image = Image.open(path).convert("RGB")
            image.thumbnail((320, 180))
            images.append(image)
    if not images:
        return
    rows = math.ceil(len(images) / columns)
    canvas = Image.new("RGB", (columns * 320, rows * 180), "white")
    for index, image in enumerate(images):
        x = (index % columns) * 320 + (320 - image.width) // 2
        y = (index // columns) * 180 + (180 - image.height) // 2
        canvas.paste(image, (x, y))
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, quality=88)


def write_before_after(source: Path, output: Path, manifest: dict, target: Path) -> None:
    frames = []
    for scene in manifest.get("clips", [{}])[0].get("scenes", []):
        if not approved_scene(scene, True):
            continue
        midpoint = (float(scene["start_seconds"]) + float(scene["end_seconds"])) / 2
        before = extract_frame(source, midpoint, width=480)
        after = extract_frame(output, midpoint, width=480)
        pair = Image.new("RGB", (before.shape[1] * 2, before.shape[0]), "white")
        pair.paste(Image.fromarray((before * 255).astype(np.uint8)), (0, 0))
        pair.paste(Image.fromarray((after * 255).astype(np.uint8)),
                   (before.shape[1], 0))
        frames.append(pair)
    if not frames:
        return
    width = frames[0].width
    height = frames[0].height
    canvas = Image.new("RGB", (width, height * len(frames)), "white")
    for index, frame in enumerate(frames):
        canvas.paste(frame, (0, index * height))
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, quality=88)


def write_preview_clips(source: Path, output: Path, manifest: dict, folder: Path) -> None:
    for scene in manifest.get("clips", [{}])[0].get("scenes", []):
        if not approved_scene(scene, True):
            continue
        start = float(scene["start_seconds"])
        end = float(scene["end_seconds"])
        length = max(0.5, min(3.0, end - start - 0.1))
        midpoint = start + max(0.0, (end - start - length) / 2)
        target = folder / f"{scene['id']}.mp4"
        try:
            run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                 "-ss", f"{midpoint:.3f}", "-t", f"{length:.3f}", "-i", str(source),
                 "-ss", f"{midpoint:.3f}", "-t", f"{length:.3f}", "-i", str(output),
                 "-filter_complex",
                 "[0:v]scale=640:360,setpts=PTS-STARTPTS[a];"
                 "[1:v]scale=640:360,setpts=PTS-STARTPTS[b];"
                 "[a][b]hstack=inputs=2[v]",
                 "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
                 "-crf", "22", "-pix_fmt", "yuv420p", str(target)])
        except EnhanceError:
            target.unlink(missing_ok=True)


def write_html(report: dict, path: Path) -> None:
    rows = []
    for clip in report["clips"]:
        for scene in clip["scenes"]:
            issues = ", ".join(f"{name}:{issue['action']}" for name, issue in scene["issues"].items()) or "none"
            rows.append("<tr>"
                        f"<td>{clip['name']}</td><td>{scene['id']}</td>"
                        f"<td>{scene['start_seconds']:.2f}–{scene['end_seconds']:.2f}</td>"
                        f"<td>{scene['decision']}</td><td>{issues}</td>"
                        f"<td>{scene['metrics']['luma_mean']:.3f}</td>"
                        f"<td>{scene['metrics']['saturation_mean']:.3f}</td>"
                        f"<td>{scene['metrics']['glare_fraction']:.3f}</td></tr>")
    page = ("<!doctype html><meta charset='utf-8'><title>Enhancement analysis</title>"
            "<style>body{font:15px/1.5 system-ui,sans-serif;margin:2rem;color:#0f172a}"
            "h1{margin:0 0 .25rem}p{color:#475569}table{border-collapse:collapse;width:100%}"
            "th,td{padding:.5rem .65rem;border-bottom:1px solid #e2e8f0;text-align:left;font-size:.9rem}"
            "th{background:#f8fafc;text-transform:uppercase;font-size:.75rem;letter-spacing:.04em}"
            "tr:hover td{background:#f8fafc}.review{color:#b45309}.fix{color:#047857}</style>"
            "<h1>Enhancement analysis</h1>"
            f"<p>{len(report['clips'])} clip(s) · generated {report['generated_at']}</p>"
            "<table><thead><tr><th>Clip</th><th>Scene</th><th>Time (s)</th><th>Decision</th>"
            "<th>Issues</th><th>Luma</th><th>Saturation</th><th>Glare</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")


def analyze_clip(path: Path, output_root: Path, force: bool = False,
                 auto_fix: bool = False) -> dict:
    stat = path.stat()
    digest = sha256_file(path)
    stem = path.stem
    work = output_root / stem
    report_path = work / "analysis" / "report.json"
    manifest_path = work / "manifests" / "enhancement.yaml"
    if not force and report_path.is_file() and manifest_path.is_file():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if (report.get("analysis_version") == ANALYSIS_VERSION
                    and report.get("source_hash") == digest):
                return report
        except (OSError, ValueError):
            pass
    work.mkdir(parents=True, exist_ok=True)
    metadata = probe_video(path)
    scenes = detect_scenes(path, metadata["duration_seconds"])
    analyzed = []
    for index, (start, end) in enumerate(scenes, 1):
        scene = analyze_scene(path, f"scene-{index:03d}", start, end, work)
        if auto_fix and scene["decision"] == "FIX" and all(
                issue["action"] in {"FIX", "SKIP"} for issue in scene["issues"].values()):
            scene["review"]["status"] = "auto_approved"
        analyzed.append(scene)
    for folder_name in ("masks", "previews/before-after", "previews/contact-sheets",
                        "rendered"):
        (work / folder_name).mkdir(parents=True, exist_ok=True)
    write_contact_sheet(
        [Path(path_value) for scene in analyzed for path_value in scene["evidence"]],
        work / "previews" / "contact-sheets" / f"{stem}.jpg")
    clip = {
        "name": path.name,
        "source": str(path.resolve()),
        "source_hash": digest,
        "source_bytes": stat.st_size,
        "metadata": metadata,
        "scenes": analyzed,
        "summary": {
            "scenes": len(analyzed),
            "fix": sum(1 for s in analyzed if s["decision"] == "FIX"),
            "review": sum(1 for s in analyzed if s["decision"] == "REVIEW"),
            "unsupported": sum(1 for s in analyzed if s["decision"] == "UNSUPPORTED"),
            "skip": sum(1 for s in analyzed if s["decision"] == "SKIP"),
        },
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": now(),
        "source": str(path.resolve()),
        "source_hash": digest,
        "clips": [clip],
    }
    work.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": now(),
        "source": str(path.resolve()),
        "source_hash": digest,
        "output": None,
        "clips": [{
            "name": path.name,
            "source": str(path.resolve()),
            "source_hash": digest,
            "scenes": [{
                "id": scene["id"],
                "start_seconds": scene["start_seconds"],
                "end_seconds": scene["end_seconds"],
                "decision": scene["decision"],
                "corrections": scene["corrections"],
                "issues": scene["issues"],
                "review": scene["review"],
                "evidence": scene["evidence"],
            } for scene in analyzed],
        }],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    write_html(report, work / "reports" / "quality.html")
    return report


def analyze_folder(folder: Path, output_root: Path | None = None,
                   force: bool = False, auto_fix: bool = False) -> dict:
    output_root = output_root or folder / ".content-studio" / "enhancement"
    sources = sorted(p for p in folder.iterdir() if p.is_file()
                     and p.suffix.lower() in {".mp4", ".mov", ".mkv", ".m4v", ".webm"})
    clips = []
    for source in sources:
        clips.append(analyze_clip(source, output_root, force=force, auto_fix=auto_fix))
    report = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": now(),
        "folder": str(folder.resolve()),
        "clips": [clip for entry in clips for clip in entry["clips"]],
    }
    report_path = output_root / "analysis" / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_html(report, output_root / "reports" / "quality.html")
    return report


def analyze_timeline(timeline_path: Path, output_root: Path | None = None,
                     force: bool = False, auto_fix: bool = False,
                     selected_clips: bool = False) -> dict:
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    source_root = Path(timeline.get("source_root") or timeline_path.parent).resolve()
    names = []
    ranges: dict[str, list[dict]] = {}
    for track in timeline.get("tracks", []):
        if track.get("kind") != "video":
            continue
        for clip in track.get("clips", []):
            name = clip.get("source")
            if not name:
                continue
            if name not in names:
                names.append(name)
                ranges[name] = []
            if clip.get("source_in") is not None and clip.get("source_out") is not None:
                ranges[name].append({"start_seconds": float(clip["source_in"]),
                                     "end_seconds": float(clip["source_out"])})
    if not names:
        raise EnhanceError("timeline has no video clips")
    output_root = output_root or source_root / ".content-studio" / "enhancement"
    clips = []
    timeline_clips = []
    for name in names:
        source = (source_root / name).resolve()
        if not source.is_file():
            raise EnhanceError(f"timeline source missing: {source}")
        result = analyze_clip(source, output_root, force=force, auto_fix=auto_fix)
        clips.append(result)
        timeline_clips.append({
            "source": str(source),
            "source_hash": result["clips"][0]["source_hash"],
            "selected_ranges": ranges[name],
            "manifest": str((output_root / source.stem / "manifests" /
                             "enhancement.yaml").resolve()),
            "summary": result["clips"][0]["summary"],
        })
    report = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": now(),
        "timeline": str(timeline_path.resolve()),
        "selected_clips": selected_clips,
        "clips": [clip for entry in clips for clip in entry["clips"]],
    }
    timeline_manifest = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": report["generated_at"],
        "timeline": str(timeline_path.resolve()),
        "timeline_source_root": str(source_root),
        "clips": timeline_clips,
    }
    (output_root / "manifests").mkdir(parents=True, exist_ok=True)
    (output_root / "manifests" / "timeline-enhancement.yaml").write_text(
        yaml.safe_dump(timeline_manifest, sort_keys=False), encoding="utf-8")
    report["timeline_manifest"] = str(
        (output_root / "manifests" / "timeline-enhancement.yaml").resolve())
    report_path = output_root / "analysis" / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_html(report, output_root / "reports" / "quality.html")
    return report


def approved_scene(scene: dict, allow_pending: bool) -> bool:
    if scene.get("decision") != "FIX" or not scene.get("corrections"):
        return False
    status = (scene.get("review") or {}).get("status")
    return allow_pending or status in {"approved", "auto_approved"}


def render_manifest(manifest_path: Path, output: Path,
                    allow_pending: bool = False) -> dict:
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    clip = (manifest.get("clips") or [None])[0]
    if not clip:
        raise EnhanceError("manifest has no clips")
    source = Path(clip["source"])
    if not source.is_file():
        raise EnhanceError(f"source missing: {source}")
    if output.resolve() == source.resolve():
        raise EnhanceError("output must differ from the source")
    if sha256_file(source) != clip.get("source_hash"):
        raise EnhanceError("source changed since analysis; rerun analysis")
    filters = []
    for scene in clip.get("scenes", []):
        if not approved_scene(scene, allow_pending):
            continue
        start, end = float(scene["start_seconds"]), float(scene["end_seconds"])
        for correction in scene.get("corrections", []):
            filters.append(f"{correction}:enable='between(t,{start:.3f},{end:.3f})'")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not filters:
        shutil.copy2(source, output)
        validation = {"status": "skipped", "reason": "no approved corrections"}
    else:
        run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(source), "-vf", ",".join(filters), "-c:v", "libx264",
             "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "copy", "-movflags", "+faststart", str(output)])
        validation = validate_render(manifest, source, output)
        if validation["status"] == "rejected":
            output.unlink(missing_ok=True)
            raise EnhanceError("quality validation rejected the correction")
    validation_path = manifest_path.parent / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    if validation["status"] == "passed":
        write_before_after(source, output, manifest,
                           manifest_path.parent.parent / "previews" / "before-after" /
                           f"{source.stem}.jpg")
        write_preview_clips(source, output, manifest,
                            manifest_path.parent.parent / "previews" / "before-after")
    manifest["output"] = str(output.resolve())
    manifest["validation"] = validation
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return validation


def validate_render(manifest: dict, source: Path, output: Path) -> dict:
    samples = []
    for scene in manifest.get("clips", [{}])[0].get("scenes", []):
        if not approved_scene(scene, True):
            continue
        midpoint = (float(scene["start_seconds"]) + float(scene["end_seconds"])) / 2
        before = frame_metrics(extract_frame(source, midpoint))
        after = frame_metrics(extract_frame(output, midpoint))
        samples.append({"scene": scene["id"], "before": before, "after": after})
    failures = []
    for sample in samples:
        before, after = sample["before"], sample["after"]
        if abs(after["luma_mean"] - before["luma_mean"]) > 0.20:
            failures.append(f"{sample['scene']}: luma changed too much")
        if abs(after["saturation_mean"] - before["saturation_mean"]) > 0.30:
            failures.append(f"{sample['scene']}: saturation changed too much")
        if after["clip_high"] - before["clip_high"] > 0.05:
            failures.append(f"{sample['scene']}: clipping increased")
    return {"status": "rejected" if failures else "passed",
            "failures": failures, "samples": samples}


def run_benchmark(source: Path, config_path: Path, output_root: Path,
                  frames: int = 3, timeout: int = 300) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    name = str(config.get("name") or "external").strip()
    command = config.get("command")
    if not isinstance(command, list) or not command:
        raise EnhanceError("backend config needs a command array")
    template = " ".join(str(part) for part in command)
    if "{input}" not in template or "{output}" not in template:
        raise EnhanceError("backend command needs {input} and {output} placeholders")
    work = output_root / name
    work.mkdir(parents=True, exist_ok=True)
    report = analyze_clip(source, work / "analysis")
    scenes = [scene for scene in report["clips"][0]["scenes"]
              if "reflection" in scene["issues"]]
    if not scenes:
        raise EnhanceError("no reflection evidence in this clip")
    metadata = report["clips"][0]["metadata"]
    sample_width = min(1280, max(320, int(metadata.get("width") or 1280)))
    results = []
    for index, scene in enumerate(scenes[:max(1, frames)], 1):
        midpoint = (float(scene["start_seconds"]) + float(scene["end_seconds"])) / 2
        before_rgb = extract_frame(source, midpoint, width=sample_width)
        input_path = work / f"input-{index:03d}.png"
        output_path = work / f"output-{index:03d}.png"
        Image.fromarray((before_rgb * 255).astype(np.uint8)).save(input_path)
        argv = [str(part).replace("{input}", str(input_path.resolve()))
                .replace("{output}", str(output_path.resolve())) for part in command]
        started = time.perf_counter()
        try:
            proc = subprocess.run(argv, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=timeout)
            runtime = time.perf_counter() - started
            if proc.returncode != 0:
                raise EnhanceError((proc.stderr or proc.stdout)[-1000:])
            if not output_path.is_file():
                raise EnhanceError("backend did not write the output image")
            after_rgb = np.asarray(Image.open(output_path).convert("RGB"),
                                   dtype=np.float32) / 255.0
            if after_rgb.shape != before_rgb.shape:
                raise EnhanceError("backend changed image dimensions")
            before = frame_metrics(before_rgb)
            after = frame_metrics(after_rgb)
            before["scene"] = scene["id"]
            after["scene"] = scene["id"]
            results.append({
                "scene": scene["id"],
                "runtime_seconds": round(runtime, 3),
                "before": before,
                "after": after,
                "glare_reduction": round(before["glare_fraction"] - after["glare_fraction"], 5),
                "luma_delta": round(abs(after["luma_mean"] - before["luma_mean"]), 5),
                "sharpness_ratio": round(after["sharpness"] / max(before["sharpness"], 1e-6), 3),
                "accepted": (abs(after["luma_mean"] - before["luma_mean"]) <= 0.20
                             and after["sharpness"] >= before["sharpness"] * 0.5),
            })
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            results.append({"scene": scene["id"], "error": str(exc),
                            "accepted": False})
    valid = [item for item in results if "error" not in item]
    summary = {
        "backend": name,
        "license": config.get("license"),
        "checkpoint": config.get("checkpoint"),
        "samples": len(results),
        "accepted": sum(1 for item in results if item.get("accepted")),
        "failed": sum(1 for item in results if "error" in item),
        "mean_runtime_seconds": round(
            sum(item["runtime_seconds"] for item in valid) / len(valid), 3) if valid else None,
        "mean_glare_reduction": round(
            sum(item["glare_reduction"] for item in valid) / len(valid), 5) if valid else None,
    }
    document = {"schema_version": SCHEMA_VERSION, "generated_at": now(),
                "source": str(source.resolve()), "config": str(config_path.resolve()),
                "summary": summary, "results": results}
    (work / "benchmarks.json").write_text(json.dumps(document, indent=2) + "\n",
                                          encoding="utf-8")
    rows = "".join(
        "<tr>"
        f"<td>{item.get('scene')}</td>"
        f"<td>{item.get('runtime_seconds', '')}</td>"
        f"<td>{item.get('glare_reduction', '')}</td>"
        f"<td>{item.get('luma_delta', '')}</td>"
        f"<td>{item.get('sharpness_ratio', '')}</td>"
        f"<td>{'yes' if item.get('accepted') else 'no'}</td>"
        f"<td>{item.get('error', '')}</td></tr>" for item in results)
    page = ("<!doctype html><meta charset='utf-8'><title>Reflection benchmark</title>"
            "<style>body{font:15px/1.5 system-ui,sans-serif;margin:2rem;color:#0f172a}"
            "table{border-collapse:collapse;width:100%}th,td{padding:.5rem .65rem;"
            "border-bottom:1px solid #e2e8f0;text-align:left}"
            "th{background:#f8fafc;text-transform:uppercase;font-size:.75rem}</style>"
            f"<h1>Reflection benchmark: {name}</h1>"
            f"<p>License: {config.get('license') or 'unspecified'} · "
            f"accepted {summary['accepted']}/{summary['samples']} · "
            f"mean runtime {summary['mean_runtime_seconds'] or '-'}s</p>"
            "<table><thead><tr><th>Scene</th><th>Runtime (s)</th><th>Glare reduction</th>"
            "<th>Luma delta</th><th>Sharpness ratio</th><th>Accepted</th><th>Error</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>")
    (work / "benchmark.html").write_text(page, encoding="utf-8")
    return document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("analyze", "plan"):
        item = sub.add_parser(name)
        item.add_argument("--folder", type=Path, help="analyze every video in a folder")
        item.add_argument("--file", type=Path, help="analyze one video")
        item.add_argument("--timeline", type=Path, help="analyze sources referenced by an editable timeline")
        item.add_argument("--selected-clips", action="store_true",
                          help="analyze only sources referenced by the timeline")
        item.add_argument("--out", type=Path, help="analysis output root")
        item.add_argument("--auto-fix", action="store_true",
                          help="auto-approve scenes where every detected issue is FIX/SKIP")
        item.add_argument("--force", action="store_true")
        item.add_argument("--json", action="store_true")
    render = sub.add_parser("render")
    render.add_argument("--manifest", type=Path, required=True)
    render.add_argument("--output", type=Path, required=True)
    render.add_argument("--allow-pending", action="store_true")
    benchmark = sub.add_parser("benchmark",
                               help="benchmark an external reflection backend on evidence frames")
    benchmark.add_argument("--file", type=Path, required=True)
    benchmark.add_argument("--config", type=Path, required=True,
                           help="JSON adapter with name, license, checkpoint, and command")
    benchmark.add_argument("--out", type=Path)
    benchmark.add_argument("--frames", type=int, default=3)
    benchmark.add_argument("--timeout", type=int, default=300)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.action in {"analyze", "plan"}:
            if sum(bool(value) for value in (args.folder, args.file, args.timeline)) != 1:
                raise EnhanceError("use exactly one of --folder, --file, or --timeline")
            if args.file:
                out = args.out or args.file.parent / ".content-studio" / "enhancement"
                report = analyze_clip(args.file, out, force=args.force,
                                      auto_fix=args.auto_fix)
                report = {"schema_version": SCHEMA_VERSION, "analysis_version": ANALYSIS_VERSION,
                          "generated_at": now(), "clips": report["clips"]}
            elif args.timeline:
                report = analyze_timeline(args.timeline, args.out, force=args.force,
                                          auto_fix=args.auto_fix,
                                          selected_clips=args.selected_clips)
            else:
                report = analyze_folder(args.folder, args.out, force=args.force,
                                        auto_fix=args.auto_fix)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                for clip in report["clips"]:
                    print(f"{clip['name']}: {clip['summary']}")
            return 0
        if args.action == "benchmark":
            out = args.out or args.file.parent / ".content-studio" / "enhancement" / "benchmarks"
            document = run_benchmark(args.file, args.config, out,
                                     frames=args.frames, timeout=args.timeout)
            print(json.dumps(document["summary"], indent=2))
            return 0
        validation = render_manifest(args.manifest, args.output, args.allow_pending)
        print(json.dumps(validation, indent=2))
        return 0
    except (EnhanceError, OSError, ValueError) as exc:
        print(f"enhance: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
