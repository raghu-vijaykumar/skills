"""Check the exact delivery and create bounded review evidence."""

from __future__ import annotations

import json
import subprocess
from fractions import Fraction
from pathlib import Path

from compiler import media_info
from model import AUDIO_METHODS, load, sha256_file, validate


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-1200:])


def _loudness(path: Path) -> dict:
    """Measure the delivered audio without writing another media master."""
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "info",
         "-i", str(path), "-vn",
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"Loudness measurement failed: {result.stderr[-1200:]}")
    marker = result.stderr.rfind('"input_i"')
    opening = result.stderr.rfind("{", 0, marker)
    closing = result.stderr.find("}", marker)
    if marker < 0 or opening < 0 or closing < 0:
        raise RuntimeError("Loudness measurement did not return input metrics")
    measured = json.loads(result.stderr[opening:closing + 1])
    integrated = float(measured["input_i"])
    true_peak = float(measured["input_tp"])
    return {
        "integrated_lufs": integrated,
        "true_peak_dbtp": true_peak,
        "status": "FIX" if abs(integrated + 16) <= 1
        and true_peak <= -1.5 else "REVIEW",
    }


def verify_output(record_path: Path, evidence_dir: Path | None = None) -> dict:
    record = load(record_path)
    output = Path(record["output"]).resolve()
    timeline_path = Path(record["timeline"]).resolve()
    if not timeline_path.is_file() or sha256_file(timeline_path) != record["timeline_sha256"]:
        raise ValueError("Rendered timeline revision is missing or changed")
    approval_path = Path(record["approval"]).resolve()
    if not approval_path.is_file() or sha256_file(approval_path) != record["approval_sha256"]:
        raise ValueError("Render approval record is missing or changed")
    approval = load(approval_path)
    if (approval.get("actor") != "human"
            or approval.get("fingerprint") != record["approval_fingerprint"]):
        raise ValueError("Render approval record is missing or changed")
    timeline = load(timeline_path)
    resolved = validate(timeline)
    if output != resolved["output"] or not output.is_file():
        raise ValueError("Delivered output is missing or differs from the timeline")
    if sha256_file(output) != record["output_sha256"]:
        raise ValueError("Delivered output bytes changed")
    info = media_info(output)
    video, audio = info["video"], info["audio"]
    if not video or not audio:
        raise ValueError("Delivered picture or audio stream is missing")
    fps_text = video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1"
    fps = float(Fraction(fps_text))
    if (int(video.get("width") or 0) != resolved["width"]
            or int(video.get("height") or 0) != resolved["height"]
            or abs(fps - resolved["fps"]) > .05
            or int(audio.get("sample_rate") or 0) != 48000
            or abs(info["duration"] - resolved["duration"]) > .15):
        raise ValueError(
            "Delivered media differs from timeline: "
            f"size={video.get('width')}x{video.get('height')} "
            f"fps={fps:.3f} audio_rate={audio.get('sample_rate')} "
            f"duration={info['duration']:.3f}; expected "
            f"{resolved['width']}x{resolved['height']} "
            f"fps={resolved['fps']:.3f} audio_rate=48000 "
            f"duration={resolved['duration']:.3f}")
    mastering = None
    if any(item["method"] == "loudnorm" for item in resolved["operations"]):
        mastering = _loudness(output)
    evidence: list[dict] = []
    if evidence_dir is not None:
        evidence_dir = evidence_dir.resolve()
        evidence_dir.mkdir(parents=True, exist_ok=True)
        # Boundary samples from the exact master expose timing spillover;
        # sampling is review evidence, not another master render.
        for index, item in enumerate(resolved["operations"]):
            start, end = float(item["start"]), float(item["end"])
            margin = (0.1 if item["method"] in AUDIO_METHODS
                      else 0.5 / resolved["fps"])
            positions = {
                "inside_start": min(end, start + margin),
                "inside_end": max(start, end - margin),
            }
            if start >= margin:
                positions["before"] = start - margin
            if end + margin < resolved["duration"]:
                positions["after"] = end + margin
            samples = []
            for label, at in positions.items():
                if not 0 <= at < resolved["duration"]:
                    continue
                if item["method"] in AUDIO_METHODS:
                    sample = evidence_dir / f"operation-{index:03d}-{label}.wav"
                    if not sample.exists():
                        _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                              "-ss", f"{at:.6f}", "-t", "0.1", "-i", str(output),
                              "-vn", "-c:a", "pcm_s16le", str(sample)])
                    samples.append({"position": label, "at": round(at, 3),
                                    "audio": str(sample)})
                else:
                    still = evidence_dir / f"operation-{index:03d}-{label}.png"
                    if not still.exists():
                        _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                              "-ss", f"{at:.6f}", "-i", str(output),
                              "-frames:v", "1", "-c:v", "png", str(still)])
                    samples.append({"position": label, "at": round(at, 3),
                                    "frame": str(still)})
            evidence.append({"id": item["id"], "range": [start, end],
                             "samples": samples})
        for index, cue in enumerate(resolved["audio"]):
            at = float(cue["start"])
            sample = evidence_dir / f"audio-{index:03d}.wav"
            if not sample.exists():
                _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                      "-ss", f"{at:.6f}", "-t", "1", "-i", str(output),
                      "-vn", "-c:a", "pcm_s16le", str(sample)])
            evidence.append({"id": cue["id"], "at": round(at, 3),
                             "audio": str(sample)})
        manifest = evidence_dir / "review-manifest.json"
        manifest.write_text(json.dumps({
            "timeline_sha256": record["timeline_sha256"],
            "output_sha256": record["output_sha256"],
            "evidence": evidence, "human_review_required": True,
        }, indent=2) + "\n", encoding="utf-8")
    return {
        "verified": True,
        "output": str(output),
        "duration": info["duration"],
        "resolution": [resolved["width"], resolved["height"]],
        "fps": fps,
        "audio_sample_rate": 48000,
        "mastering": mastering,
        "evidence": evidence,
        "human_review_required": True,
    }
