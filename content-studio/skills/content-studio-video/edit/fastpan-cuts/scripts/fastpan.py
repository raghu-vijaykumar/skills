#!/usr/bin/env python3
"""Find fast camera sweeps, preview reviewed removals, and export timeline cuts.

The scanner estimates whole-frame translation from small grayscale samples. Its
results are suggestions for an editor, never permission to remove footage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np


CANDIDATE_SCHEMA = "content-studio.fastpan-candidates.v1"
DECISION_SCHEMA = "content-studio.fastpan-decisions.v1"
MIN_KEEP_SECONDS = 0.5


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_new(path: Path, value: dict) -> None:
    # Review artifacts are immutable: a rerun must use a new name.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as target:
        json.dump(value, target, indent=2, ensure_ascii=False)
        target.write("\n")


def media_info(source: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,r_frame_rate,avg_frame_rate,"
         "color_transfer,side_data_list,nb_frames", "-of", "json", str(source)],
        capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(f"ffprobe failed: {result.stderr[-500:]}")
    data = json.loads(result.stdout)
    video = next((item for item in data.get("streams", [])
                  if item.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("Input has no video stream")
    fps_text = video.get("avg_frame_rate", "0/1")
    rate_text = video.get("r_frame_rate", "0/1")

    def fraction(value: str) -> float:
        numerator, denominator = (float(part) for part in value.split("/"))
        return numerator / denominator if denominator else 0.0

    fps = fraction(fps_text)
    if fps < 1 or abs(fps - fraction(rate_text)) > 0.01:
        raise ValueError("Fast-pan cuts v1 needs a constant-frame-rate source")
    transfer = video.get("color_transfer", "unknown")
    side_data = json.dumps(video.get("side_data_list", [])).upper()
    if transfer in {"arib-std-b67", "smpte2084"} or "DOVI" in side_data:
        raise ValueError("HDR/Dolby Vision needs a separately approved preservation or tone-map route")
    duration = float(data.get("format", {}).get("duration", 0))
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Input has no positive duration")
    return {"duration_s": duration, "fps": fps, "fps_text": fps_text,
            "width": int(video["width"]), "height": int(video["height"]),
            "has_audio": any(item.get("codec_type") == "audio"
                             for item in data.get("streams", [])),
            "frames": int(video["nb_frames"]) if video.get("nb_frames", "").isdigit() else None}


def phase_translation(previous: np.ndarray, current: np.ndarray,
                      window: np.ndarray) -> tuple[int, int, float]:
    # Phase correlation estimates translation common to most of the picture.
    fa = np.fft.rfft2((previous - previous.mean()) * window)
    fb = np.fft.rfft2((current - current.mean()) * window)
    cross = fa * np.conj(fb)
    cross /= np.maximum(np.abs(cross), 1e-9)
    surface = np.fft.irfft2(cross, s=previous.shape)
    y, x = np.unravel_index(int(np.argmax(surface)), surface.shape)
    height, width = previous.shape
    if x > width // 2:
        x -= width
    if y > height // 2:
        y -= height
    return int(x), int(y), float(surface[y % height, x % width])


def sample_motion(source: Path, *, sample_fps: int, width: int,
                  height: int) -> list[dict]:
    argv = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-noautorotate", "-i", str(source), "-an", "-vf",
            f"fps={sample_fps},scale={width}:{height}:flags=fast_bilinear,format=gray",
            "-pix_fmt", "gray", "-f", "rawvideo", "pipe:1"]
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    window = np.outer(np.hanning(height), np.hanning(width))
    frame_bytes = width * height
    previous = None
    samples: list[dict] = []
    frame_number = 0
    try:
        while True:
            raw = process.stdout.read(frame_bytes)
            if not raw:
                break
            if len(raw) != frame_bytes:
                raise ValueError("Truncated grayscale frame from FFmpeg")
            frame = np.frombuffer(raw, np.uint8).reshape(height, width).astype(np.float32)
            if previous is not None:
                dx, dy, peak = phase_translation(previous, frame, window)
                samples.append({"time_s": frame_number / sample_fps,
                                "dx": dx, "dy": dy, "peak": peak,
                                "mean_abs_diff": float(np.mean(np.abs(previous - frame)))})
            previous = frame
            frame_number += 1
    finally:
        process.stdout.close()
        error = process.stderr.read().decode("utf-8", errors="replace")
        process.stderr.close()
        status = process.wait()
    if status:
        raise ValueError(f"FFmpeg scan failed: {error[-500:]}")
    return samples


def candidate_windows(samples: list[dict], *, sample_fps: int,
                      width: int, motion_threshold: float) -> list[dict]:
    windows: list[dict] = []
    count = 2 * sample_fps
    for first in range(0, len(samples) - count + 1, sample_fps):
        rows = samples[first:first + count]
        good = [row for row in rows if row["peak"] >= 0.07
                and abs(row["dx"]) <= width * 0.35]
        if len(good) < sample_fps:
            continue
        gross = sum(abs(row["dx"]) for row in good)
        if gross == 0:
            continue
        signed = abs(sum(row["dx"] for row in good))
        coherence = signed / gross
        screen_per_second = signed / width / 2
        if coherence < 0.55 or screen_per_second < motion_threshold:
            continue
        windows.append({"start_s": max(0.0, rows[0]["time_s"] - 1 / sample_fps),
                        "end_s": rows[-1]["time_s"],
                        "screen_widths_per_second": screen_per_second,
                        "coherence": coherence,
                        "tracked_fraction": len(good) / len(rows),
                        "median_peak": float(np.median([row["peak"] for row in good]))})
    return windows


def merge_candidates(windows: list[dict], *, source_fps: float,
                     duration: float) -> list[dict]:
    spans: list[dict] = []
    for item in windows:
        if spans and item["start_s"] <= spans[-1]["end_s"] + 1:
            spans[-1]["end_s"] = max(spans[-1]["end_s"], item["end_s"])
            spans[-1]["windows"].append(item)
        else:
            spans.append({"start_s": item["start_s"], "end_s": item["end_s"],
                          "windows": [item]})
    candidates = []
    for index, span in enumerate(spans, 1):
        rows = span["windows"]
        start = max(0, int(math.floor(span["start_s"] * source_fps)))
        end = min(int(math.ceil(duration * source_fps)),
                  int(math.ceil(span["end_s"] * source_fps)))
        if end <= start:
            continue
        candidates.append({"id": f"pan-{index:04d}", "start_frame": start,
                           "end_frame": end, "start_s": round(start / source_fps, 3),
                           "end_s": round(end / source_fps, 3),
                           "peak_screen_widths_per_second": round(max(
                               row["screen_widths_per_second"] for row in rows), 3),
                           "median_coherence": round(float(np.median([
                               row["coherence"] for row in rows])), 3),
                           "median_peak": round(float(np.median([
                               row["median_peak"] for row in rows])), 3),
                           "tracked_fraction": round(float(np.median([
                               row["tracked_fraction"] for row in rows])), 3),
                           "review_status": "pending_review"})
    return candidates


def scan(source: Path, output: Path, *, sample_fps: int = 4,
         width: int = 320, motion_threshold: float = 0.12) -> dict:
    source = source.resolve(strict=True)
    if output.resolve() == source:
        raise ValueError("Report cannot overwrite source")
    if sample_fps < 2 or sample_fps > 8 or width < 160 or width > 640:
        raise ValueError("sample-fps must be 2-8 and width must be 160-640")
    if not 0.02 <= motion_threshold <= 1:
        raise ValueError("motion-threshold must be 0.02-1 screen widths/second")
    info = media_info(source)
    height = max(2, round(width * info["height"] / info["width"] / 2) * 2)
    samples = sample_motion(source, sample_fps=sample_fps, width=width, height=height)
    windows = candidate_windows(samples, sample_fps=sample_fps, width=width,
                                motion_threshold=motion_threshold)
    candidates = merge_candidates(windows, source_fps=info["fps"],
                                  duration=info["duration_s"])
    stat = source.stat()
    report = {"schema": CANDIDATE_SCHEMA, "source": str(source),
              "source_sha256": sha256_file(source), "source_bytes": stat.st_size,
              "source_mtime_ns": stat.st_mtime_ns, "duration_s": info["duration_s"],
              "fps": info["fps"], "fps_text": info["fps_text"],
              "sample_fps": sample_fps, "analysis_size": [width, height],
              "motion_threshold_screen_widths_per_second": motion_threshold,
              "sample_count": len(samples) + 1, "candidates": candidates,
              "note": "Global screen motion suggests review ranges; it does not distinguish all intentional tracking, moving foregrounds, cuts, or blur. No cut is approved."}
    write_new(output, report)
    return {"report": str(output), "sample_count": report["sample_count"],
            "candidate_count": len(candidates), "source_sha256": report["source_sha256"]}


def validate_decisions(source: Path, decisions: dict, *, require_approval: bool,
                       exact_hash: bool, decision_schema: str = DECISION_SCHEMA) -> tuple[dict, list[dict]]:
    source = source.resolve(strict=True)
    info = media_info(source)
    stat = source.stat()
    if decisions.get("schema") != decision_schema or Path(decisions.get("source", "")).resolve() != source:
        raise ValueError("Cut decision schema or source does not match")
    if decisions.get("source_bytes") != stat.st_size or decisions.get("source_mtime_ns") != stat.st_mtime_ns:
        raise ValueError("Source size or modification time changed since review")
    if abs(float(decisions.get("fps", 0)) - info["fps"]) > 1e-4:
        raise ValueError("Source frame rate changed since review")
    if exact_hash and decisions.get("source_sha256") != sha256_file(source):
        raise ValueError("Source SHA-256 changed since review")
    cuts = decisions.get("cuts")
    if not isinstance(cuts, list) or not cuts:
        raise ValueError("At least one cut is required")
    approved = []
    seen_ids = set()
    previous_end = 0
    max_frame = info["frames"] or int(math.floor(info["duration_s"] * info["fps"]))
    for cut in sorted(cuts, key=lambda row: row.get("start_frame", -1)):
        if (not isinstance(cut, dict) or not isinstance(cut.get("id"), str)
                or not cut["id"] or type(cut.get("start_frame")) is not int
                or type(cut.get("end_frame")) is not int):
            raise ValueError("Cuts need an ID and integer source-frame bounds")
        start, end = cut["start_frame"], cut["end_frame"]
        if cut["id"] in seen_ids:
            raise ValueError(f"Duplicate cut ID: {cut['id']}")
        seen_ids.add(cut["id"])
        if start < previous_end + math.ceil(MIN_KEEP_SECONDS * info["fps"]) or end <= start or end > max_frame:
            raise ValueError(f"Overlapping, too-close, or out-of-bounds cut: {cut['id']}")
        if require_approval and cut.get("review_status") != "approved":
            raise ValueError(f"Cut lacks human review: {cut['id']}")
        approved.append(cut)
        previous_end = end
    if max_frame - previous_end < math.ceil(MIN_KEEP_SECONDS * info["fps"]):
        raise ValueError("The final retained source range is too short")
    if require_approval and (decisions.get("actor") != "human"
                             or not str(decisions.get("reviewer", "")).strip()
                             or not str(decisions.get("review_note", "")).strip()):
        raise ValueError("Human reviewer and review note are required")
    return info, approved


def preview(source: Path, decisions_file: Path, cut_id: str, output: Path,
            *, padding: float = 2.0, max_seconds: float = 30.0) -> dict:
    source = source.resolve(strict=True)
    output = output.resolve()
    if source == output or output.exists():
        raise ValueError("Preview output must be new and separate from source")
    decisions = read_json(decisions_file)
    info, cuts = validate_decisions(source, decisions, require_approval=False,
                                    exact_hash=False)
    cut = next((row for row in cuts if row["id"] == cut_id), None)
    if cut is None:
        raise ValueError(f"Unknown cut ID: {cut_id}")
    if padding < MIN_KEEP_SECONDS or padding > 10:
        raise ValueError("Preview padding must be 0.5-10 seconds")
    cut_start = cut["start_frame"] / info["fps"]
    cut_end = cut["end_frame"] / info["fps"]
    start = max(0, cut_start - padding)
    end = min(info["duration_s"], cut_end + padding)
    if end - start > max_seconds:
        raise ValueError("Preview exceeds the bounded duration budget")
    left, right, length = cut_start - start, cut_end - start, end - start
    if left < MIN_KEEP_SECONDS or end - cut_end < MIN_KEEP_SECONDS:
        raise ValueError("Preview needs source context on both sides of the cut")
    picture = (f"[0:v:0]split=2[v0][v1];"
               f"[v0]trim=start=0:end={left:.6f},setpts=PTS-STARTPTS[a];"
               f"[v1]trim=start={right:.6f}:end={length:.6f},setpts=PTS-STARTPTS[b];"
               f"[a][b]concat=n=2:v=1:a=0,scale=1280:-2[v]")
    audio = ""
    if info["has_audio"]:
        audio = (f";[0:a:0]asplit=2[a0][a1];"
                 f"[a0]atrim=start=0:end={left:.6f},asetpts=PTS-STARTPTS[c];"
                 f"[a1]atrim=start={right:.6f}:end={length:.6f},asetpts=PTS-STARTPTS[d];"
                 f"[c][d]concat=n=2:v=0:a=1[outa]")
    argv = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-ss", f"{start:.6f}",
            "-t", f"{length:.6f}", "-i", str(source), "-filter_complex", picture + audio,
            "-map", "[v]"]
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
            "expected_duration_s": round(length - (cut_end - cut_start), 3),
            "audio_cut_with_picture": info["has_audio"]}


def timeline_changes(source: Path, decisions_file: Path,
                     timeline_file: Path, output: Path, *,
                     decision_schema: str = DECISION_SCHEMA,
                     clip_prefix: str = "fastpan") -> dict:
    source = source.resolve(strict=True)
    decisions = read_json(decisions_file)
    info, cuts = validate_decisions(source, decisions, require_approval=True,
                                    exact_hash=True, decision_schema=decision_schema)
    timeline = read_json(timeline_file)
    picture = timeline.get("picture", [])
    if (len(picture) != 1 or timeline.get("operations")
            or timeline.get("transitions") or timeline.get("audio")):
        raise ValueError("Cut handoff needs one source and no timed cues or transitions")
    original = picture[0]
    root = Path(timeline.get("source_root", "")).resolve()
    if (root / original.get("source", "")).resolve() != source or original.get("sha256") != decisions["source_sha256"]:
        raise ValueError("Timeline source does not match the reviewed source")
    # timeline.py init leaves source_out unset; this is still a full-source draft.
    source_out = original.get("source_out", info["duration_s"])
    if abs(float(original.get("source_in", -1))) > 1e-6 or abs(float(source_out) - info["duration_s"]) > 0.1:
        raise ValueError("Timeline must contain the full uncut source")
    if output.exists() or output.resolve() == source:
        raise ValueError("Timeline changes output must be new and separate")
    kept = []
    cursor = 0
    for cut in cuts:
        kept.append((cursor / info["fps"], cut["start_frame"] / info["fps"]))
        cursor = cut["end_frame"]
    kept.append((cursor / info["fps"], float(source_out)))
    clips = [{"id": f"{clip_prefix}-keep-{index:04d}", "source": original["source"],
              "sha256": original["sha256"], "source_in": round(start, 6),
              "source_out": round(end, 6), "audio_gain": float(original.get("audio_gain", 1))}
             for index, (start, end) in enumerate(kept, 1)]
    changes = {"picture": clips, "audio_policy": "mix"}
    write_new(output, changes)
    return {"changes": str(output), "removed_cuts": len(cuts),
            "kept_clips": len(clips),
            "expected_duration_s": round(sum(end - start for start, end in kept), 3),
            "note": "Use timeline.py revise, validate, preview, fingerprint, human approval, render, and verify; this command did not render."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    scan_cmd = actions.add_parser("scan")
    scan_cmd.add_argument("--input", type=Path, required=True)
    scan_cmd.add_argument("--output", type=Path, required=True)
    scan_cmd.add_argument("--sample-fps", type=int, default=4)
    scan_cmd.add_argument("--width", type=int, default=320)
    scan_cmd.add_argument("--motion-threshold", type=float, default=0.12)
    preview_cmd = actions.add_parser("preview")
    preview_cmd.add_argument("--input", type=Path, required=True)
    preview_cmd.add_argument("--decisions", type=Path, required=True)
    preview_cmd.add_argument("--cut-id", required=True)
    preview_cmd.add_argument("--output", type=Path, required=True)
    preview_cmd.add_argument("--padding", type=float, default=2.0)
    changes_cmd = actions.add_parser("timeline-changes")
    changes_cmd.add_argument("--input", type=Path, required=True)
    changes_cmd.add_argument("--decisions", type=Path, required=True)
    changes_cmd.add_argument("--timeline", type=Path, required=True)
    changes_cmd.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "scan":
            result = scan(args.input, args.output, sample_fps=args.sample_fps,
                          width=args.width, motion_threshold=args.motion_threshold)
        elif args.action == "preview":
            result = preview(args.input, args.decisions, args.cut_id,
                             args.output, padding=args.padding)
        else:
            result = timeline_changes(args.input, args.decisions,
                                      args.timeline, args.output)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"fastpan {args.action} failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
