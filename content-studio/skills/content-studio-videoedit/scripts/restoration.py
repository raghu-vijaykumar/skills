#!/usr/bin/env python3
"""Diagnosis-first restoration decisions for video upscaling.

The analyzer never assumes that a super-resolution model improves a clip. It
measures the source, renders a short Lanczos and AI candidate, and only returns
FIX when edge detail improves without added noise, clipping, exposure drift, or
frame-to-frame flicker. Artifacts land next to the clip for human review.
"""

from __future__ import annotations

import html
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

import enhance
import refine
import upscale

ANALYSIS_VERSION = "1"
SCHEMA_VERSION = 1
DECISIONS = ("SKIP", "FIX", "REVIEW", "UNSUPPORTED")
SAMPLE_FRACTIONS = (0.15, 0.35, 0.55, 0.75, 0.90)
SAMPLE_WIDTH = 960
MIN_RESOLUTION_GAIN = 1.15
MIN_DETAIL_GAIN = 0.03
NOISE_SOFT = 1.20
NOISE_HARD = 1.50
TEMPORAL_SOFT = 1.35
TEMPORAL_HARD = 2.00
JITTER_SOFT = 0.30
JITTER_HARD = 0.45
LUMA_HARD = 0.12
CLIP_HARD = 0.01


def sample_times(duration: float, count: int = 5) -> list[float]:
    if duration <= 0.5:
        return [max(0.0, duration / 2)]
    fractions = SAMPLE_FRACTIONS[:max(2, min(count, len(SAMPLE_FRACTIONS)))]
    return [round(duration * fraction, 3) for fraction in fractions]


def preview_window(duration: float, seconds: float) -> tuple[float, float]:
    length = min(max(3.0, seconds), 15.0, max(duration, 3.0))
    if duration <= length:
        return 0.0, max(0.0, duration)
    start = min(max(0.0, duration * 0.4 - length / 2), duration - length)
    return round(start, 3), round(length, 3)


def sample_metrics(path: Path, times: list[float],
                   width: int = SAMPLE_WIDTH) -> dict:
    values = []
    for at in times:
        try:
            values.append(refine.metrics(path, at, width=width))
        except Exception as exc:  # noqa: BLE001 - analyzer errors are decisions
            raise upscale.UpscaleError(f"cannot measure {path.name} at {at:.2f}s: {exc}") from exc
    keys = values[0].keys()
    summary = {key: round(float(np.median([item[key] for item in values])), 5)
               for key in keys}
    return {"samples": values, "summary": summary}


def analyze_clip(source: Path, target: tuple[int, int] | None,
                 backend: str | None = None,
                 executable: str | Path | None = None) -> dict:
    """Cheap diagnosis. A candidate is never FIX without a preview."""
    source = Path(source).expanduser().resolve()
    info = upscale.probe(source)
    target = target or (info["width"] * 2, info["height"] * 2)
    width, height = info["width"], info["height"]
    target_width, target_height = target
    result = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "clip": source.name,
        "source": str(source),
        "source_size": [width, height],
        "target": list(target),
        "source_hash": upscale.source_hash(source),
        "duration_seconds": round(info["duration"], 3),
        "pix_fmt": info["pix_fmt"],
        "color_transfer": info["color_transfer"],
        "dolby_vision": info["dolby_vision"],
        "decision": "REVIEW",
        "reasons": [],
        "needs_preview": True,
    }
    if width >= target_width and height >= target_height:
        return {**result, "decision": "SKIP", "reasons": ["already_at_target"],
                "needs_preview": False}
    if (width > height) != (target_width > target_height):
        return {**result, "decision": "UNSUPPORTED",
                "reasons": ["orientation_mismatch"], "needs_preview": False}
    if upscale.is_hdr(info):
        return {**result, "decision": "UNSUPPORTED",
                "reasons": ["hdr_step_not_approved"], "needs_preview": False}
    gain = min(target_width / width, target_height / height)
    result["resolution_gain"] = round(gain, 3)
    if gain < MIN_RESOLUTION_GAIN:
        return {**result, "decision": "SKIP",
                "reasons": ["no_meaningful_resolution_gain"], "needs_preview": False}
    times = sample_times(info["duration"])
    metrics = sample_metrics(source, times)
    summary = metrics["summary"]
    result["source_metrics"] = summary
    result["samples"] = metrics["samples"]
    if summary["luma_mean"] < 0.05 and summary["edge_sharpness"] < 0.01:
        return {**result, "decision": "SKIP", "reasons": ["low_information_frame"],
                "needs_preview": False}
    reasons = ["candidate_needs_preview"]
    if summary["noise_flat"] > 0.06:
        reasons.append("noisy_source")
    if summary["edge_sharpness"] < 0.02:
        reasons.append("soft_source")
    return {**result, "reasons": reasons}


