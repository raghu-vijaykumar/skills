#!/usr/bin/env python3
"""Per-clip iterative polish selection and timeline capture.

Upscaling is intentionally excluded. The loop evaluates short proxies for
polish presets, picks the best measured candidate, and writes the applied
filters and metrics into an editable timeline copy.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np

import enhance
import match
import polish

CANDIDATES = {
    "off": [],
    "light": [polish.DENOISE["light"], "deflicker=mode=pm:size=10",
              polish.SHARPEN["light"]],
    "medium": [polish.DENOISE["medium"], "deflicker=mode=pm:size=10",
               polish.SHARPEN["medium"]],
}


class RefineError(RuntimeError):
    pass


def run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise RefineError((result.stderr or result.stdout)[-3000:])


def metrics(path: Path, at: float, width: int = 480) -> dict:
    rgb = enhance.extract_frame(path, at, width=width)
    luma = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    saturation = np.divide(maximum - minimum, maximum,
                           out=np.zeros_like(maximum), where=maximum > 1e-5)
    gray = rgb.mean(axis=2)
    gx = gray[:, 1:] - gray[:, :-1]
    gy = gray[1:, :] - gray[:-1, :]
    grad = np.sqrt(gx[:-1, :] ** 2 + gy[:, :-1] ** 2)
    blurred = (gray + np.roll(gray, 1, 0) + np.roll(gray, -1, 0)
               + np.roll(gray, 1, 1) + np.roll(gray, -1, 1)) / 5.0
    highpass = (gray - blurred)[:-1, :-1]
    flat = grad < np.percentile(grad, 35)
    return {"luma_mean": float(luma.mean()), "luma_std": float(luma.std()),
            "saturation": float(saturation.mean()),
            "edge_sharpness": float(np.percentile(grad, 99)),
            "noise_flat": float(highpass[flat].std()),
            "clip_high": float((luma > 0.98).mean())}


def proxy(source: Path, output: Path, start: float, duration: float,
          filters: list[str]) -> None:
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(source),
           "-vf", ",".join(["scale=480:-2"] + filters) if filters else "scale=480:-2",
           "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", str(output)]
    run(cmd)


def score(before: dict, after: dict) -> float:
    return (after["edge_sharpness"] / max(before["edge_sharpness"], 1e-6)
            - 0.5 * after["noise_flat"] / max(before["noise_flat"], 1e-6)
            - 5.0 * max(0.0, after["clip_high"] - before["clip_high"])
            - 0.2 * abs(after["luma_mean"] - before["luma_mean"]))


def choose_candidate(source: Path, start: float, duration: float,
                     work: Path) -> dict:
    windows = [start + duration * 0.25, start + duration * 0.65]
    baseline = work / "baseline.mp4"
    proxy(source, baseline, start, duration, [])
    before = [metrics(baseline, min(duration - 0.05, w - start))
              for w in windows]
    results = []
    for name, filters in CANDIDATES.items():
        target = work / f"{name}.mp4"
        if filters:
            proxy(source, target, start, duration, filters)
        else:
            target = baseline
        after = [metrics(target, min(duration - 0.05, w - start))
                 for w in windows]
        values = [score(b, a) for b, a in zip(before, after)]
        results.append({"candidate": name, "filters": filters,
                        "score": round(float(np.mean(values)), 5),
                        "before": {key: float(np.median([item[key] for item in before]))
                                   for key in before[0]},
                        "after": {key: float(np.median([item[key] for item in after]))
                                  for key in after[0]}})
    best = max(results, key=lambda item: item["score"])
    off = next(item for item in results if item["candidate"] == "off")
    # A sharper proxy is not a reason to polish a clean source. Require a
    # diagnosed noise floor and a measurable reduction over doing nothing.
    noise_before = float(np.median([item["noise_flat"] for item in before]))
    noise_after = best["after"]["noise_flat"]
    issue = noise_before >= 0.01
    improved = (best["candidate"] != "off" and best["score"] - off["score"] >= 0.03
                and noise_after <= noise_before * 0.95)
    selected = best if issue and improved else off
    return {"selected": selected, "alternatives": results,
            "diagnosis": {"issue": "flat_area_noise" if issue else "none",
                          "baseline_noise": round(noise_before, 5),
                          "required_reduction": 0.05,
                          "measured_reduction": round(
                              1 - noise_after / max(noise_before, 1e-6), 5),
                          "decision": "FIX" if selected is best and improved else "SKIP"}}


def color_enhancements(source: Path, start: float, end: float,
                       analysis_root: Path, auto_fix: bool = False) -> list[dict]:
    report = enhance.analyze_clip(source, analysis_root)
    items = []
    for scene in report["clips"][0]["scenes"]:
        overlap_start = max(start, scene["start_seconds"])
        overlap_end = min(end, scene["end_seconds"])
        if overlap_end <= overlap_start:
            continue
        if scene["decision"] != "FIX" or not scene.get("corrections"):
            continue
        status = (scene.get("review") or {}).get("status")
        if not auto_fix and status not in {"approved", "auto_approved"}:
            continue
        items.append({"stage": "color",
                      "source_start": overlap_start,
                      "source_end": overlap_end,
                      "filters": list(scene["corrections"]),
                      "scene": scene["id"],
                      "review_status": "auto_approved" if auto_fix else status})
    return items


def refine(args) -> dict:
    timeline_path = Path(args.timeline).expanduser().resolve()
    output_path = Path(args.output_timeline).expanduser().resolve()
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    source_root = Path(timeline.get("source_root") or timeline_path.parent).resolve()
    analysis_root = Path(args.analysis_dir).expanduser().resolve() if args.analysis_dir \
        else source_root / ".content-studio" / "enhancement"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="refine-", dir=output_path.parent))
    report = {"schema_version": 1,
              "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
              "timeline": str(timeline_path), "clips": []}
    source_colors = {}
    target = None
    if args.match:
        for track in timeline.get("tracks", []):
            if track.get("kind") != "video":
                continue
            for clip in track.get("clips", []):
                source = (source_root / clip["source"]).resolve()
                if source not in source_colors:
                    info = enhance.probe_video(source)
                    source_colors[source] = match.mean_color(
                        source, info["duration_seconds"])
        target = {key: float(np.median([color[key] for color in source_colors.values()]))
                  for key in ("r", "g", "b")}
    try:
        for track in timeline.get("tracks", []):
            if track.get("kind") != "video":
                continue
            for clip in track.get("clips", []):
                source = (source_root / clip["source"]).resolve()
                start = float(clip["source_in"])
                end = float(clip["source_out"])
                selected = choose_candidate(source, start, end - start, work)
                items = []
                sharpen = []
                if selected["selected"]["filters"]:
                    sharpen = [value for value in selected["selected"]["filters"]
                               if value.startswith(("cas=", "unsharp="))]
                    polish_filters = [value for value in selected["selected"]["filters"]
                                      if value not in sharpen]
                    if polish_filters:
                        items.append({"stage": "polish",
                                      "source_start": start, "source_end": end,
                                      "candidate": selected["selected"]["candidate"],
                                      "filters": polish_filters,
                                      "metrics": {"before": selected["selected"]["before"],
                                                  "after": selected["selected"]["after"]}})
                gains = match.gains_for(source_colors[source], target) if target else None
                if gains and any(abs(gains[key] - 1.0) > 0.005 for key in gains):
                    items.append({"stage": "match",
                                  "source_start": start, "source_end": end,
                                  "gains": gains, "review_status": "review_required",
                                  "filters": ["colorchannelmixer="
                                              f"rr={gains['r']}:gg={gains['g']}:bb={gains['b']}"]})
                items.extend(color_enhancements(source, start, end, analysis_root,
                                                auto_fix=args.auto_fix))
                if sharpen:
                    items.append({"stage": "sharpen",
                                  "source_start": start, "source_end": end,
                                  "filters": sharpen})
                clip["enhancements"] = items
                report["clips"].append({"source": clip["source"],
                                        "source_in": start, "source_out": end,
                                        "selected": selected["selected"]["candidate"],
                                        "diagnosis": selected["diagnosis"],
                                        "delivery_verification": "required_after_timeline_render",
                                        "score": selected["selected"]["score"],
                                        "alternatives": selected["alternatives"],
                                        "enhancements": items})
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(timeline, indent=2) + "\n", encoding="utf-8")
    report_path = output_path.parent / "refine.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def verify_render(timeline_path: Path, render_path: Path,
                  report_path: Path | None = None) -> dict:
    """Check selected polish on the actual timeline render, then save evidence."""
    timeline_path = Path(timeline_path).expanduser().resolve()
    render_path = Path(render_path).expanduser().resolve()
    report_path = (Path(report_path).expanduser().resolve() if report_path
                   else timeline_path.parent / "refine.json")
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    root = Path(timeline.get("source_root") or timeline_path.parent).resolve()
    clips = [clip for track in timeline.get("tracks", [])
             if track.get("kind") == "video" for clip in track.get("clips", [])]
    if len(clips) != len(report["clips"]):
        raise RefineError("refine report does not match the rendered timeline")
    checks = []
    for clip, selected in zip(clips, report["clips"]):
        if selected["selected"] == "off" and not clip.get("enhancements"):
            continue
        duration = float(clip.get("duration") or
                         float(clip["source_out"]) - float(clip["source_in"]))
        samples = []
        for fraction in (0.2, 0.5, 0.8):
            source_at = float(clip["source_in"]) + duration * fraction
            render_at = float(clip.get("start", 0)) + duration * fraction
            samples.append({"source_at": round(source_at, 3),
                            "render_at": round(render_at, 3),
                            "before": metrics((root / clip["source"]).resolve(),
                                              source_at),
                            "after": metrics(render_path, render_at)})
        before = {key: float(np.median([item["before"][key] for item in samples]))
                  for key in samples[0]["before"]}
        after = {key: float(np.median([item["after"][key] for item in samples]))
                 for key in samples[0]["after"]}
        diagnosis = selected.get("diagnosis", {})
        noise_fixed = (diagnosis.get("issue") != "flat_area_noise" or
                       after["noise_flat"] <= before["noise_flat"] * 0.95)
        safe = all(item["after"]["clip_high"] - item["before"]["clip_high"] <= 0.02
                   for item in samples)
        subjective = any(item.get("stage") in {"match", "color"}
                         for item in clip.get("enhancements", []))
        checks.append({"source": clip["source"], "samples": samples, "before": before,
                       "after": after, "noise_fixed": noise_fixed,
                       "clipping_safe": safe, "subjective_review": subjective,
                       "passed": noise_fixed and safe and not subjective})
    result = {"status": ("skipped" if not checks else "passed"
                         if all(item["passed"] for item in checks)
                         else "review_required"),
              "render": str(render_path), "checks": checks}
    report["delivery_verification"] = result
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--output-timeline", type=Path)
    parser.add_argument("--verify-render", type=Path,
                        help="verify the rendered refined timeline against source clips")
    parser.add_argument("--report", type=Path,
                        help="refine.json for --verify-render (default: beside timeline)")
    parser.add_argument("--analysis-dir", type=Path)
    parser.add_argument("--auto-fix", action="store_true",
                        help="include conservative analyzer FIX color corrections without prior approval")
    parser.add_argument("--match", action="store_true",
                        help="propose cross-shot matching for review")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.verify_render:
            result = verify_render(args.timeline, args.verify_render, args.report)
            print(json.dumps(result, indent=2))
            return 0 if result["status"] in {"passed", "skipped"} else 2
        if not args.output_timeline:
            raise RefineError("--output-timeline is required when selecting candidates")
        print(json.dumps(refine(args), indent=2))
        return 0
    except (RefineError, OSError, ValueError) as exc:
        print(f"refine: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
