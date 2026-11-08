#!/usr/bin/env python3
"""Batch spoken-word audio mastering with FFmpeg; never changes source files."""
import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXTS = {".mp4", ".mov", ".mkv", ".m4v", ".webm", ".avi"}
TARGET_LUFS = -16.0
TARGET_PEAK = -1.5


def build_filter(cleanup=False, deess=False, gate=False, arnndn_model=None):
    if not any((cleanup, deess, gate, arnndn_model)):
        return ""
    parts = ["highpass=f=80"]
    if arnndn_model:
        escaped = str(Path(arnndn_model).expanduser().resolve()).replace("\\", "/").replace(":", "\\:")
        parts.append(f"arnndn=m='{escaped}'")
    elif cleanup:
        parts.append("afftdn=nf=-28")
    if cleanup:
        parts.append("acompressor=threshold=0.12:ratio=2:attack=15:release=180")
    if cleanup or deess:
        parts.append("deesser")
    if cleanup or gate:
        parts.append("agate=threshold=0.03:ratio=2:attack=10:release=200")
    return ",".join(parts)

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[-2500:])
    return p

def probe(path):
    p = run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)])
    return json.loads(p.stdout)["streams"]

def measure_filter(filters):
    return ",".join(part for part in
                    (filters, "loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json")
                    if part)

def measure(path, filters):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn",
           "-af", measure_filter(filters),
           "-f", "null", "-"]
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-2500:])
    matches = re.findall(r'\{\s*"input_i".*?\}', p.stderr, re.S)
    if not matches:
        raise RuntimeError("No loudness measurement returned")
    return json.loads(matches[-1])