def _frames(path: Path, start: float, count: int, folder: Path,
            width: int = 480) -> list[np.ndarray]:
    folder.mkdir(parents=True, exist_ok=True)
    upscale.run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                 "-ss", f"{max(0.0, start):.3f}", "-i", str(path),
                 "-frames:v", str(max(2, count)),
                 "-vf", f"scale={width}:-2", str(folder / "%03d.png")])
    frames = []
    for item in sorted(folder.glob("*.png")):
        frames.append(np.asarray(Image.open(item).convert("L"), dtype=np.float32) / 255.0)
    return frames


def _sharpness(frame: np.ndarray) -> float:
    gx = frame[:, 1:] - frame[:, :-1]
    gy = frame[1:, :] - frame[:-1, :]
    gradient = np.sqrt(gx[:-1, :] ** 2 + gy[:, :-1] ** 2)
    return float(np.percentile(gradient, 99))


def temporal_profile(lanczos: Path, candidate: Path, at: float,
                     scratch: Path, frames: int = 8) -> dict:
    """Compare motion-normalized change between the resized and AI candidates.

    Lanczos carries the same camera motion as the AI pass, so the ratio of
    adjacent-frame change isolates detail that flickers instead of moving.
    """
    left = _frames(lanczos, at, frames, scratch / "temporal-lanczos")
    right = _frames(candidate, at, frames, scratch / "temporal-ai")
    count = min(len(left), len(right))
    if count < 3:
        return {"frames": count, "motion_ratio": 1.0, "sharpness_jitter": 0.0}
    base = float(np.mean([np.abs(left[i] - left[i - 1]).mean()
                          for i in range(1, count)]))
    changed = float(np.mean([np.abs(right[i] - right[i - 1]).mean()
                             for i in range(1, count)]))
    sharpness = [_sharpness(frame) for frame in right]
    mean = float(np.mean(sharpness)) or 1e-6
    return {
        "frames": count,
        "motion_ratio": round(changed / max(base, 1e-5), 3),
        "sharpness_jitter": round(float(np.std(sharpness) / mean), 3),
    }


def decide(preview: dict) -> dict:
    """Turn measured differences into SKIP/FIX/REVIEW/UNSUPPORTED."""
    lanczos = preview["lanczos"]["summary"]
    ai = preview["ai"]["summary"]
    temporal = preview["temporal"]
    sharp_gain = ai["edge_sharpness"] / max(lanczos["edge_sharpness"], 1e-6) - 1.0
    noise_ratio = ai["noise_flat"] / max(lanczos["noise_flat"], 1e-6)
    luma_delta = abs(ai["luma_mean"] - lanczos["luma_mean"])
    clip_delta = ai["clip_high"] - lanczos["clip_high"]
    preview["comparison"] = {
        "sharpness_gain": round(sharp_gain, 4),
        "noise_ratio": round(noise_ratio, 4),
        "luma_delta": round(luma_delta, 4),
        "clip_high_delta": round(clip_delta, 4),
    }
    hard: list[str] = []
    soft: list[str] = []
    if clip_delta > CLIP_HARD:
        hard.append("clipping")
    if luma_delta > LUMA_HARD:
        hard.append("exposure_shift")
    if noise_ratio > NOISE_HARD:
        hard.append("noise_increase")
    elif noise_ratio > NOISE_SOFT:
        soft.append("noise_increase")
    if temporal["motion_ratio"] > TEMPORAL_HARD:
        hard.append("temporal_flicker")
    elif temporal["motion_ratio"] > TEMPORAL_SOFT:
        soft.append("temporal_flicker")
    if temporal["sharpness_jitter"] > JITTER_HARD:
        hard.append("texture_flicker")
    elif temporal["sharpness_jitter"] > JITTER_SOFT:
        soft.append("texture_flicker")
    if sharp_gain < MIN_DETAIL_GAIN:
        decision = "SKIP"
        reasons = ["no_measurable_detail_gain"] + hard + soft
    elif hard:
        decision, reasons = "UNSUPPORTED", hard + soft
    elif soft:
        decision, reasons = "REVIEW", soft
    else:
        decision, reasons = "FIX", ["detail_gain_without_artifacts"]
    return {"decision": decision, "reasons": reasons,
            "metrics": {"sharpness_gain": round(sharp_gain, 4),
                        "noise_ratio": round(noise_ratio, 4),
                        "motion_ratio": temporal["motion_ratio"],
                        "sharpness_jitter": temporal["sharpness_jitter"]}}


