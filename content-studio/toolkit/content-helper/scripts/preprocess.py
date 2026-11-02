"""Batch voice, stabilization, and blur review for camera clips.

This module deliberately treats a Dolby Vision label as a verified output
property, not something inferred from a 10-bit HDR encode.
"""

from __future__ import annotations

import csv
import html
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import wave
from fractions import Fraction
from pathlib import Path

from common import channel_root, select_channels
import ordering


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv"}
SAMPLE_RATE = 48000
QUIET_GAIN_DB = -13.0
MAX_VOICE_BOOST_DB = 13.0
VOICE_RMS_DBFS = -21.0
LIMIT = 10 ** (-1 / 20)


class ProcessingError(RuntimeError):
    pass


def command(argv: list[str], *, cwd: Path | None = None, stderr: bool = False) -> str:
    """Keep FFmpeg progress out of the console while retaining useful errors."""
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        lines = [line for line in result.stderr.splitlines()
                 if not re.match(r"\s*(frame=|size=|time=|bitrate=|speed=)", line)]
        raise ProcessingError(f"{' '.join(argv[:3])} failed: " + "\n".join(lines[-8:]))
    return result.stderr if stderr else result.stdout


def probe(path: Path) -> dict:
    return json.loads(command(["ffprobe", "-v", "error", "-show_streams",
                               "-show_format", "-of", "json", str(path)]) or "{}")


def streams(info: dict) -> tuple[dict, dict | None]:
    video = next((s for s in info.get("streams", [])
                  if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")), None)
    if not video:
        raise ProcessingError("no camera video stream")
    # Apple clips can also contain APAC spatial audio; the regular AAC track is
    # the appropriate starting point for intelligible stereo dialogue.
    audio = next((s for s in info.get("streams", [])
                  if s.get("codec_type") == "audio" and s.get("channels", 0) <= 2), None)
    return video, audio


def dolby_info(video: dict) -> dict | None:
    return next((item for item in video.get("side_data_list", [])
                 if item.get("side_data_type") == "DOVI configuration record"), None)


def source_files(args) -> tuple[list[Path], Path]:
    slug, _ = select_channels(args.cfg, args.channel)[0]
    channel = channel_root(args.cfg, slug)
    if args.path:
        source = Path(args.path).expanduser().resolve()
        if not source.is_file() or source.suffix.lower() not in VIDEO_EXTENSIONS:
            raise ProcessingError("--path must name a camera video file")
        return [source], Path(args.out).expanduser().resolve() if args.out else source.parent / "processed-clips"
    if not args.draft or Path(args.draft).name != args.draft:
        raise ProcessingError("pass a draft folder name with --draft, or use --path")
    draft = channel / "drafts" / args.draft
    if not draft.is_dir():
        raise ProcessingError(f"draft not found: {draft}")
    sources = ordering.camera_files(draft)
    if args.clip:
        sources = [p for p in sources if p.name.lower() == args.clip.lower()
                   or ordering.original_name(p.name).lower() == args.clip.lower()]
    if not sources:
        raise ProcessingError("no matching camera clips in the draft root")
    return sources, Path(args.out).expanduser().resolve() if args.out else draft / "processed-clips"


def extract_audio(source: Path, audio: dict, target: Path) -> None:
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(source), "-map", f"0:{audio['index']}", "-vn", "-ac", "2",
             "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(target)])


def deepfilter(source: Path, out_dir: Path) -> Path:
    exe = shutil.which("deep-filter") or shutil.which("deepFilter")
    if not exe:
        raise ProcessingError("DeepFilterNet is required: install deep-filter.exe or pip install deepfilternet")
    out_dir.mkdir(parents=True, exist_ok=True)
    # The standalone Rust release works on Windows without a Python wheel;
    # the Python package exposes a different CLI spelling and output flag.
    args = [exe, "-D", "-o", str(out_dir), str(source)] if Path(exe).stem.lower() == "deep-filter" else [
        exe, "--compensate-delay", "--output-dir", str(out_dir), str(source)]
    command(args)
    outputs = list(out_dir.glob("*.wav"))
    if len(outputs) != 1:
        raise ProcessingError("DeepFilterNet did not produce one enhanced WAV")
    return outputs[0]


def pcm16(path: Path) -> tuple[int, "numpy.ndarray"]:
    import numpy as np

    with wave.open(str(path), "rb") as wav:
        if wav.getsampwidth() != 2:
            raise ProcessingError("expected 16-bit PCM after audio conversion")
        rate, channels = wav.getframerate(), wav.getnchannels()
        data = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
    return rate, data.reshape(-1, channels).astype(np.float32) / 32768.0


def speech_intervals(clean_pcm: Path) -> list[tuple[float, float]]:
    try:
        import torch
        from silero_vad import get_speech_timestamps, load_silero_vad
    except ImportError as exc:
        raise ProcessingError("Silero VAD is required: pip install silero-vad") from exc
    import numpy as np

    with wave.open(str(clean_pcm), "rb") as wav:
        rate = wav.getframerate()
    if rate != SAMPLE_RATE:
        raise ProcessingError("unexpected speech input sample rate")
    # FFmpeg handles the 48-to-16 kHz conversion so the VAD sees the model's
    # supported input rate, even when the camera recorded spatial audio.
    vad_pcm = clean_pcm.with_name("vad-16k.wav")
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(clean_pcm), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
             str(vad_pcm)])
    _, vad_samples = pcm16(vad_pcm)
    torch.set_num_threads(1)
    detected = get_speech_timestamps(torch.from_numpy(np.ascontiguousarray(vad_samples[:, 0])),
                                     load_silero_vad(), sampling_rate=16000,
                                     return_seconds=True)
    return [(float(p["start"]), float(p["end"])) for p in detected]


