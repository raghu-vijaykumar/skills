#!/usr/bin/env python3
"""Shortlist sustained camera roll and hand reviewed removals to the timeline.

Straight edges are only a scene-level proxy for camera angle. The scan never
approves a cut and cannot identify a quarter-turn of the whole camera.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "fastpan-cuts" / "scripts"))
import fastpan  # noqa: E402


CANDIDATE_SCHEMA = "content-studio.tilt-candidates.v1"
DECISION_SCHEMA = "content-studio.tilt-decisions.v1"


def estimate_roll(frame: np.ndarray) -> tuple[float, float]:
    """Return dominant line rotation in degrees and its fourfold coherence.

    Fourfold symmetry treats scene horizontals and verticals alike. It also
    folds 90-degree camera turns onto zero, which is why visual review remains
    mandatory even when the scan finds no candidate.
    """
    gray = frame.astype(np.float32)
    gy, gx = np.gradient(gray)
    magnitude = np.hypot(gx, gy)
    selected = magnitude > np.quantile(magnitude, 0.85)
    weights = magnitude[selected]
    if not len(weights) or weights.sum() <= 0:
        return 0.0, 0.0
    theta = np.arctan2(-gx[selected], gy[selected])
    vector = np.sum(weights * np.exp(4j * theta)) / weights.sum()
    return float(np.angle(vector, deg=True) / 4), float(abs(vector))


def sample_roll(source: Path, *, sample_fps: int, width: int, height: int) -> list[dict]:
    argv = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-noautorotate", "-i", str(source), "-an", "-vf",
            f"fps={sample_fps},scale={width}:{height}:flags=fast_bilinear,format=gray",
            "-pix_fmt", "gray", "-f", "rawvideo", "pipe:1"]
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    frame_bytes = width * height
    samples = []
    try:
        while True:
            raw = process.stdout.read(frame_bytes)
            if not raw:
                break
            if len(raw) != frame_bytes:
                raise ValueError("Truncated grayscale frame from FFmpeg")
            frame = np.frombuffer(raw, np.uint8).reshape(height, width)
            angle, coherence = estimate_roll(frame)
            samples.append({"time_s": round(len(samples) / sample_fps, 3),
                            "roll_deg": round(angle, 2),
                            "coherence": round(coherence, 3)})
    finally:
        process.stdout.close()
        error = process.stderr.read().decode("utf-8", errors="replace")
        process.stderr.close()
        status = process.wait()
    if status:
        raise ValueError(f"FFmpeg scan failed: {error[-500:]}")
    return samples


def group_candidates(samples: list[dict], *, threshold_deg: float,
                     sample_fps: int, fps: float, duration: float,
                     min_coherence: float = 0.18) -> list[dict]:
    # A line angle alone is not camera roll; only sustained evidence is queued.
    active = [row for row in samples if row["coherence"] >= min_coherence
              and abs(row["roll_deg"]) > threshold_deg]
    groups: list[list[dict]] = []
    for row in active:
        if groups and row["time_s"] - groups[-1][-1]["time_s"] <= 2:
            groups[-1].append(row)
        else:
            groups.append([row])
    candidates = []
    for group in groups:
        if len(group) < 3 * sample_fps:
            continue
        angles = [row["roll_deg"] for row in group]
        if abs(float(np.median(angles))) <= threshold_deg:
            continue
        start = max(0, math.floor((group[0]["time_s"] - 1) * fps))
        end = min(math.ceil(duration * fps),
                  math.ceil((group[-1]["time_s"] + 1 + 1 / sample_fps) * fps))
        candidates.append({"id": f"tilt-{len(candidates) + 1:04d}",
                           "start_frame": start, "end_frame": end,
                           "start_s": round(start / fps, 3),
                           "end_s": round(end / fps, 3),
                           "median_line_angle_deg": round(float(np.median(angles)), 1),
                           "peak_abs_line_angle_deg": round(max(abs(value) for value in angles), 1),
                           "median_coherence": round(float(np.median(
                               [row["coherence"] for row in group])), 3),
                           "sample_count": len(group),
                           "review_status": "pending_visual_review"})
    return candidates


def scan(source: Path, output: Path, *, threshold_deg: float = 10,
         sample_fps: int = 1, width: int = 320) -> dict:
    source = source.resolve(strict=True)
    output = output.resolve()
    if source == output or output.exists():
        raise ValueError("Scan report must be new and separate from source")
    if not 1 <= sample_fps <= 4 or not 160 <= width <= 640:
        raise ValueError("sample-fps must be 1-4 and width must be 160-640")
    if not 1 <= threshold_deg <= 44:
        raise ValueError("threshold-deg must be 1-44")
    info = fastpan.media_info(source)
    height = max(2, round(width * info["height"] / info["width"] / 2) * 2)
    samples = sample_roll(source, sample_fps=sample_fps, width=width,
                          height=height)
    candidates = group_candidates(samples, threshold_deg=threshold_deg,
                                  sample_fps=sample_fps, fps=info["fps"],
                                  duration=info["duration_s"])
    stat = source.stat()
    report = {"schema": CANDIDATE_SCHEMA, "source": str(source),
              "source_sha256": fastpan.sha256_file(source),
              "source_bytes": stat.st_size, "source_mtime_ns": stat.st_mtime_ns,
              "duration_s": info["duration_s"], "fps": info["fps"],
              "fps_text": info["fps_text"], "threshold_deg": threshold_deg,
              "sample_fps": sample_fps, "analysis_size": [width, height],
              "sample_count": len(samples), "samples": samples,
              "candidates": candidates,
              "note": "Angles are dominant scene-line estimates, not measured camera roll."
                      " Perspective and intentional diagonals may trigger false positives."
                      " A 90-degree camera turn folds to zero. Inspect all candidates and"
                      " sparse frames outside them before choosing exact cut frames."
                      " No cut is approved."}
    fastpan.write_new(output, report)
    return {"report": str(output), "sample_count": len(samples),
            "candidate_count": len(candidates), "source_sha256": report["source_sha256"]}


def preview(source: Path, decisions_file: Path, cut_id: str, output: Path,
            *, padding: float = 2.0) -> dict:
    """Encode only the two sides of a join, even for a long removed range."""
    source = source.resolve(strict=True)
    output = output.resolve()
    if source == output or output.exists():
        raise ValueError("Preview must be new and separate from source")
    decisions = fastpan.read_json(decisions_file)
    info, cuts = fastpan.validate_decisions(source, decisions,
                                           require_approval=False, exact_hash=False,
                                           decision_schema=DECISION_SCHEMA)
    cut = next((row for row in cuts if row["id"] == cut_id), None)
    if cut is None:
        raise ValueError(f"Unknown cut ID: {cut_id}")
    if not 0.5 <= padding <= 10:
        raise ValueError("Preview padding must be 0.5-10 seconds")
    start = cut["start_frame"] / info["fps"]
    end = cut["end_frame"] / info["fps"]
    if start < padding or info["duration_s"] - end < padding:
        raise ValueError("Preview needs full source context on both sides")
    picture = ("[0:v:0]setpts=PTS-STARTPTS,scale=1280:-2[a];"
               "[1:v:0]setpts=PTS-STARTPTS,scale=1280:-2[b];"
               "[a][b]concat=n=2:v=1:a=0[v]")
    audio = ""
    if info["has_audio"]:
        audio = (";[0:a:0]asetpts=PTS-STARTPTS[c];"
                 "[1:a:0]asetpts=PTS-STARTPTS[d];"
                 "[c][d]concat=n=2:v=0:a=1[outa]")
    argv = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-ss", f"{start - padding:.6f}", "-t", f"{padding:.6f}", "-i", str(source),
            "-ss", f"{end:.6f}", "-t", f"{padding:.6f}", "-i", str(source),
            "-filter_complex", picture + audio, "-map", "[v]"]
    if info["has_audio"]:
        argv += ["-map", "[outa]", "-c:a", "aac", "-b:a", "160k"]
    else:
        argv += ["-an"]
    argv += ["-r", f"{info['fps']:.6f}", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    if result.returncode:
        output.unlink(missing_ok=True)
        raise ValueError(f"FFmpeg preview failed: {result.stderr[-500:]}")
    return {"preview": str(output), "cut_id": cut_id,
            "removed_frames": cut["end_frame"] - cut["start_frame"],
            "expected_duration_s": round(2 * padding, 3),
            "audio_cut_with_picture": info["has_audio"]}


def timeline_changes(source: Path, decisions: Path, timeline: Path,
                     output: Path) -> dict:
    return fastpan.timeline_changes(source, decisions, timeline, output,
                                    decision_schema=DECISION_SCHEMA,
                                    clip_prefix="tilt")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    scan_cmd = actions.add_parser("scan")
    scan_cmd.add_argument("--input", type=Path, required=True)
    scan_cmd.add_argument("--output", type=Path, required=True)
    scan_cmd.add_argument("--threshold-deg", type=float, default=10)
    scan_cmd.add_argument("--sample-fps", type=int, default=1)
    scan_cmd.add_argument("--width", type=int, default=320)
    preview_cmd = actions.add_parser("preview")
    preview_cmd.add_argument("--input", type=Path, required=True)
    preview_cmd.add_argument("--decisions", type=Path, required=True)
    preview_cmd.add_argument("--cut-id", required=True)
    preview_cmd.add_argument("--output", type=Path, required=True)
    preview_cmd.add_argument("--padding", type=float, default=2)
    changes_cmd = actions.add_parser("timeline-changes")
    changes_cmd.add_argument("--input", type=Path, required=True)
    changes_cmd.add_argument("--decisions", type=Path, required=True)
    changes_cmd.add_argument("--timeline", type=Path, required=True)
    changes_cmd.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "scan":
            result = scan(args.input, args.output, threshold_deg=args.threshold_deg,
                          sample_fps=args.sample_fps, width=args.width)
        elif args.action == "preview":
            result = preview(args.input, args.decisions, args.cut_id,
                             args.output, padding=args.padding)
        else:
            result = timeline_changes(args.input, args.decisions,
                                      args.timeline, args.output)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"tilt {args.action} failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
