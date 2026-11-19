"""Diagnose separate-recorder offset and drift without altering camera originals."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np

SAMPLE_RATE = 8000
ENVELOPE_HZ = 50


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _run(command: list[str], *, binary: bool = False):
    result = subprocess.run(command, capture_output=True, text=not binary)
    if result.returncode:
        error = result.stderr.decode(errors="replace") if binary else result.stderr
        raise RuntimeError(error[-1000:])
    return result.stdout


def _duration(path: Path) -> float:
    probe = json.loads(_run(["ffprobe", "-v", "error", "-show_format", "-of", "json", str(path)]))
    return float(probe["format"].get("duration") or 0)


def _envelope(path: Path, start: float, duration: float) -> np.ndarray:
    raw = _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}",
                "-t", f"{duration:.3f}", "-i", str(path), "-vn", "-ac", "1",
                "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"], binary=True)
    audio = np.frombuffer(raw, dtype="<f4")
    block = SAMPLE_RATE // ENVELOPE_HZ
    audio = audio[:len(audio) // block * block]
    if not len(audio):
        return np.empty(0)
    return np.sqrt(np.mean(audio.reshape(-1, block).astype(np.float64) ** 2, axis=1))


def _activity(envelope: np.ndarray) -> bool:
    # A steady hum or silence has no useful temporal fingerprint.
    return bool(len(envelope) >= ENVELOPE_HZ * 4
                and envelope.max(initial=0) > .001
                and np.std(envelope) > max(.0005, np.mean(envelope) * .08))


def _candidate_lags(reference: np.ndarray, external: np.ndarray,
                    max_lag: int) -> list[tuple[int, float]]:
    left = reference - np.mean(reference)
    right = external - np.mean(external)
    raw = np.correlate(left, right, "full")
    lags = np.arange(-len(right) + 1, len(left))
    left_power = np.concatenate(([0], np.cumsum(left * left)))
    right_power = np.concatenate(([0], np.cumsum(right * right)))
    results = []
    for lag, dot in zip(lags, raw):
        if abs(lag) > max_lag:
            continue
        if lag >= 0:
            length = min(len(left) - lag, len(right))
            la, ra = lag, 0
        else:
            length = min(len(left), len(right) + lag)
            la, ra = 0, -lag
        if length < ENVELOPE_HZ * 4:
            continue
        energy = (left_power[la + length] - left_power[la]) * (
            right_power[ra + length] - right_power[ra])
        if energy > 1e-12:
            results.append((int(lag), float(dot / math.sqrt(energy))))
    return sorted(results, key=lambda item: item[1], reverse=True)


def _local_offset(reference: Path, external: Path, at: float,
                  expected_offset: float) -> tuple[float, float] | None:
    span, margin = 5.0, 2.0
    recorder_start = max(0, at - expected_offset - margin)
    camera = _envelope(reference, at, span)
    recorder = _envelope(external, recorder_start, span + margin * 2)
    if not _activity(camera) or not _activity(recorder) or len(recorder) < len(camera):
        return None
    scores = _candidate_lags(recorder, camera, len(recorder))
    if not scores:
        return None
    best_lag, score = scores[0]
    return (at - recorder_start - best_lag / ENVELOPE_HZ, score)


def analyze(reference: Path, external: Path, search_seconds: float = 60) -> dict:
    reference, external = reference.resolve(), external.resolve()
    if reference == external or not reference.is_file() or not external.is_file():
        raise ValueError("Sync needs distinct existing camera and recorder files")
    if not 2 <= search_seconds <= 180:
        raise ValueError("search_seconds must be 2-180")
    reference_duration, external_duration = _duration(reference), _duration(external)
    span = min(search_seconds + 10, reference_duration, external_duration)
    camera, recorder = (_envelope(path, 0, span) for path in (reference, external))
    report = {"reference": str(reference), "reference_sha256": sha256_file(reference),
              "external": str(external), "external_sha256": sha256_file(external),
              "reference_duration_seconds": reference_duration,
              "external_duration_seconds": external_duration,
              "method": "rms-envelope-correlation-v1", "search_seconds": search_seconds,
              "offset_seconds": None, "drift_ppm": None, "confidence": 0.0,
              "status": "UNSUPPORTED", "reason": None, "human_review_required": True}
    if not _activity(camera) or not _activity(recorder):
        report["reason"] = "Camera or recorder audio is silent, steady, or too short"
        return report
    scores = _candidate_lags(camera, recorder, round(search_seconds * ENVELOPE_HZ))
    if not scores:
        report["reason"] = "No overlapping, active audio inside the search window"
        return report
    lag, best = scores[0]
    second = max((value for at, value in scores if abs(at - lag) >= ENVELOPE_HZ // 2),
                 default=-1.0)
    report["confidence"] = round(max(0.0, min(1.0, best * max(0, best - second) * 10)), 3)
    report["peak_correlation"] = round(best, 3)
    report["alternate_correlation"] = round(second, 3)
    if best < .35 or best - second < .06:
        report["reason"] = "Audio match is weak or ambiguous; seek a manual sync marker"
        return report
    coarse = lag / ENVELOPE_HZ
    first_at = max(5.0, coarse + 5.0)
    last_at = min(reference_duration - 7.0, external_duration + coarse - 7.0)
    anchors = []
    if last_at - first_at >= 20:
        for at in (first_at, last_at):
            anchor = _local_offset(reference, external, at, coarse)
            if anchor is None or anchor[1] < .4:
                report["reason"] = "Offset found; drift anchor is uncertain"
                break
            anchors.append({"picture_at": round(at, 3),
                            "offset_seconds": round(anchor[0], 4),
                            "correlation": round(anchor[1], 3)})
    if len(anchors) == 2:
        slope = ((anchors[1]["offset_seconds"] - anchors[0]["offset_seconds"])
                 / (anchors[1]["picture_at"] - anchors[0]["picture_at"]))
        if abs(slope) > .005:
            report["reason"] = "Measured drift exceeds the bounded timeline adapter"
            report["anchors"] = anchors
            return report
        offset_zero = anchors[0]["offset_seconds"] - slope * anchors[0]["picture_at"]
        report["offset_seconds"] = round(offset_zero, 4)
        report["drift_ppm"] = round(slope * 1_000_000, 1)
    else:
        report["offset_seconds"] = round(coarse, 4)
        report["drift_ppm"] = None
    report["anchors"] = anchors
    report["status"] = "REVIEW"
    if report["reason"] is None and report["drift_ppm"] is None:
        report["reason"] = "Offset candidate; clip too short for reliable drift estimate"
    return report


def audition(report: dict, output: Path, at: float, duration: float) -> None:
    reference, external = Path(report["reference"]), Path(report["external"])
    if (report.get("status") != "REVIEW" or report.get("offset_seconds") is None
            or sha256_file(reference) != report["reference_sha256"]
            or sha256_file(external) != report["external_sha256"]):
        raise ValueError("Sync candidate or source hash is stale")
    if not 0 <= at < report["reference_duration_seconds"] or not 0 < duration <= 10:
        raise ValueError("Audition must be a bounded picture interval")
    offset = float(report["offset_seconds"])
    speed = 1 - float(report.get("drift_ppm") or 0) / 1_000_000
    recorder_at = max(0, (at - offset) * speed)
    delay = round(max(0, offset - at) * 1000)
    output.parent.mkdir(parents=True, exist_ok=True)
    graph = (f"[0:a:0]atrim=duration={duration:g},asetpts=PTS-STARTPTS,"
             "aresample=48000,aformat=channel_layouts=mono,apad,"
             f"atrim=duration={duration:g}[camera];"
             f"[1:a:0]atempo={speed:.8f},adelay={delay},"
             "aresample=48000,aformat=channel_layouts=mono,apad,"
             f"atrim=duration={duration:g}[recorder];"
             "[camera][recorder]amerge=inputs=2[a]")
    _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
          "-ss", f"{at:.3f}", "-t", f"{duration:.3f}", "-i", str(reference),
          "-ss", f"{recorder_at:.3f}", "-t", f"{duration * speed + 1:.3f}",
          "-i", str(external), "-filter_complex", graph, "-map", "[a]",
          "-c:a", "pcm_s16le", str(output)])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    study = commands.add_parser("analyze")
    study.add_argument("--reference", required=True, type=Path)
    study.add_argument("--external", required=True, type=Path)
    study.add_argument("--search-seconds", type=float, default=60)
    study.add_argument("--report", required=True, type=Path)
    listen = commands.add_parser("audition")
    listen.add_argument("--report", required=True, type=Path)
    listen.add_argument("--output", required=True, type=Path)
    listen.add_argument("--at", type=float, required=True)
    listen.add_argument("--duration", type=float, required=True)
    args = parser.parse_args()
    if args.command == "analyze":
        result = analyze(args.reference, args.external, args.search_seconds)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
    else:
        audition(json.loads(args.report.read_text(encoding="utf-8")),
                 args.output, args.at, args.duration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