def gain_envelope(samples, intervals: list[tuple[float, float]]):
    import numpy as np

    count = len(samples)
    envelope = np.full(count, 10 ** (QUIET_GAIN_DB / 20), dtype=np.float32)
    fades = int(0.12 * SAMPLE_RATE)
    pad = int(0.15 * SAMPLE_RATE)
    speech_levels = []
    for start, end in intervals:
        raw_start = max(0, int(start * SAMPLE_RATE))
        raw_end = min(count, int(end * SAMPLE_RATE))
        if raw_end <= raw_start:
            continue
        rms = float(np.sqrt(np.mean(samples[raw_start:raw_end] ** 2)))
        gain_db = min(MAX_VOICE_BOOST_DB,
                      VOICE_RMS_DBFS - 20 * math.log10(max(rms, 1e-6)))
        speech_levels.append(round(gain_db, 2))
        gain = 10 ** (gain_db / 20)
        left, right = max(0, raw_start - pad), min(count, raw_end + pad)
        ramp = min(fades, (right - left) // 2)
        target = np.full(right - left, gain, dtype=np.float32)
        if ramp:
            target[:ramp] = np.linspace(envelope[0], gain, ramp)
            target[-ramp:] = np.linspace(gain, envelope[0], ramp)
        envelope[left:right] = np.maximum(envelope[left:right], target)
    return envelope, speech_levels


def enhance_audio(source: Path, audio: dict, work: Path, report: dict,
                  denoise: str = "auto") -> Path:
    import numpy as np

    original = work / "original.wav"
    extract_audio(source, audio, original)
    available = shutil.which("deep-filter") or shutil.which("deepFilter")
    engine = "deepfilter" if denoise == "deepfilter" or denoise == "auto" and available else "ffmpeg"
    if engine == "deepfilter":
        enhanced = deepfilter(original, work / "deepfilter")
    else:
        enhanced = work / "fft-denoised.wav"
        command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                 "-i", str(original), "-af", "highpass=f=80,afftdn=nr=12:tn=1",
                 "-c:a", "pcm_s16le", str(enhanced)])
    report["denoise_engine"] = engine
    clean = work / "clean.wav"
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(enhanced), "-ac", "2", "-ar", str(SAMPLE_RATE),
             "-c:a", "pcm_s16le", str(clean)])
    _, raw = pcm16(original)
    _, samples = pcm16(clean)
    # Model delay or padding must never move dialogue against the camera frame.
    if len(samples) < len(raw):
        samples = np.pad(samples, ((0, len(raw) - len(samples)), (0, 0)))
    samples = samples[:len(raw)]
    intervals = speech_intervals(clean)
    envelope, levels = gain_envelope(samples, intervals)
    report["audio"] = {"speech_intervals": intervals, "speech_gain_db": levels,
                       "quiet_gain_db": QUIET_GAIN_DB, "peak_ceiling_dbfs": -1}
    float_audio = work / "gained.f32le"
    (samples * envelope[:, None]).astype("<f4").tofile(float_audio)
    result = work / "enhanced-voice.wav"
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", "2", "-i", str(float_audio),
             "-af", f"alimiter=limit={LIMIT:.6f}:attack=5:release=50:level=0",
             "-c:a", "pcm_s16le", str(result)])
    return result