def master(source, dest, force, audio_only=False, filters="", review_dir=None):
    streams = probe(source)
    if not any(s["codec_type"] == "audio" for s in streams):
        return {"source": str(source), "status": "skipped_no_audio"}
    wav = dest / (source.stem + ".mastered.wav")
    video = dest / (source.stem + ".mastered.mp4")
    if not force and ((wav.exists() and audio_only) or
                      (not audio_only and (wav.exists() or video.exists()))):
        return {"source": str(source), "status": "skipped_output_exists"}
    baseline = measure(source, "")
    has_loudness = math.isfinite(float(baseline["input_i"]))
    loudness_issue = has_loudness and abs(float(baseline["input_i"]) - TARGET_LUFS) > 1.0
    peak_issue = has_loudness and float(baseline["input_tp"]) > TARGET_PEAK
    needs_normalization = loudness_issue or peak_issue
    issues = (["loudness_outside_target"] if loudness_issue else []) + \
             (["peak_above_target"] if peak_issue else [])
    if not has_loudness:
        issues.append("silent_or_unmeasurable_audio")
    if filters and has_loudness:
        issues.append("cleanup_requested_requires_listening_review")
    wav_tmp = dest / (source.stem + ".mastered.tmp.wav")
    video_tmp = dest / (source.stem + ".mastered.tmp.mp4")
    try:
        attempts = []
        candidates = [filters] + ([""] if filters and has_loudness else [])
        for candidate_filters in candidates:
            wav_tmp.unlink(missing_ok=True)
            if needs_normalization or candidate_filters:
                m = measure(source, candidate_filters) if candidate_filters else baseline
                second = (f"{candidate_filters + ',' if candidate_filters else ''}"
                          f"loudnorm=I=-16:LRA=11:TP=-1.5:"
                          f"measured_I={m['input_i']}:measured_LRA={m['input_lra']}:"
                          f"measured_TP={m['input_tp']}:measured_thresh={m['input_thresh']}:"
                          f"offset={m['target_offset']}:linear=true")
            else:
                second = "anull"
            try:
                run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                     "-i", str(source), "-map", "0:a:0", "-vn", "-af", second,
                     "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le",
                     str(wav_tmp)])
                output_loudness = measure(wav_tmp, "")
            except RuntimeError as exc:
                attempts.append({"filters": candidate_filters, "status": "rejected",
                                 "reason": str(exc)})
                continue
            output_i = float(output_loudness["input_i"])
            output_tp = float(output_loudness["input_tp"])
            validation = {"status": "passed", "target_lufs": TARGET_LUFS,
                          "target_peak_dbtp": TARGET_PEAK,
                          "output_lufs": output_i if math.isfinite(output_i) else None,
                          "output_peak_dbtp": output_tp if math.isfinite(output_tp) else None}
            if needs_normalization and (
                    validation["output_lufs"] is None or
                    abs(validation["output_lufs"] - TARGET_LUFS) > 1.5 or
                    validation["output_peak_dbtp"] is None or
                    validation["output_peak_dbtp"] > -1.0):
                attempts.append({"filters": candidate_filters, "status": "rejected",
                                 "reason": "missed loudness/peak gate",
                                 "validation": validation})
                continue
            break
        else:
            raise RuntimeError("all mastering candidates failed: " +
                               json.dumps(attempts))
        if filters and has_loudness:
            validation["status"] = "review_required"
            validation["reason"] = ("cleanup candidate failed; loudness-only fallback"
                                    if not candidate_filters else
                                    "cleanup fidelity needs listening review")
        wav_tmp.replace(wav)
        result = {"source": str(source), "status": "ok", "audio": str(wav),
                  "decision": "REVIEW" if filters and has_loudness else "FIX" if needs_normalization else "SKIP",
                  "issues": issues, "requested_filters": filters,
                  "filters": candidate_filters, "rejected_candidates": attempts,
                  "input_loudness": baseline, "output_loudness": output_loudness,
                  "validation": validation}
        if review_dir is not None and (filters or needs_normalization):
            review_dir.mkdir(parents=True, exist_ok=True)
            before = review_dir / "before.wav"
            after = review_dir / "after.wav"
            for original, target in ((source, before), (wav, after)):
                run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                     "-i", str(original), "-vn", "-t", "10", "-ar", "48000",
                     "-ac", "2", "-c:a", "pcm_s16le", str(target)])
            result["review_audio"] = {"before": str(before), "after": str(after)}
        if not audio_only:
            # Re-encode video only if source codec is incompatible with MP4 stream-copy.
            codec = next((s.get("codec_name") for s in streams if s["codec_type"] == "video"), None)
            video_codec = "copy" if codec in {"h264", "hevc", "av1", "mpeg4"} else "libx264"
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
                 "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
                 "-c:v", video_codec, "-c:a", "aac", "-b:a", "192k",
                 "-map_metadata", "0", "-movflags", "+faststart", "-shortest", str(video_tmp)])
            video_tmp.replace(video)
            result["video"] = str(video)
        return result
    finally:
        for tmp in (wav_tmp, video_tmp):
            if tmp.exists():
                tmp.unlink()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--folder", type=Path, required=True)
    ap.add_argument("--out", type=Path, help="output folder (default: draft root for WAV, or <folder>/audio-mastered)")
    ap.add_argument("--audio-only", action="store_true", help="write mastered WAV only; no mastered MP4 (always on for drafts)")
    ap.add_argument("--cleanup", action="store_true",
                    help="add de-esser and noise gate for vlog dialogue")
    ap.add_argument("--deess", action="store_true", help="add de-essing")
    ap.add_argument("--gate", action="store_true", help="add a gentle noise gate")
    ap.add_argument("--arnndn-model", help="use RNNoise speech denoise model instead of afftdn")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if not args.folder.is_dir():
        ap.error("--folder must be a directory")
    folder = args.folder
    draft = None
    if (folder / "draft.json").exists() or (folder / ".content-studio").is_dir():
        draft = folder
        if (folder / "video").is_dir():
            folder = folder / "video"
    elif folder.name == "video" and ((folder.parent / "draft.json").exists()
                                     or (folder.parent / ".content-studio").is_dir()):
        draft = folder.parent
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            ap.error(binary + " not found on PATH")
    if args.out:
        dest = args.out
        manifest = dest / "manifest.json"
    elif draft is not None:
        dest = draft
        manifest = draft / ".content-studio" / "audio" / "manifest.json"
    else:
        dest = folder / "audio-mastered"
        manifest = dest / "manifest.json"
    dest.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    audio_only = args.audio_only or draft is not None
    filters = build_filter(cleanup=args.cleanup, deess=args.deess, gate=args.gate,
                           arnndn_model=args.arnndn_model)
    if draft is not None:
        candidates = [draft / f"{draft.name}-final.mp4", draft / "final-video.mp4",
                      draft / "video.mp4", draft / "video" / "with-audio.mp4"]
        sources = [next((path for path in candidates if path.is_file()), folder)]
    else:
        sources = sorted(folder.iterdir())
    results = []
    for source in sources:
        if not source.is_file() or source.suffix.lower() not in EXTS:
            continue
        try:
            result = master(source, dest, args.force, audio_only=audio_only,
                            filters=filters,
                            review_dir=manifest.parent / "previews" / source.stem)
            if draft is not None and result.get("status") == "ok":
                wav_path = Path(result["audio"])
                mp3 = draft / f"{draft.name}-audio-only.mp3"
                run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                     "-i", str(wav_path), "-vn", "-c:a", "libmp3lame", "-b:a", "192k",
                     str(mp3)])
                wav_path.unlink(missing_ok=True)
                result["audio"] = str(mp3)
        except Exception as exc:
            result = {"source": str(source), "status": "error", "error": str(exc)}
        results.append(result)
        print(result["status"], source.name, flush=True)
    manifest.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 1 if any(r["status"] == "error" for r in results) else 0

if __name__ == "__main__":
    sys.exit(main())
