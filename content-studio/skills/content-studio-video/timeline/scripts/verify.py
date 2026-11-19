"""Check the exact delivery and create bounded review evidence."""

from __future__ import annotations

import json
import importlib.util
import subprocess
from fractions import Fraction
from pathlib import Path

from compiler import media_info, verify_picture_copy
from model import AUDIO_METHODS, load, sha256_file, validate


def _inspect_master(output: Path, digest: str, evidence_dir: Path | None) -> dict:
    """Run the canonical final-render review against the hash-bound master."""
    script = Path(__file__).resolve().parents[2] / "review" / "final-render" / "scripts" / "inspect.py"
    spec = importlib.util.spec_from_file_location("content_studio_final_inspect", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("Final-render inspector is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.inspect_master(output, digest,
                                 evidence_dir / "safe-zones" if evidence_dir else None)


def _mastering_result(analysis: dict | None, delivered: dict | None) -> dict:
    """Compare the exact encoded audio with the approved measured decision."""
    if not analysis or not delivered:
        return {"status": "REVIEW", "reason": "Final-mix analysis or output measurement missing"}
    integrated = delivered.get("integrated_lufs")
    peak = delivered.get("true_peak_dbtp")
    decision = analysis.get("decision")
    if integrated is None or peak is None:
        status = "REVIEW"
        reason = "Delivered audio is silent or unmeasurable"
    elif decision == "FIX":
        status = "FIX" if abs(integrated + 16) <= 1 and peak <= -1.5 else "REVIEW"
        reason = "Measured correction met target" if status == "FIX" else "Measured correction missed final output gate"
    elif decision == "SKIP":
        status = "SKIP" if abs(integrated + 16) <= 1 and peak <= -1.5 else "REVIEW"
        reason = "Acceptable mix was preserved" if status == "SKIP" else "Previously acceptable mix missed output gate"
    else:
        status, reason = "REVIEW", analysis.get("reason", "Analysis needs review")
    return {**delivered, "status": status, "reason": reason,
            "decision": decision, "baseline": analysis.get("measurement"),
            "target_lufs": -16, "target_true_peak_dbtp": -1.5}


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-1200:])


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
    picture_copy = None
    if resolved["video_policy"] == "copy_source":
        picture_copy = verify_picture_copy(resolved["clips"][0]["path"], output)
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
    retimed = [clip for clip in resolved["clips"] if clip.get("retime_resolved")]
    retime_verification = None
    if retimed:
        # A retime changes frame count. Check the exact coded output rather
        # than treating a plausible container duration as delivery proof.
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-count_frames", "-show_entries", "stream=nb_read_frames",
            "-of", "json", str(output)], capture_output=True, text=True)
        if result.returncode:
            raise ValueError("Cannot count exact-master retime frames")
        delivered = int(json.loads(result.stdout)["streams"][0]["nb_read_frames"])
        expected = round(resolved["duration"] * resolved["fps"])
        if delivered != expected:
            raise ValueError(f"Retime frame count differs: {delivered} != {expected}")
        retime_verification = {
            "status": "REVIEW", "expected_master_frames": expected,
            "delivered_master_frames": delivered,
            "spans": [{"id": clip["id"], "method": clip["retime_resolved"]["method"],
                       "start": clip["start"], "end": clip["end"],
                       "source_audio": clip["retime_resolved"]["audio"]}
                      for clip in retimed],
            "human_motion_and_sound_review": "pending",
        }
    inspection = _inspect_master(output, record["output_sha256"], evidence_dir)
    mastering = None
    if any(item["method"] == "loudnorm" for item in resolved["operations"]):
        mastering = _mastering_result(record.get("audio_analysis"), inspection["loudness"])
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
        for index, clip in enumerate(retimed):
            positions = {"first": clip["start"] + .5 / resolved["fps"],
                         "middle": (clip["start"] + clip["end"]) / 2,
                         "last": clip["end"] - .5 / resolved["fps"]}
            samples = []
            for label, at in positions.items():
                frame = evidence_dir / f"retime-{index:03d}-{label}.png"
                audio_sample = evidence_dir / f"retime-{index:03d}-{label}.wav"
                if not frame.exists():
                    _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                          "-ss", f"{at:.6f}", "-i", str(output), "-frames:v", "1",
                          "-c:v", "png", str(frame)])
                if not audio_sample.exists():
                    _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                          "-ss", f"{max(0, at - .1):.6f}", "-t", "0.2", "-i", str(output),
                          "-vn", "-c:a", "pcm_s16le", str(audio_sample)])
                samples.append({"position": label, "at": round(at, 3),
                                "frame": str(frame), "audio": str(audio_sample)})
            evidence.append({"id": clip["id"], "method": clip["retime_resolved"]["method"],
                             "range": [clip["start"], clip["end"]], "samples": samples})
        for index, cue in enumerate(resolved["audio"]):
            # Recorder drift needs an early and a late listen on the exact
            # master; one start sample cannot establish end-of-edit sync.
            positions = ([max(.1, resolved["duration"] * .1),
                          max(.1, resolved["duration"] - 1.1)]
                         if cue["kind"] == "external_sync" else [float(cue["start"])])
            for sample_index, at in enumerate(dict.fromkeys(positions)):
                sample = evidence_dir / f"audio-{index:03d}-{sample_index:02d}.wav"
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
            "evidence": evidence, "master_inspection": inspection,
            "retime_verification": retime_verification,
            "human_review_required": True,
        }, indent=2) + "\n", encoding="utf-8")
    return {
        "verified": True,
        "output": str(output),
        "duration": info["duration"],
        "resolution": [resolved["width"], resolved["height"]],
        "fps": fps,
        "audio_sample_rate": 48000,
        "picture_copy": picture_copy,
        "mastering": mastering,
        "retime_verification": retime_verification,
        "master_inspection": inspection,
        "evidence": evidence,
        "human_review_required": True,
    }