def frame_times(source: Path) -> list[float]:
    output = command(["ffprobe", "-v", "error", "-select_streams", "v:0",
                      "-show_entries", "frame=best_effort_timestamp_time",
                      "-of", "csv=p=0", str(source)])
    return [float(line.split(",")[0]) for line in output.splitlines()
            if line.strip() and line.split(",")[0] != "N/A"]


def sharpness_scores(source: Path, video: dict) -> list[float]:
    import numpy as np

    width = 320
    height = max(64, round(width * int(video["height"]) / int(video["width"]) / 2) * 2)
    frame_bytes = width * height
    proc = subprocess.Popen(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                             "-i", str(source), "-map", f"0:{video['index']}",
                             "-vf", f"scale={width}:{height},format=gray", "-fps_mode", "passthrough",
                             "-f", "rawvideo", "-"], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    scores = []
    try:
        while True:
            data = proc.stdout.read(frame_bytes)
            if not data:
                break
            if len(data) != frame_bytes:
                raise ProcessingError("incomplete frame during blur analysis")
            image = np.frombuffer(data, dtype=np.uint8).reshape(height, width).astype(np.int16)
            if image.mean() < 18 or image.std() < 10:
                scores.append(float("nan"))
                continue
            center = image[1:-1, 1:-1]
            laplace = (4 * center - image[:-2, 1:-1] - image[2:, 1:-1]
                       - image[1:-1, :-2] - image[1:-1, 2:])
            scores.append(float(laplace.var()))
        error = proc.stderr.read().decode("utf-8", errors="replace")
        if proc.wait() != 0:
            raise ProcessingError("blur analysis failed: " + "\n".join(error.splitlines()[-5:]))
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    return scores


def blur_candidates(times: list[float], scores: list[float], duration: float) -> list[dict]:
    import numpy as np

    if len(times) != len(scores):
        raise ProcessingError(f"frame/timestamp mismatch in blur scan: {len(scores)} vs {len(times)}")
    if not scores:
        return []
    values = np.asarray(scores)
    valid = values[np.isfinite(values)]
    if len(valid) < 5:
        return []
    baseline = float(np.percentile(valid, 75))
    # This threshold only proposes edits. Low-detail shots can also have a
    # small sharpness score, so no span is removed without review.
    threshold = baseline * 0.28
    selected = [i for i, score in enumerate(scores)
                if math.isfinite(score) and score < threshold]
    if not selected:
        return []
    median_gap = float(np.median(np.diff(times))) if len(times) > 1 else 1 / 30
    groups: list[list[int]] = []
    for index in selected:
        if groups and times[index] - times[groups[-1][-1]] <= 1.5 * median_gap:
            groups[-1].append(index)
        else:
            groups.append([index])
    candidates = []
    for group in groups:
        first, last = group[0], group[-1]
        start = max(0.0, times[first] - median_gap / 2)
        end = min(duration, times[last] + median_gap / 2)
        candidates.append({"id": len(candidates) + 1, "start": round(start, 3),
                           "end": round(end, 3), "score": round(min(scores[i] for i in group), 2),
                           "remove": "", "notes": ""})
    return candidates