def three_panel(source: Path, lanczos: Path, candidate: Path, source_at: float,
                local_at: float, target: Path, width: int = 640) -> None:
    def grab(path: Path, offset: float) -> Image.Image:
        result = subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{max(0.0, offset):.3f}",
             "-i", str(path), "-frames:v", "1", "-vf", f"scale={width}:-2",
             "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if result.returncode or not result.stdout:
            raise upscale.UpscaleError(f"cannot sample {path}")
        import io
        return Image.open(io.BytesIO(result.stdout)).convert("RGB")

    panels = [grab(source, source_at), grab(lanczos, local_at),
              grab(candidate, local_at)]
    height = min(panel.height for panel in panels)
    canvas = Image.new("RGB", (width * 3, height), "white")
    for index, panel in enumerate(panels):
        canvas.paste(panel.resize((width, height)), (index * width, 0))
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, quality=92)


def _write_preview_html(report: dict, path: Path) -> None:
    rows = "".join(
        f"<tr><td>{html.escape(name)}</td><td class='num'>{value}</td></tr>"
        for name, value in report["comparison"].items())
    reasons = ", ".join(report["decision"]["reasons"]) or "none"
    path.write_text(f"""<!doctype html><meta charset='utf-8'>
<title>Restoration preview - {html.escape(report['clip'])}</title>
<style>body{{font-family:system-ui;margin:2rem}}table{{border-collapse:collapse}}
td,th{{border:1px solid #ccc;padding:.3rem .5rem}}td.num{{text-align:right}}</style>
<h1>{html.escape(report['clip'])}</h1>
<p><strong>{report['decision']['decision']}</strong> - {html.escape(reasons)}</p>
<p><img src='three-panel.jpg' style='max-width:100%'></p>
<p><video controls src='preview-lanczos.mp4' width='48%'></video>
<video controls src='preview-ai.mp4' width='48%'></video></p>
<table><tr><th>metric</th><th>AI vs Lanczos</th></tr>{rows}</table>
<p>Left to right: source, Lanczos, AI candidate.</p>
""", encoding="utf-8")


