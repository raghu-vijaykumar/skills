"""Hash-bound technical inspection of the exact Content Studio delivery master."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _run(command: list[str]) -> subprocess.CompletedProcess:
    # FFprobe returns UTF-8 tags even when Windows uses a legacy console code page.
    result = subprocess.run(command, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-1200:])
    return result


def _events(log: str, pattern: str, kind: str) -> list[dict]:
    return [{"kind": kind, "start": round(float(start), 3),
             "end": round(float(end), 3), "status": "REVIEW"}
            for start, end in re.findall(pattern, log)]


def _paired_events(log: str, start_tag: str, end_tag: str,
                   kind: str, duration: float) -> list[dict]:
    """Pair detector markers across log lines, including an open interval at EOF."""
    markers = re.findall(rf"({start_tag}|{end_tag}):\s*([\d.]+)", log)
    pending = None
    findings = []
    for tag, value in markers:
        at = float(value)
        if tag == start_tag:
            pending = at
        elif pending is not None:
            findings.append({"kind": kind, "start": round(pending, 3),
                             "end": round(at, 3), "status": "REVIEW"})
            pending = None
    if pending is not None:
        findings.append({"kind": kind, "start": round(pending, 3),
                         "end": round(duration, 3), "status": "REVIEW"})
    return findings


def _video_candidates(log: str, duration: float) -> list[dict]:
    findings = _events(log, r"black_start:([\d.]+)\s+black_end:([\d.]+)", "black")
    findings += _paired_events(log, "freeze_start", "freeze_end", "frozen", duration)
    frames = [(float(at), float(value)) for at, value in re.findall(
        r"frame:\d+\s+pts:\d+\s+pts_time:([\d.]+).*?lavfi\.signalstats\.YAVG=([\d.]+)",
        log, flags=re.DOTALL)]
    # A one-frame luma excursion that immediately returns is a flash candidate;
    # the reviewer decides whether it is an intended cut or graphic.
    for previous, current, following in zip(frames, frames[1:], frames[2:]):
        if (current[1] - max(previous[1], following[1]) >= 45
                and abs(previous[1] - following[1]) <= 15):
            findings.append({"kind": "flash", "start": round(current[0], 3),
                             "end": round(following[0], 3), "status": "REVIEW"})
    return sorted(findings, key=lambda item: (item["start"], item["kind"]))


def _audio_candidates(log: str, duration: float) -> list[dict]:
    return _paired_events(log, "silence_start", "silence_end", "audio_silence", duration)


def _loudness(log: str) -> dict | None:
    marker = log.rfind('"input_i"')
    start, end = log.rfind("{", 0, marker), log.find("}", marker)
    if marker < 0 or start < 0 or end < 0:
        return None
    data = json.loads(log[start:end + 1])
    def finite(value: str) -> float | None:
        number = float(value)
        return number if math.isfinite(number) else None

    return {"integrated_lufs": finite(data["input_i"]),
            "true_peak_dbtp": finite(data["input_tp"]),
            "loudness_range_lu": finite(data["input_lra"])}


def inspect_master(path: Path, expected_sha256: str, evidence_dir: Path | None = None) -> dict:
    """Return timecoded candidates; no detector can approve creative intent."""
    path = path.resolve()
    if not path.is_file() or sha256_file(path) != expected_sha256:
        raise ValueError("Exact master is missing or its bytes changed")
    probe = json.loads(_run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                             "-of", "json", str(path)]).stdout)
    duration = float(probe.get("format", {}).get("duration") or 0)
    streams = probe.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not video or not audio or duration <= 0:
        raise ValueError("Exact master needs a nonempty video and audio stream")
    picture_log = _run(["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "info",
                        "-i", str(path), "-an", "-vf",
                        "blackdetect=d=0.1:pix_th=0.1,freezedetect=n=-50dB:d=1,"
                        "scale=160:90,signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                        "-f", "null", "-"]).stderr
    sound_log = _run(["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "info",
                      "-i", str(path), "-vn", "-af",
                      "silencedetect=noise=-50dB:d=0.25,"
                      "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                      "-f", "null", "-"]).stderr
    findings = _video_candidates(picture_log, duration) + _audio_candidates(sound_log, duration)
    guides = []
    if evidence_dir is not None:
        evidence_dir = evidence_dir.resolve()
        evidence_dir.mkdir(parents=True, exist_ok=True)
        for index, at in enumerate(sorted({0.0, duration * .25, duration * .5,
                                           duration * .75, max(0.0, duration - .1)})):
            still = evidence_dir / f"safe-zone-{index:02d}.png"
            # Guides are separate review images; they never alter the delivered master.
            _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{at:.3f}",
                  "-i", str(path), "-vf",
                  "drawbox=x=iw*0.05:y=ih*0.05:w=iw*0.9:h=ih*0.9:color=yellow@0.9:t=2,"
                  "drawbox=x=iw*0.1:y=ih*0.1:w=iw*0.8:h=ih*0.8:color=cyan@0.9:t=2",
                  "-frames:v", "1", str(still)])
            guides.append({"at": round(at, 3), "path": str(still), "sha256": sha256_file(still)})
    if sha256_file(path) != expected_sha256:
        raise ValueError("Exact master changed during inspection")
    return {"output": str(path), "output_sha256": expected_sha256,
            "duration_seconds": round(duration, 3),
            "format": {"container": probe["format"].get("format_name"),
                       "video_codec": video.get("codec_name"), "pixel_format": video.get("pix_fmt"),
                       "width": video.get("width"), "height": video.get("height"),
                       "fps": video.get("avg_frame_rate"),
                       "color_range": video.get("color_range"),
                       "color_primaries": video.get("color_primaries"),
                       "color_transfer": video.get("color_transfer"),
                       "color_space": video.get("color_space"),
                       "audio_codec": audio.get("codec_name"),
                       "audio_sample_rate": audio.get("sample_rate")},
            "loudness": _loudness(sound_log), "findings": findings,
            "safe_zone_guides": guides, "status": "REVIEW" if findings else "SKIP",
            "human_review_required": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = inspect_master(args.master, args.sha256, args.evidence_dir)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