def write_review(source: Path, video: dict, duration: float, folder: Path, report: dict) -> None:
    times = frame_times(source)
    scores = sharpness_scores(source, video)
    candidates = blur_candidates(times, scores, duration)
    report["blur"] = {"frames_scanned": len(scores), "candidates": len(candidates),
                      "review_csv": "review.csv", "review_html": "review.html"}
    with (folder / "review.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["id", "start", "end", "score", "remove", "notes"])
        writer.writeheader()
        writer.writerows(candidates)
    rows = []
    for item in candidates:
        name = f"blur-{item['id']:03d}.jpg"
        command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                 "-ss", str((item["start"] + item["end"]) / 2), "-i", str(source),
                 "-map", f"0:{video['index']}", "-frames:v", "1", "-vf", "scale=480:-2",
                 str(folder / name)])
        rows.append(f"<tr><td><img src='{name}' width='480'></td><td>{item['start']:.3f}–{item['end']:.3f}s"
                    f"</td><td>{item['score']:.1f}</td></tr>")
    page = ("<!doctype html><meta charset='utf-8'><title>Blur review</title>"
            "<style>body{font:16px sans-serif;max-width:900px;margin:2rem auto}td{padding:1rem;border-bottom:1px solid #aaa}"
            "img{max-width:100%}</style>"
            f"<h1>{html.escape(source.name)} — blur review</h1>"
            "<p>These are candidates, not automatic cuts. Set <code>remove</code> to <code>yes</code> "
            "for approved rows in review.csv, then run preprocess with --apply-review.</p>"
            "<table><tr><th>Frame</th><th>Time</th><th>Sharpness</th></tr>" + "".join(rows) + "</table>")
    (folder / "review.html").write_text(page, encoding="utf-8")


def approved_cuts(csv_path: Path) -> list[tuple[float, float]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    cuts = []
    for row in rows:
        if row["remove"].strip().lower() in {"yes", "y", "true", "1"}:
            start, end = float(row["start"]), float(row["end"])
            if end <= start or start < 0:
                raise ProcessingError(f"invalid approved cut {row['id']}")
            cuts.append((start, end))
    return sorted(cuts)


def keep_ranges(duration: float, cuts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    cursor = 0.0
    kept = []
    for start, end in cuts:
        if start >= duration:
            raise ProcessingError("approved cut starts beyond the clip")
        if start > cursor:
            kept.append((cursor, start))
        cursor = max(cursor, min(duration, end))
    if cursor < duration:
        kept.append((cursor, duration))
    if not kept:
        raise ProcessingError("approved cuts remove the entire clip")
    return kept


def color_args(video: dict) -> list[str]:
    options = []
    for field, flag in (("color_primaries", "-color_primaries"),
                        ("color_transfer", "-color_trc"),
                        ("color_space", "-colorspace"), ("color_range", "-color_range")):
        value = video.get(field)
        if value and value not in {"unknown", "unspecified"}:
            options += [flag, str(value)]
    return options


def encoding_args(video: dict, rpu: bool = False) -> list[str]:
    hdr = video.get("color_transfer") in {"arib-std-b67", "smpte2084"}
    ten_bit = hdr or "10" in video.get("pix_fmt", "") or rpu
    if ten_bit:
        params = "vbv-maxrate=20000:vbv-bufsize=20000:hrd=1"
        return ["-c:v", "libx265", "-preset", "medium", "-crf", "20",
                "-pix_fmt", "yuv420p10le", "-x265-params", params,
                "-dolbyvision", "0" if rpu else "-1", "-tag:v", "hvc1", *color_args(video)]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", *color_args(video)]


def detect_stabilization(source: Path, work: Path) -> None:
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(source), "-map", "0:v:0",
             "-vf", "vidstabdetect=shakiness=5:accuracy=9:result=transforms.trf",
             "-an", "-f", "null", os.devnull], cwd=work)


def video_filter(kept: list[tuple[float, float]] | None,
                 video: dict) -> tuple[str, str, str | None]:
    # vidstab's automatic border crop can reduce the encoded dimensions;
    # restore the camera frame size so downstream clip assembly stays stable.
    stabilizer = ("vidstabtransform=input=transforms.trf:smoothing=15:optzoom=1,"
                  f"scale={video['width']}:{video['height']}:flags=lanczos")
    if not kept:
        return stabilizer, "0:v:0", None
    if len(kept) == 1:
        start, end = kept[0]
        graph = (f"[0:v:0]{stabilizer},trim=start={start:.6f}:end={end:.6f},"
                 f"setpts=PTS-STARTPTS[v];[1:a:0]atrim=start={start:.6f}:end={end:.6f},"
                 "asetpts=PTS-STARTPTS[a]")
        return graph, "[v]", "[a]"
    n = len(kept)
    video_parts = [f"[vs{i}]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[v{i}]"
                   for i, (start, end) in enumerate(kept)]
    audio_parts = [f"[as{i}]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[a{i}]"
                   for i, (start, end) in enumerate(kept)]
    graph = (f"[0:v:0]{stabilizer},split={n}" + "".join(f"[vs{i}]" for i in range(n))
             + ";" + ";".join(video_parts)
             + f";[1:a:0]asplit={n}" + "".join(f"[as{i}]" for i in range(n))
             + ";" + ";".join(audio_parts)
             + ";" + "".join(f"[v{i}][a{i}]" for i in range(n))
             + f"concat=n={n}:v=1:a=1[v][a]")
    return graph, "[v]", "[a]"