def preview_clip(source: Path, target: tuple[int, int] | None,
                 preview_seconds: float = 8.0, backend: str | None = None,
                 executable: str | Path | None = None, model: str | None = None,
                 tile: int = 256, denoise_strength: float | None = None,
                 weights: str | None = None, work: Path | None = None) -> dict:
    source = Path(source).expanduser().resolve()
    info = upscale.probe(source)
    if upscale.is_hdr(info):
        raise upscale.UpscaleError("HDR/Dolby Vision source: previews refuse to "
                                   "guess a tone-map; process the SDR final instead")
    target = target or (info["width"] * 2, info["height"] * 2)
    work = (Path(work) if work else source.parent / "upscale-work") / "preview"
    work.mkdir(parents=True, exist_ok=True)
    start, seconds = preview_window(info["duration"], preview_seconds)
    scale = min(4, max(2, int(math.ceil(max(target[0] / info["width"],
                                             target[1] / info["height"])))))
    resolved, executable_path = upscale.preferred_backend(backend, executable)
    if resolved == "lanczos":
        raise upscale.UpscaleError("no AI backend is available for a preview")
    model_name = upscale.resolve_model(resolved, model,
                                       executable_path if resolved == "realesrgan" else None)
    lanczos_video = work / "preview-lanczos.mp4"
    ai_video = work / "preview-ai.mp4"
    upscale.run_lanczos(source, lanczos_video, target, start, seconds, False,
                        info["fps"], info, preset="fast")
    timing = upscale.render_ai(source, ai_video, work / "ai", resolved,
                               executable_path, model_name, scale, tile,
                               start, seconds, info, chunk=0,
                               denoise_strength=denoise_strength, weights=weights,
                               preset="fast")
    times = [round(seconds * fraction, 3) for fraction in (0.2, 0.5, 0.8)]
    lanczos_metrics = sample_metrics(lanczos_video, times)
    ai_metrics = sample_metrics(ai_video, times)
    with tempfile.TemporaryDirectory(prefix="restoration-", dir=work) as scratch:
        temporal = temporal_profile(lanczos_video, ai_video,
                                    round(seconds * 0.3, 3), Path(scratch))
    preview = {
        "lanczos": lanczos_metrics,
        "ai": ai_metrics,
        "temporal": temporal,
    }
    decision = decide(preview)
    three_panel(source, lanczos_video, ai_video, round(start + seconds * 0.5, 3),
                round(seconds * 0.5, 3), work / "three-panel.jpg")
    report = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "generated_at": upscale.now(),
        "clip": source.name,
        "source": str(source),
        "source_size": [info["width"], info["height"]],
        "target": list(target),
        "window": {"start": start, "duration": seconds},
        "backend": resolved,
        "model": model_name,
        "scale": scale,
        "tile": tile,
        "timing": timing,
        "lanczos": lanczos_metrics,
        "ai": ai_metrics,
        "temporal": temporal,
        "comparison": preview["comparison"],
        "decision": decision,
        "artifacts": {"preview_lanczos": str(lanczos_video),
                      "preview_ai": str(ai_video),
                      "three_panel": str(work / "three-panel.jpg")},
    }
    report_path = work / "preview.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _write_preview_html(report, work / "preview.html")
    report["report_path"] = str(report_path)
    report["html_path"] = str(work / "preview.html")
    return report


def timeline_sources(timeline_path: Path, files: list[Path]) -> list[Path]:
    """Keep only processed clips referenced by an editable timeline."""
    timeline_path = Path(timeline_path).expanduser().resolve()
    if not timeline_path.is_file():
        raise upscale.UpscaleError(f"timeline not found: {timeline_path}")
    data = json.loads(timeline_path.read_text(encoding="utf-8"))
    names = set()
    for track in data.get("tracks", []):
        if track.get("kind") != "video":
            continue
        for clip in track.get("clips", []):
            value = clip.get("source")
            if value:
                names.add(Path(value).stem.casefold())
                names.add(Path(value).name.casefold())
    picked = [path for path in files
              if path.parent.name.casefold() in names
              or path.parent.name.rsplit(".", 1)[0].casefold() in names]
    if not picked:
        raise upscale.UpscaleError("timeline does not reference any processed clips")
    return picked


def write_batch_report(summary: dict, path: Path) -> None:
    rows = []
    for item in summary.get("clips", []):
        reasons = ", ".join(item.get("reasons", []) or [])
        preview = item.get("preview") or ""
        link = ""
        if preview:
            target = Path(preview)
            if target.is_file():
                relative = os.path.relpath(target, path.parent).replace(os.sep, "/")
                link = f"<a href='{relative}'>preview</a>"
        rows.append(
            f"<tr><td>{html.escape(Path(item.get('source', '')).name)}</td>"
            f"<td>{html.escape(item.get('status', ''))}</td>"
            f"<td>{html.escape(str(item.get('decision', '')))}</td>"
            f"<td>{html.escape(reasons)}</td><td>{link}</td></tr>")
    path.write_text(f"""<!doctype html><meta charset='utf-8'>
<title>Restoration decisions</title>
<style>body{{font-family:system-ui;margin:2rem}}table{{border-collapse:collapse}}
td,th{{border:1px solid #ccc;padding:.3rem .5rem}}</style>
<h1>Restoration decisions</h1>
<p>{summary.get('upscaled', 0)} upscaled, {summary.get('review_pending', 0)} awaiting
review, {summary.get('unsupported', 0)} unsupported.</p>
<table><tr><th>clip</th><th>status</th><th>decision</th><th>reasons</th>
<th>review</th></tr>{''.join(rows)}</table>
""", encoding="utf-8")
