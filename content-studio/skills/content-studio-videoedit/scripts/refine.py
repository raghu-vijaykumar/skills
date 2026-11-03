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


def metrics(path: Path, at: float) -> dict:
    rgb = enhance.extract_frame(path, at, width=480)
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
                        "before": before[0], "after": after[0]})
    best = max(results, key=lambda item: item["score"])
    return {"selected": best, "alternatives": results}


def color_enhancements(source: Path, start: float, end: float,
                       analysis_root: Path) -> list[dict]:
    report = enhance.analyze_clip(source, analysis_root)
    items = []
    for scene in report["clips"][0]["scenes"]:
        overlap_start = max(start, scene["start_seconds"])
        overlap_end = min(end, scene["end_seconds"])
        if overlap_end <= overlap_start:
            continue
        if scene["decision"] != "FIX" or not scene.get("corrections"):
            continue
        items.append({"stage": "color",
                      "source_start": overlap_start,
                      "source_end": overlap_end,
                      "filters": list(scene["corrections"]),
                      "scene": scene["id"]})
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
                if selected["selected"]["filters"]:
                    items.append({"stage": "polish",
                                  "source_start": start, "source_end": end,
                                  "candidate": selected["selected"]["candidate"],
                                  "filters": selected["selected"]["filters"],
                                  "metrics": {"before": selected["selected"]["before"],
                                              "after": selected["selected"]["after"]}})
                items.extend(color_enhancements(source, start, end, analysis_root))
                clip["enhancements"] = items
                report["clips"].append({"source": clip["source"],
                                        "source_in": start, "source_out": end,
                                        "selected": selected["selected"]["candidate"],
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--output-timeline", type=Path, required=True)
    parser.add_argument("--analysis-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(json.dumps(refine(args), indent=2))
        return 0
    except (RefineError, OSError, ValueError) as exc:
        print(f"refine: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