def rpu_for_source(source: Path, work: Path, cuts: list[tuple[float, float]],
                   proof_seconds: float | None = None) -> None:
    dovi = shutil.which("dovi_tool")
    if not dovi:
        raise ProcessingError("dovi_tool is not installed; Dolby Vision video kept unchanged")
    raw = work / "source.hevc"
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(source), "-map", "0:v:0", "-c:v", "copy",
             "-bsf:v", "hevc_mp4toannexb", "-f", "hevc", str(raw)])
    command([dovi, "extract-rpu", "-i", str(raw), "-o", "source-rpu.bin"], cwd=work)
    times = frame_times(source)
    summary = command([dovi, "info", "-i", "source-rpu.bin", "-s"], cwd=work)
    count = re.search(r"Frames:\s*(\d+)", summary)
    if not count or int(count.group(1)) != len(times):
        raise ProcessingError("source Dolby Vision RPU/frame count mismatch")
    removed = [i for i, stamp in enumerate(times)
               if any(start <= stamp < end for start, end in cuts)
               or proof_seconds is not None and stamp >= proof_seconds]
    if removed:
        groups = []
        for index in removed:
            if groups and index == groups[-1][-1] + 1:
                groups[-1].append(index)
            else:
                groups.append([index])
        config = {"remove": [f"{group[0]}-{group[-1]}" for group in groups]}
        (work / "rpu-edit.json").write_text(json.dumps(config), encoding="utf-8")
        command([dovi, "editor", "-i", "source-rpu.bin", "-j", "rpu-edit.json",
                 "-o", "rpu.bin"], cwd=work)
    else:
        shutil.copyfile(work / "source-rpu.bin", work / "rpu.bin")


def frame_count(path: Path) -> int:
    output = command(["ffprobe", "-v", "error", "-select_streams", "v:0",
                      "-count_frames", "-show_entries", "stream=nb_read_frames",
                      "-of", "default=nw=1:nk=1", str(path)])
    return int(output.strip())


