#!/usr/bin/env python3
"""Diagnosis-first reflection detection, conservative correction, and benchmarks.

The detector looks for bright, low-saturation, low-texture regions that persist
across a scene.  It deliberately does not claim to separate a reflected layer
from the scene behind glass: single-image reflection separation is under-
determined.  Minor glare/veil candidates can receive a masked highlight
compression; content-rich or large reflections remain REVIEW/UNSUPPORTED until
a licensed backend has been benchmarked on the clip's own evidence frames.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

import enhance

SCHEMA_VERSION = 1
ANALYSIS_VERSION = "1"
SAMPLE_WIDTH = 640
FRAMES_PER_SCENE = 5
MAX_SCENE_SECONDS = 6.0
MINOR_FILTER = "eq=brightness=-0.10:contrast=1.05:saturation=1.0"
PREVIEW_FILTER = "eq=brightness=-0.08:contrast=1.12:saturation=1.0"
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".m4v", ".webm"}


class ReflectionError(RuntimeError):
    pass


def _shift(mask: np.ndarray, dy: int, dx: int, radius: int = 1) -> np.ndarray:
    padded = np.pad(mask, ((radius, radius), (radius, radius)),
                    mode="constant")
    height, width = mask.shape
    return padded[radius + dy:radius + dy + height,
                  radius + dx:radius + dx + width]


def _dilate(mask: np.ndarray, radius: int = 1) -> np.ndarray:
    result = mask.copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dy or dx:
                result = result | _shift(mask, dy, dx, radius)
    return result


def _erode(mask: np.ndarray, radius: int = 1) -> np.ndarray:
    result = mask.copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dy or dx:
                result = result & _shift(mask, dy, dx, radius)
    return result


def reflection_masks(rgb: np.ndarray) -> dict:
    """Return candidate glare and veil masks for one RGB frame.

    The masks are evidence, not a separation result.  A bright sky, a lamp, or
    a white sign can satisfy the same thresholds, so every caller must keep the
    review gate.
    """
    luma = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    saturation = np.divide(maximum - minimum, maximum,
                           out=np.zeros_like(maximum), where=maximum > 1e-5)
    gradient_y, gradient_x = np.gradient(luma)
    gradient = np.hypot(gradient_x, gradient_y)
    smooth = gradient <= 0.035
    glare = ((luma >= 0.90) & (saturation <= 0.18) & (gradient <= 0.12))
    veil = ((luma >= 0.58) & (luma < 0.96) & (saturation <= 0.14) & smooth)
    # Close pinholes, remove thin high-detail structures, then leave a small
    # margin so the evidence remains readable after scaling for display.
    candidate = _erode(_dilate(glare | veil, 1), 1)
    candidate = _dilate(_erode(candidate, 2), 2)
    candidate = _dilate(candidate, 1)
    return {
        "luma": luma,
        "saturation": saturation,
        "gradient": gradient,
        "glare": glare,
        "veil": veil,
        "candidate": candidate,
    }


def fraction(mask: np.ndarray) -> float:
    return float(mask.mean())


def save_mask(mask: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((mask.astype(np.uint8) * 255)).save(path)


def save_overlay(rgb: np.ndarray, mask: np.ndarray, path: Path) -> None:
    overlay = rgb.copy()
    tint = np.zeros_like(overlay)
    tint[:, :, 0] = 1.0
    selected = mask.astype(bool)
    overlay[selected] = 0.55 * overlay[selected] + 0.45 * tint[selected]
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((np.clip(overlay, 0, 1) * 255).astype(np.uint8)).save(
        path, quality=88)


def split_long_scenes(scenes: list[tuple[float, float]],
                      maximum: float = MAX_SCENE_SECONDS) -> list[tuple[float, float]]:
    result = []
    for start, end in scenes:
        cursor = start
        while end - cursor > maximum:
            result.append((round(cursor, 3), round(cursor + maximum, 3)))
            cursor += maximum
        if end - cursor >= 0.4:
            result.append((round(cursor, 3), round(end, 3)))
    return result or scenes


def analyze_scene(path: Path, scene_id: str, start: float, end: float,
                  work: Path) -> dict:
    duration = max(0.4, end - start)
    samples = []
    masks = []
    originals = []
    overlays = []
    mask_paths = []
    for index, position in enumerate(np.linspace(0.1, 0.9, FRAMES_PER_SCENE), 1):
        at = start + duration * float(position)
        rgb = enhance.extract_frame(path, at, width=SAMPLE_WIDTH)
        parts = reflection_masks(rgb)
        samples.append({
            "at_seconds": round(at, 3),
            "glare_fraction": round(fraction(parts["glare"]), 5),
            "veil_fraction": round(fraction(parts["veil"]), 5),
            "candidate_fraction": round(fraction(parts["candidate"]), 5),
            "sharpness": round(float(parts["gradient"].mean()), 5),
        })
        masks.append(parts["candidate"])
        original = work / "analysis" / "evidence" / f"{scene_id}-{index:02d}.jpg"
        overlay = work / "analysis" / "overlays" / f"{scene_id}-{index:02d}.jpg"
        mask_path = work / "masks" / f"{scene_id}-{index:02d}.png"
        original.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray((rgb * 255).astype(np.uint8)).save(original, quality=88)
        save_overlay(rgb, parts["candidate"], overlay)
        save_mask(parts["candidate"], mask_path)
        originals.append(str(original))
        overlays.append(str(overlay))
        mask_paths.append(str(mask_path))

    stack = np.stack(masks).astype(np.float32)
    persistence = stack.mean(axis=0)
    candidate_values = [item["candidate_fraction"] for item in samples]
    glare_values = [item["glare_fraction"] for item in samples]
    veil_values = [item["veil_fraction"] for item in samples]
    metrics = {
        "candidate_mean": round(float(np.mean(candidate_values)), 5),
        "candidate_peak": round(float(np.max(candidate_values)), 5),
        "glare_mean": round(float(np.mean(glare_values)), 5),
        "glare_peak": round(float(np.max(glare_values)), 5),
        "veil_mean": round(float(np.mean(veil_values)), 5),
        "veil_peak": round(float(np.max(veil_values)), 5),
        "persistent_fraction": round(float((persistence >= 0.6).mean()), 5),
        "flicker": round(float(np.std(candidate_values)), 5),
        "sampled_frames": FRAMES_PER_SCENE,
        "sample_width": SAMPLE_WIDTH,
    }
    decision, reflection_type, severity, confidence = classify(metrics)
    best = int(np.argmax(candidate_values))
    issue = {
        "id": "reflection",
        "kind": "reflection",
        "detected": metrics["candidate_peak"] >= 0.004,
        "type": reflection_type,
        "severity": severity,
        "action": decision,
        "confidence": round(confidence, 3),
        "selected": decision,
        "alternatives": [
            "leave the source unchanged",
            "masked glare/veil compression",
            "licensed reflection-separation backend benchmark",
        ],
        "parameters": {
            "reason": reason_for(decision, reflection_type),
            "candidate_peak": metrics["candidate_peak"],
            "persistent_fraction": metrics["persistent_fraction"],
            "evidence_mask": mask_paths[best],
            "preview_filter": PREVIEW_FILTER,
        },
    }
    region_masks = []
    corrections = []
    if decision == "FIX":
        region_masks.append({
            "start_seconds": round(start, 3),
            "end_seconds": round(end, 3),
            "filter": MINOR_FILTER,
            "mask": mask_paths[best],
        })
        corrections = [MINOR_FILTER]
    return {
        "id": scene_id,
        "start_seconds": round(start, 3),
        "end_seconds": round(end, 3),
        "metrics": metrics,
        "samples": samples,
        "issue": issue,
        "decision": decision,
        "corrections": corrections,
        "region_masks": region_masks,
        "evidence": {"originals": originals, "overlays": overlays,
                     "masks": mask_paths},
        "review": {"status": "pending", "preview": None},
    }


def classify(metrics: dict) -> tuple[str, str, str, float]:
    peak = metrics["candidate_peak"]
    mean = metrics["candidate_mean"]
    persistent = metrics["persistent_fraction"]
    glare_peak = metrics["glare_peak"]
    if peak < 0.004:
        return "SKIP", "none", "none", 0.0
    if (persistent >= 0.06 or peak >= 0.20 or mean >= 0.12
            or glare_peak >= 0.12):
        confidence = min(0.98, 0.60 + persistent * 2.0 + peak)
        return "UNSUPPORTED", "strong_reflection", "high", confidence
    if mean >= 0.05 or peak >= 0.10:
        confidence = min(0.95, 0.45 + mean * 2.0 + persistent)
        return "REVIEW", "content_reflection", "moderate", confidence
    if persistent >= 0.02 and mean >= 0.004:
        confidence = min(0.92, 0.40 + persistent * 2.0 + mean)
        return "FIX", "glare_veil", "minor", confidence
    confidence = min(0.85, 0.30 + peak * 2.0)
    return "REVIEW", "transient_reflection", "low", confidence


def reason_for(decision: str, reflection_type: str) -> str:
    if decision == "FIX":
        return "small persistent glare/veil; masked highlight compression"
    if decision == "REVIEW":
        return ("content-rich or transient candidate; inspect evidence and "
                "compare a bounded preview")
    if decision == "UNSUPPORTED":
        return "strong or content-rich reflection; licensed separation backend required"
    return "no reflection candidate above threshold"


def write_html(report: dict, path: Path) -> None:
    rows = []
    for clip in report["clips"]:
        for scene in clip["scenes"]:
            issue = scene["issue"]
            overlay = Path(scene["evidence"]["overlays"][0]).as_uri() if scene["evidence"]["overlays"] else ""
            rows.append(
                "<tr>"
                f"<td>{clip['name']}</td><td>{scene['id']}</td>"
                f"<td>{scene['start_seconds']:.2f}–{scene['end_seconds']:.2f}</td>"
                f"<td>{scene['decision']}</td><td>{issue['type']}</td>"
                f"<td>{scene['metrics']['candidate_mean']:.3f}</td>"
                f"<td>{scene['metrics']['persistent_fraction']:.3f}</td>"
                f"<td>{scene['metrics']['glare_peak']:.3f}</td>"
                f"<td>{scene['metrics']['flicker']:.3f}</td>"
                f"<td><a href='{overlay}'>evidence</a></td></tr>")
    page = ("<!doctype html><meta charset='utf-8'><title>Reflection analysis</title>"
            "<style>body{font:15px/1.5 system-ui,sans-serif;margin:2rem;color:#0f172a}"
            "h1{margin:0 0 .25rem}p{color:#475569}table{border-collapse:collapse;width:100%}"
            "th,td{padding:.5rem .65rem;border-bottom:1px solid #e2e8f0;text-align:left;"
            "font-size:.9rem}th{background:#f8fafc;text-transform:uppercase;font-size:.75rem}"
            "tr:hover td{background:#f8fafc}a{color:#0369a1}</style>"
            "<h1>Reflection analysis</h1>"
            f"<p>{len(report['clips'])} clip(s) · generated {report['generated_at']} · "
            "candidate masks are evidence, not a separation result</p>"
            "<table><thead><tr><th>Clip</th><th>Scene</th><th>Time (s)</th><th>Decision</th>"
            "<th>Type</th><th>Candidate</th><th>Persistent</th><th>Glare peak</th>"
            "<th>Flicker</th><th>Evidence</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")


def _check_hdr(metadata: dict) -> None:
    transfer = str(metadata.get("color_transfer") or "").lower()
    if transfer in {"smpte2084", "arib-std-b67"}:
        raise ReflectionError(
            "HDR/HLG source needs an explicit tone-map decision before any "
            "reflection correction")


def detect_clip(path: Path, output_root: Path, force: bool = False) -> dict:
    path = path.resolve()
    if not path.is_file():
        raise ReflectionError(f"source missing: {path}")
    digest = enhance.sha256_file(path)
    work = output_root / path.stem
    report_path = work / "analysis" / "report.json"
    manifest_path = work / "manifests" / "reflection.yaml"
    if not force and report_path.is_file() and manifest_path.is_file():
        try:
            cached = json.loads(report_path.read_text(encoding="utf-8"))
            if (cached.get("analysis_version") == ANALYSIS_VERSION
                    and cached.get("source_hash") == digest):
                return cached
        except (OSError, ValueError):
            pass

    metadata = enhance.probe_video(path)
    _check_hdr(metadata)
    scenes = split_long_scenes(
        enhance.detect_scenes(path, metadata["duration_seconds"]))
    analyzed = []
    for index, (start, end) in enumerate(scenes, 1):
        analyzed.append(analyze_scene(path, f"scene-{index:03d}",
                                      start, end, work))
    for folder in ("previews", "rendered", "benchmarks"):
        (work / folder).mkdir(parents=True, exist_ok=True)
    enhance.write_contact_sheet(
        [Path(item) for scene in analyzed
         for item in scene["evidence"]["overlays"]],
        work / "previews" / "contact-sheet.jpg")

    summary = {
        "scenes": len(analyzed),
        "fix": sum(1 for scene in analyzed if scene["decision"] == "FIX"),
        "review": sum(1 for scene in analyzed if scene["decision"] == "REVIEW"),
        "unsupported": sum(1 for scene in analyzed
                           if scene["decision"] == "UNSUPPORTED"),
        "skip": sum(1 for scene in analyzed if scene["decision"] == "SKIP"),
    }
    clip = {
        "name": path.name,
        "source": str(path),
        "source_hash": digest,
        "source_bytes": path.stat().st_size,
        "metadata": metadata,
        "scenes": analyzed,
        "summary": summary,
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": enhance.now(),
        "source": str(path),
        "source_hash": digest,
        "clips": [clip],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": report["generated_at"],
        "source": str(path),
        "source_hash": digest,
        "output": None,
        "clips": [{
            "name": path.name,
            "source": str(path),
            "source_hash": digest,
            "scenes": [{
                "id": scene["id"],
                "start_seconds": scene["start_seconds"],
                "end_seconds": scene["end_seconds"],
                "decision": scene["decision"],
                "corrections": scene["corrections"],
                "region_masks": scene["region_masks"],
                "issue": scene["issue"],
                "review": scene["review"],
                "evidence": scene["evidence"],
            } for scene in analyzed],
        }],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(enhance.yaml.safe_dump(manifest, sort_keys=False),
                             encoding="utf-8")
    write_html(report, work / "reports" / "reflection.html")
    return report


def detect_folder(folder: Path, output_root: Path | None = None,
                  force: bool = False) -> dict:
    output_root = output_root or folder / ".content-studio" / "reflection"
    sources = sorted(path for path in folder.iterdir()
                     if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES)
    reports = [detect_clip(source, output_root, force=force) for source in sources]
    report = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": enhance.now(),
        "folder": str(folder.resolve()),
        "clips": [clip for entry in reports for clip in entry["clips"]],
    }
    report_path = output_root / "analysis" / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_html(report, output_root / "reports" / "reflection.html")
    return report


def approved(scene: dict, allow_pending: bool = False) -> bool:
    if scene.get("decision") != "FIX" or not scene.get("region_masks"):
        return False
    status = (scene.get("review") or {}).get("status")
    return allow_pending or status in {"approved", "auto_approved"}


def load_manifest(manifest_path: Path) -> dict:
    manifest = enhance.yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    clip = (manifest.get("clips") or [None])[0]
    if not clip:
        raise ReflectionError("manifest has no clips")
    source = Path(clip["source"])
    if not source.is_file():
        raise ReflectionError(f"source missing: {source}")
    if enhance.sha256_file(source) != clip.get("source_hash"):
        raise ReflectionError("source changed since detection; rerun detect")
    _check_hdr(enhance.probe_video(source))
    return manifest


def _mask_command(source: Path, output: Path, masks: list[dict],
                  duration: float, trim: tuple[float, float] | None = None,
                  filter_override: str | None = None) -> list[str]:
    metadata = enhance.probe_video(source)
    width = int(metadata["display_width"])
    height = int(metadata["display_height"])
    # Pin the working format; without this FFmpeg can negotiate a gray output
    # when the mask input is gray, which silently desaturates the whole clip.
    graph = ["[0:v]format=yuv444p,split=2[base][over]"]
    overlay_filter = filter_override or str(
        masks[0].get("filter") or MINOR_FILTER)
    graph.append(f"[over]{overlay_filter}[overc]")
    command = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error"]
    if trim:
        command += ["-ss", f"{trim[0]:.3f}", "-t", f"{trim[1]:.3f}"]
    command += ["-i", str(source)]
    previous = "[base]"
    for index, item in enumerate(masks, 1):
        mask_path = Path(item["mask"])
        if not mask_path.is_file():
            raise ReflectionError(f"mask missing: {mask_path}")
        command += ["-loop", "1", "-framerate", "30", "-i", str(mask_path)]
        graph.append(f"[{index}:v]scale={width}:{height},format=gray[mask{index}]")
        if trim:
            condition = "between(t,0,100000)"
        else:
            condition = (f"between(t,{float(item['start_seconds']):.3f},"
                         f"{float(item['end_seconds']):.3f})")
        graph.append(f"{previous}[overc][mask{index}]maskedmerge="
                     f"enable='{condition}'[m{index}]")
        previous = f"[m{index}]"
    command += ["-filter_complex", ";".join(graph), "-map", previous,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-c:a", "copy",
                "-t", f"{duration:.3f}", "-movflags", "+faststart", str(output)]
    return command


def _sample_metrics(path: Path, at: float) -> dict:
    rgb = enhance.extract_frame(path, at, width=SAMPLE_WIDTH)
    parts = reflection_masks(rgb)
    metrics = enhance.frame_metrics(rgb)
    return {
        "candidate_fraction": round(fraction(parts["candidate"]), 5),
        "glare_fraction": round(fraction(parts["glare"]), 5),
        "luma_mean": round(metrics["luma_mean"], 5),
        "saturation_mean": round(metrics["saturation_mean"], 5),
        "clip_high": round(metrics["clip_high"], 5),
        "sharpness": round(metrics["sharpness"], 5),
    }


def _write_compare(source: Path, output: Path, start: float, length: float,
                   target: Path) -> Path | None:
    try:
        enhance.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(source),
            "-i", str(output),
            "-filter_complex",
            "[0:v]scale=960:-2,setpts=PTS-STARTPTS[a];"
            "[1:v]scale=960:-2,setpts=PTS-STARTPTS[b];"
            "[a][b]hstack=inputs=2[v]",
            "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "22", "-pix_fmt", "yuv420p", str(target)])
        return target
    except enhance.EnhanceError:
        target.unlink(missing_ok=True)
        return None


def validate(manifest: dict, source: Path, output: Path,
             allow_pending: bool = False) -> dict:
    samples = []
    checks = []
    for scene in manifest.get("clips", [{}])[0].get("scenes", []):
        if not approved(scene, allow_pending):
            continue
        start = float(scene["start_seconds"])
        end = float(scene["end_seconds"])
        before_items = []
        after_items = []
        for position in (0.2, 0.5, 0.8):
            at = start + (end - start) * position
            before = _sample_metrics(source, at)
            after = _sample_metrics(output, at)
            item = {"scene": scene["id"], "at_seconds": round(at, 3),
                    "before": before, "after": after}
            samples.append(item)
            before_items.append(before)
            after_items.append(after)
        before = {key: float(np.mean([item[key] for item in before_items]))
                  for key in before_items[0]}
        after = {key: float(np.mean([item[key] for item in after_items]))
                 for key in after_items[0]}
        issue = scene.get("issue") or {}
        reduction = (before["candidate_fraction"] - after["candidate_fraction"])
        checks.append({
            "scene": scene["id"],
            "issue": issue.get("type") or "reflection",
            "candidate_reduction": round(reduction, 5),
            "minimum": 0.0005,
            "passed": reduction >= 0.0005,
        })
    failures = []
    for sample in samples:
        before, after = sample["before"], sample["after"]
        if abs(after["luma_mean"] - before["luma_mean"]) > 0.15:
            failures.append(f"{sample['scene']} at {sample['at_seconds']}s: luma changed too much")
        if abs(after["saturation_mean"] - before["saturation_mean"]) > 0.30:
            failures.append(f"{sample['scene']} at {sample['at_seconds']}s: saturation changed too much")
        if after["clip_high"] - before["clip_high"] > 0.05:
            failures.append(f"{sample['scene']} at {sample['at_seconds']}s: clipping increased")
    failures.extend(f"{item['scene']}: reflection candidate did not improve"
                    for item in checks if not item["passed"])
    status = "rejected" if failures else "passed"
    return {"status": status, "failures": failures, "samples": samples,
            "issue_checks": checks}


def fix_manifest(manifest_path: Path, output: Path,
                 allow_pending: bool = False) -> dict:
    manifest = load_manifest(manifest_path)
    clip = manifest["clips"][0]
    source = Path(clip["source"])
    if output.resolve() == source.resolve():
        raise ReflectionError("output must differ from the source")
    masks = []
    for scene in clip.get("scenes", []):
        if approved(scene, allow_pending):
            masks.extend(scene.get("region_masks", []))
    if not masks:
        raise ReflectionError(
            "no approved FIX scenes; strong/content-rich reflections stay "
            "REVIEW or UNSUPPORTED. Use preview for a bounded comparison or "
            "benchmark a licensed backend")
    metadata = enhance.probe_video(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.stem + ".tmp" + output.suffix)
    temp.unlink(missing_ok=True)
    try:
        command = _mask_command(source, temp, masks,
                                float(metadata["duration_seconds"]))
        enhance.run(command)
        validation = validate(manifest, source, temp, allow_pending=allow_pending)
        if validation["status"] == "rejected":
            validation_path = manifest_path.parent / "validation.json"
            validation_path.write_text(json.dumps(validation, indent=2) + "\n",
                                       encoding="utf-8")
            temp.unlink(missing_ok=True)
            raise ReflectionError("quality validation rejected the correction")
        os.replace(temp, output)
    finally:
        temp.unlink(missing_ok=True)
    previews = []
    for scene in clip.get("scenes", []):
        if not approved(scene, allow_pending):
            continue
        start = float(scene["start_seconds"])
        length = max(0.5, min(3.0, float(scene["end_seconds"]) - start))
        target = (manifest_path.parent.parent / "previews" /
                  f"{scene['id']}-fix-compare.mp4")
        compare = _write_compare(source, output, start, length, target)
        if compare:
            previews.append(str(compare.resolve()))
    validation["previews"] = previews
    validation_path = manifest_path.parent / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2) + "\n",
                               encoding="utf-8")
    manifest["output"] = str(output.resolve())
    manifest["validation"] = validation
    manifest_path.write_text(enhance.yaml.safe_dump(manifest, sort_keys=False),
                             encoding="utf-8")
    return validation


def preview_manifest(manifest_path: Path, output: Path,
                     scene_id: str | None = None,
                     seconds: float = 3.0) -> dict:
    manifest = load_manifest(manifest_path)
    clip = manifest["clips"][0]
    source = Path(clip["source"])
    scenes = [scene for scene in clip.get("scenes", [])
              if (scene.get("issue") or {}).get("detected")]
    if scene_id:
        scenes = [scene for scene in scenes if scene.get("id") == scene_id]
    if not scenes:
        raise ReflectionError("manifest has no detected reflection scene")
    scene = scenes[0]
    masks = scene.get("region_masks") or []
    if not masks:
        mask = (scene.get("issue") or {}).get("parameters", {}).get("evidence_mask")
        if not mask:
            raise ReflectionError("scene has no evidence mask for a preview")
        masks = [{
            "start_seconds": scene["start_seconds"],
            "end_seconds": scene["end_seconds"],
            "filter": (scene.get("issue") or {}).get("parameters", {}).get(
                "preview_filter", PREVIEW_FILTER),
            "mask": mask,
        }]
    scene_start = float(scene["start_seconds"])
    scene_end = float(scene["end_seconds"])
    length = max(0.5, min(float(seconds), scene_end - scene_start))
    start = scene_start + max(0.0, (scene_end - scene_start - length) / 2)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.stem + ".tmp" + output.suffix)
    temp.unlink(missing_ok=True)
    try:
        command = _mask_command(source, temp, masks, length,
                                trim=(start, length),
                                filter_override=(scene.get("issue") or {}).get(
                                    "parameters", {}).get("preview_filter",
                                                          PREVIEW_FILTER))
        enhance.run(command)
        os.replace(temp, output)
    finally:
        temp.unlink(missing_ok=True)

    before = []
    after = []
    for position in (0.2, 0.5, 0.8):
        at = start + length * position
        before.append(_sample_metrics(source, at))
        after.append(_sample_metrics(output, at - start))
    before_mean = {key: float(np.mean([item[key] for item in before]))
                   for key in before[0]}
    after_mean = {key: float(np.mean([item[key] for item in after]))
                  for key in after[0]}
    validation = {
        "status": "review_required",
        "scene": scene["id"],
        "start_seconds": round(start, 3),
        "seconds": round(length, 3),
        "before": before_mean,
        "after": after_mean,
        "candidate_reduction": round(
            before_mean["candidate_fraction"] - after_mean["candidate_fraction"], 5),
        "reason": ("bounded comparison preview; a successful encode is not "
                   "proof that the reflection layer was separated"),
    }
    validation_path = manifest_path.parent / (
        f"preview-{scene['id']}-validation.json")
    validation_path.write_text(json.dumps(validation, indent=2) + "\n",
                               encoding="utf-8")
    compare = _write_compare(
        source, output, start, length,
        output.with_name(output.stem + "-compare.mp4"))
    validation["compare"] = str(compare.resolve()) if compare else None
    validation_path.write_text(json.dumps(validation, indent=2) + "\n",
                               encoding="utf-8")
    return validation


def run_benchmark(source: Path, config_path: Path, output_root: Path,
                  frames: int = 3, timeout: int = 300) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    name = str(config.get("name") or "external").strip()
    command = config.get("command")
    if not isinstance(command, list) or not command:
        raise ReflectionError("backend config needs a command array")
    template = " ".join(str(part) for part in command)
    if "{input}" not in template or "{output}" not in template:
        raise ReflectionError("backend command needs {input} and {output} placeholders")
    work = output_root / name
    work.mkdir(parents=True, exist_ok=True)
    report = detect_clip(source, output_root / "analysis")
    scenes = [scene for scene in report["clips"][0]["scenes"]
              if scene["issue"]["detected"]]
    if not scenes:
        raise ReflectionError("no reflection evidence in this clip")
    metadata = report["clips"][0]["metadata"]
    sample_width = min(1280, max(320, int(metadata.get("width") or 1280)))
    results = []
    for index, scene in enumerate(scenes[:max(1, frames)], 1):
        midpoint = (float(scene["start_seconds"]) + float(scene["end_seconds"])) / 2
        before_rgb = enhance.extract_frame(source, midpoint, width=sample_width)
        input_path = work / f"input-{index:03d}.png"
        output_path = work / f"output-{index:03d}.png"
        Image.fromarray((before_rgb * 255).astype(np.uint8)).save(input_path)
        argv = [str(part).replace("{input}", str(input_path.resolve()))
                .replace("{output}", str(output_path.resolve()))
                for part in command]
        started = time.perf_counter()
        try:
            proc = subprocess.run(argv, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace",
                                  timeout=timeout)
            runtime = time.perf_counter() - started
            if proc.returncode != 0:
                raise ReflectionError((proc.stderr or proc.stdout)[-1000:])
            if not output_path.is_file():
                raise ReflectionError("backend did not write the output image")
            after_rgb = np.asarray(Image.open(output_path).convert("RGB"),
                                   dtype=np.float32) / 255.0
            if after_rgb.shape != before_rgb.shape:
                raise ReflectionError("backend changed image dimensions")
            before = _frame_reflection_metrics(before_rgb)
            after = _frame_reflection_metrics(after_rgb)
            results.append({
                "scene": scene["id"],
                "runtime_seconds": round(runtime, 3),
                "before": before,
                "after": after,
                "candidate_reduction": round(
                    before["candidate_fraction"] - after["candidate_fraction"], 5),
                "glare_reduction": round(
                    before["glare_fraction"] - after["glare_fraction"], 5),
                "luma_delta": round(abs(after["luma_mean"] - before["luma_mean"]), 5),
                "sharpness_ratio": round(
                    after["sharpness"] / max(before["sharpness"], 1e-6), 3),
                "accepted": (
                    abs(after["luma_mean"] - before["luma_mean"]) <= 0.20
                    and after["sharpness"] >= before["sharpness"] * 0.5
                    and (before["candidate_fraction"] - after["candidate_fraction"] >= 0.002
                         or before["glare_fraction"] - after["glare_fraction"] >= 0.001)),
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
            sum(item["runtime_seconds"] for item in valid) / len(valid), 3)
        if valid else None,
        "mean_candidate_reduction": round(
            sum(item["candidate_reduction"] for item in valid) / len(valid), 5)
        if valid else None,
    }
    document = {"schema_version": SCHEMA_VERSION, "generated_at": enhance.now(),
                "source": str(source.resolve()),
                "config": str(config_path.resolve()),
                "summary": summary, "results": results}
    (work / "benchmarks.json").write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8")
    rows = "".join(
        "<tr>"
        f"<td>{item.get('scene')}</td>"
        f"<td>{item.get('runtime_seconds', '')}</td>"
        f"<td>{item.get('candidate_reduction', '')}</td>"
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
            "<table><thead><tr><th>Scene</th><th>Runtime (s)</th>"
            "<th>Candidate reduction</th><th>Glare reduction</th>"
            "<th>Luma delta</th><th>Sharpness ratio</th><th>Accepted</th>"
            f"<th>Error</th></tr></thead><tbody>{rows}</tbody></table>")
    (work / "benchmark.html").write_text(page, encoding="utf-8")
    return document


def _frame_reflection_metrics(rgb: np.ndarray) -> dict:
    parts = reflection_masks(rgb)
    metrics = enhance.frame_metrics(rgb)
    return {
        "candidate_fraction": round(fraction(parts["candidate"]), 5),
        "glare_fraction": round(fraction(parts["glare"]), 5),
        "veil_fraction": round(fraction(parts["veil"]), 5),
        "luma_mean": round(metrics["luma_mean"], 5),
        "saturation_mean": round(metrics["saturation_mean"], 5),
        "clip_high": round(metrics["clip_high"], 5),
        "sharpness": round(metrics["sharpness"], 5),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    detect = sub.add_parser("detect", help="find reflection candidates")
    detect.add_argument("--file", type=Path, help="one video")
    detect.add_argument("--folder", type=Path, help="every video in a folder")
    detect.add_argument("--out", type=Path, help="output root")
    detect.add_argument("--force", action="store_true")
    detect.add_argument("--json", action="store_true")
    fix = sub.add_parser("fix", help="render approved minor glare/veil fixes")
    fix.add_argument("--manifest", type=Path, required=True)
    fix.add_argument("--output", type=Path, required=True)
    fix.add_argument("--allow-pending", action="store_true")
    preview = sub.add_parser("preview",
                             help="render a short bounded comparison preview")
    preview.add_argument("--manifest", type=Path, required=True)
    preview.add_argument("--output", type=Path, required=True)
    preview.add_argument("--scene")
    preview.add_argument("--seconds", type=float, default=3.0)
    benchmark = sub.add_parser("benchmark",
                               help="benchmark an external licensed backend")
    benchmark.add_argument("--file", type=Path, required=True)
    benchmark.add_argument("--config", type=Path, required=True)
    benchmark.add_argument("--out", type=Path)
    benchmark.add_argument("--frames", type=int, default=3)
    benchmark.add_argument("--timeout", type=int, default=300)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.action == "detect":
            if args.file:
                root = args.out or (args.file.parent / ".content-studio" / "reflection")
                report = detect_clip(args.file, root, force=args.force)
            elif args.folder:
                report = detect_folder(args.folder, args.out, force=args.force)
            else:
                raise ReflectionError("detect needs --file or --folder")
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                for clip in report["clips"]:
                    print(f"{clip['name']}: {clip['summary']}")
            return 0
        if args.action == "fix":
            result = fix_manifest(args.manifest, args.output,
                                  allow_pending=args.allow_pending)
            print(json.dumps(result, indent=2))
            return 0
        if args.action == "preview":
            result = preview_manifest(args.manifest, args.output,
                                      scene_id=args.scene,
                                      seconds=args.seconds)
            print(json.dumps(result, indent=2))
            return 0
        if args.action == "benchmark":
            root = args.out or (args.file.parent / ".content-studio" / "reflection")
            document = run_benchmark(args.file, args.config, root,
                                     frames=args.frames, timeout=args.timeout)
            print(json.dumps(document["summary"], indent=2))
            return 0
        raise ReflectionError(f"unknown action: {args.action}")
    except (ReflectionError, enhance.EnhanceError) as exc:
        raise SystemExit(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