def validate_render(source: Path, output: Path, source_video: dict,
                    kept: list[tuple[float, float]] | None, dv: bool) -> None:
    result = probe(output)
    video, audio = streams(result)
    if not audio:
        raise ProcessingError("render has no enhanced audio track")
    expected_duration = (sum(end - start for start, end in kept) if kept
                         else float(probe(source)["format"]["duration"]))
    video_duration = float(video.get("duration") or result["format"]["duration"])
    audio_duration = float(audio.get("duration") or result["format"]["duration"])
    if abs(video_duration - expected_duration) > 0.07 or abs(audio_duration - video_duration) > 0.07:
        raise ProcessingError("render duration or audio sync changed unexpectedly")
    for key in ("width", "height", "color_primaries", "color_transfer", "color_space"):
        if video.get(key) != source_video.get(key):
            raise ProcessingError(f"render changed {key}: {source_video.get(key)} -> {video.get(key)}")
    source_times = frame_times(source)
    expected = len(source_times) if not kept else sum(
        1 for stamp in source_times if any(start <= stamp < end for start, end in kept))
    actual = frame_count(output)
    if abs(actual - expected) > 1:
        raise ProcessingError(f"render changed frame count: expected {expected}, got {actual}")
    if dv:
        dovi = dolby_info(video)
        if not dovi or dovi.get("dv_profile") != 8 or not dovi.get("rpu_present_flag"):
            raise ProcessingError("render lost Dolby Vision Profile 8 RPU")
        if dovi.get("dv_bl_signal_compatibility_id") != 4:
            raise ProcessingError("render changed the Dolby Vision HLG compatibility ID")
    command(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-xerror", "-i", str(output), "-f", "null", os.devnull])


def stabilized_render(source: Path, audio: Path, video: dict, work: Path,
                      output: Path, cuts: list[tuple[float, float]],
                      proof_seconds: float | None = None) -> dict:
    dv = bool(dolby_info(video))
    detect_stabilization(source, work)
    duration = float(probe(source)["format"]["duration"])
    kept = keep_ranges(duration, cuts) if cuts else None
    if proof_seconds is not None:
        kept = [(0.0, min(duration, proof_seconds))]
    if dv:
        rpu_for_source(source, work, cuts, proof_seconds)
        times = frame_times(source)
        rate_text = video.get("r_frame_rate") or video.get("avg_frame_rate")
        if not rate_text or rate_text in {"0/0", "N/A"}:
            raise ProcessingError("source frame rate is unknown; Dolby Vision remux is unsafe")
        rate = Fraction(rate_text)
        if rate <= 0 or any(abs((stamp - times[0]) - i / float(rate)) > 0.5 / float(rate)
                            for i, stamp in enumerate(times)):
            raise ProcessingError("source has variable frame timing; Dolby Vision raw-bitstream remux is unsafe")
    graph, vmap, amap = video_filter(kept, video)
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "info",
           "-nostats", "-i", str(source), "-i", str(audio)]
    if amap:
        cmd += ["-filter_complex", graph, "-map", vmap, "-map", amap]
    else:
        cmd += ["-map", "0:v:0", "-map", "1:a:0", "-vf", graph]
    base_output = work / "base.mov" if dv else output
    cmd += [*encoding_args(video, rpu=dv), "-fps_mode", "passthrough",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(base_output)]
    log = command(cmd, cwd=work, stderr=True)
    if dv:
        dovi = shutil.which("dovi_tool")
        base_hevc = work / "base.hevc"
        injected = work / "injected.hevc"
        command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                 "-i", str(base_output), "-map", "0:v:0", "-c:v", "copy",
                 "-bsf:v", "hevc_mp4toannexb", "-f", "hevc", str(base_hevc)])
        command([dovi, "inject-rpu", "-i", str(base_hevc), "--rpu-in", "rpu.bin",
                 "-o", str(injected)], cwd=work)
        command([dovi, "extract-rpu", "-i", str(injected), "-o", "check-rpu.bin"], cwd=work)
        summary = command([dovi, "info", "-i", "check-rpu.bin", "-s"], cwd=work)
        expected_rpu = frame_count(base_output)
        count = re.search(r"Frames:\s*(\d+)", summary)
        if not count or int(count.group(1)) != expected_rpu:
            raise ProcessingError("injected Dolby Vision RPU/frame count mismatch")
        command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                 "-r", str(rate), "-i", str(injected), "-i", str(base_output),
                 "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "copy",
                 "-strict", "unofficial", "-tag:v", "hvc1", "-movflags", "+faststart",
                 str(output)])
    validate_render(source, output, video, kept, dv)
    crop = re.search(r"Frame Cropping:\s*(\d+)/(\d+)/(\d+)/(\d+)", log)
    crop_pct = None
    if crop:
        left, right, top, bottom = map(int, crop.groups())
        crop_pct = round(max((left + right) / int(video["width"]),
                             (top + bottom) / int(video["height"])) * 100, 2)
    return {"crop_percent": crop_pct, "crop_review": crop_pct is None or crop_pct > 10,
            "dolby_vision": dv, "playback_review_required": dv}


def voice_only_copy(source: Path, voice: Path, video: dict, output: Path) -> bool:
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(source), "-i", str(voice), "-map", f"0:{video['index']}",
             "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-tag:v", "hvc1", "-movflags", "+faststart", str(output)])
    info = probe(output)
    rendered, _ = streams(info)
    if not dolby_info(rendered) or not dolby_info(rendered).get("rpu_present_flag"):
        output.unlink(missing_ok=True)
        return False
    try:
        validate_render(source, output, video, None, True)
    except ProcessingError:
        output.unlink(missing_ok=True)
        return False
    return True


def safe_render(source: Path, audio: Path, video: dict, work: Path,
                output: Path, cuts: list[tuple[float, float]],
                proof_seconds: float | None = None) -> dict:
    try:
        return stabilized_render(source, audio, video, work, output, cuts, proof_seconds)
    except (ProcessingError, OSError, ValueError):
        # A file that failed a metadata or decode gate is not a usable export.
        output.unlink(missing_ok=True)
        raise


def silent_audio(duration: float, output: Path) -> Path:
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=stereo",
             "-t", str(duration), "-c:a", "pcm_s16le", str(output)])
    return output


def write_report(folder: Path, report: dict) -> None:
    (folder / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def process_clip(source: Path, output_root: Path, args, log) -> None:
    # Keep the extension in the folder name: IMG_123.MOV and IMG_123.MP4 can
    # legitimately coexist in one camera dump.
    # Camera numbers change when a new clip is inserted; the original camera
    # basename gives each analysis folder a stable identity across reorderings.
    folder = ordering.analysis_folder(output_root, source.name)
    folder.mkdir(parents=True, exist_ok=True)
    report_path = folder / "report.json"
    if report_path.exists() and not args.force and not args.apply_review and not args.dv_approved and not args.dv_proof:
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        if previous.get("source_bytes") == source.stat().st_size:
            # Keep the report's source pointer in sync with timeline renames.
            if previous.get("source") != str(source):
                previous["source"] = str(source)
                write_report(folder, previous)
            log(f"{source.name}: already processed (use --force to rebuild)")
            return
    info = probe(source)
    video, audio = streams(info)
    duration = float(info["format"]["duration"])
    dv = dolby_info(video)
    report = {"source": str(source), "source_bytes": source.stat().st_size,
              "duration_seconds": duration, "video": {
                  "width": video.get("width"), "height": video.get("height"),
                  "pixel_format": video.get("pix_fmt"),
                  "color_transfer": video.get("color_transfer"),
                  "dolby_vision_profile": dv.get("dv_profile") if dv else None},
              "status": "processing"}
    existing = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else None
    if args.dv_approved and not dv:
        raise ProcessingError("--dv-approved applies only to Dolby Vision clips")
    if args.dv_proof and not dv:
        raise ProcessingError("--dv-proof applies only to Dolby Vision clips")
    if args.dv_proof and not existing:
        raise ProcessingError("run preprocess once to prepare enhanced audio before --dv-proof")
    if args.dv_proof:
        if existing["source_bytes"] != source.stat().st_size:
            raise ProcessingError("source changed since preprocessing; rerun with --force")
        voice = folder / "enhanced-voice.wav"
        if not voice.exists():
            raise ProcessingError("enhanced voice WAV is missing")
        proof = folder / "dv-proof.mov"
        try:
            with tempfile.TemporaryDirectory(prefix="vlog-", dir=folder) as scratch:
                rendered = safe_render(source, voice, video, Path(scratch), proof,
                                       [], proof_seconds=3.0)
        except (ProcessingError, OSError, ValueError) as exc:
            existing["dv_proof_error"] = str(exc)
            existing.pop("dv_proof_validation", None)
            existing.pop("dv_proof_output", None)
            write_report(folder, existing)
            raise
        existing["dv_proof_validation"] = rendered
        existing["dv_proof_output"] = proof.name
        existing.pop("dv_proof_error", None)
        write_report(folder, existing)
        log(f"{source.name}: Dolby Vision proof -> {proof.name}; check playback before --dv-approved")
        return
    if args.dv_approved and not existing:
        raise ProcessingError("run preprocess and review its Dolby Vision proof first")
    if args.dv_approved and existing and not args.apply_review:
        if existing["source_bytes"] != source.stat().st_size:
            raise ProcessingError("source changed since Dolby Vision proof; rerun with --force")
        if not existing.get("dv_proof_validation") or not (folder / "dv-proof.mov").exists():
            raise ProcessingError("validated Dolby Vision proof is missing")
        voice = folder / "enhanced-voice.wav"
        if not voice.exists():
            raise ProcessingError("enhanced voice WAV is missing")
        with tempfile.TemporaryDirectory(prefix="vlog-", dir=folder) as scratch:
            rendered = safe_render(source, voice, video, Path(scratch),
                                   folder / "processed.mov", [])
        existing["render_validation"] = rendered
        existing["processed_output"] = "processed.mov"
        existing["status"] = "dv_playback_review_required"
        write_report(folder, existing)
        log(f"{source.name}: stabilized Dolby Vision render requires playback review")
        return
    if args.apply_review and not existing:
        raise ProcessingError("run preprocess once to create review.csv before --apply-review")
    if args.apply_review:
        if existing["source_bytes"] != source.stat().st_size:
            raise ProcessingError("source changed since blur review; rerun with --force")
        cuts = approved_cuts(folder / "review.csv")
        if not cuts:
            log(f"{source.name}: no approved blur cuts")
            return
        if dv and not args.dv_approved:
            raise ProcessingError("Dolby Vision cuts need --dv-approved after proof playback review")
        if dv and not (folder / "dv-proof.mov").exists():
            raise ProcessingError("Dolby Vision proof is missing; run preprocess first")
        voice = folder / "enhanced-voice.wav"
        if not voice.exists():
            raise ProcessingError("enhanced voice WAV is missing; rerun with --force")
        with tempfile.TemporaryDirectory(prefix="vlog-", dir=folder) as scratch:
            work = Path(scratch)
            target = folder / ("cut.mov" if dv or source.suffix.lower() == ".mov" else "cut.mp4")
            rendered = safe_render(source, voice, video, work, target, cuts)
        existing["approved_cuts"] = cuts
        existing["cut_output"] = target.name
        existing["cut_validation"] = rendered
        existing["status"] = "dv_playback_review_required" if dv else "ready"
        write_report(folder, existing)
        log(f"{source.name}: approved cuts -> {target.name}")
        return

    with tempfile.TemporaryDirectory(prefix="vlog-", dir=folder) as scratch:
        work = Path(scratch)
        if audio:
            voice = enhance_audio(source, audio, work, report, args.denoise)
        else:
            voice = silent_audio(duration, work / "silent.wav")
            report["audio"] = {"status": "no source audio; silent stereo track added"}
        voice_export = folder / "enhanced-voice.wav"
        shutil.copyfile(voice, voice_export)
        write_review(source, video, duration, folder, report)
        if dv:
            fallback = folder / "voice-only.mov"
            if voice_only_copy(source, voice_export, video, fallback):
                report["voice_only_output"] = fallback.name
            else:
                report["voice_only_output"] = None
                report["note"] = "The untouched original and enhanced-voice.wav remain available."
            if shutil.which("dovi_tool"):
                proof = folder / "dv-proof.mov"
                try:
                    report["dv_proof_validation"] = safe_render(
                        source, voice_export, video, work, proof, [], proof_seconds=3.0)
                    report["dv_proof_output"] = proof.name
                except ProcessingError as exc:
                    proof.unlink(missing_ok=True)
                    report["dv_proof_error"] = str(exc)
            else:
                report["dv_proof_error"] = "dovi_tool is unavailable"
            report["status"] = "dv_original_video_retained"
        else:
            target = folder / ("processed.mov" if source.suffix.lower() == ".mov" else "processed.mp4")
            report["render_validation"] = safe_render(
                source, voice_export, video, work, target, [])
            report["processed_output"] = target.name
            report["status"] = "ready"
    write_report(folder, report)
    log(f"{source.name}: {report['status']} ({report['blur']['candidates']} blur candidates)")


def run(cfg: dict, args, log) -> int:
    args.cfg = cfg
    try:
        if args.draft and not args.path:
            if Path(args.draft).name != args.draft:
                raise ProcessingError("pass a draft folder name with --draft")
            slug, _ = select_channels(cfg, args.channel)[0]
            draft = channel_root(cfg, slug) / "drafts" / args.draft
            if not draft.is_dir():
                raise ProcessingError(f"draft not found: {draft}")
            # Detect inserted footage before choosing a clip or launching an
            # expensive batch, so numbered filenames always reflect capture time.
            ordering.ensure_current(draft, log, utc_offset=args.utc_offset)
        sources, output_root = source_files(args)
    except (ProcessingError, ordering.OrderError, OSError, ValueError) as exc:
        log(f"preprocess: {exc}")
        return 1
    output_root.mkdir(parents=True, exist_ok=True)
    failed = 0
    for source in sources:
        try:
            process_clip(source, output_root, args, log)
        except (ProcessingError, ordering.OrderError, OSError, ValueError) as exc:
            failed += 1
            log(f"{source.name}: {exc}")
    log(f"preprocess: {len(sources) - failed} ready, {failed} failed; output {output_root}")
    return 1 if failed else 0
