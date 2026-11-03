#!/usr/bin/env python3
"""Batch spoken-word audio mastering with FFmpeg; never changes source files."""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXTS = {".mp4", ".mov", ".mkv", ".m4v", ".webm", ".avi"}
FILTER = "highpass=f=80,afftdn=nf=-28,acompressor=threshold=0.12:ratio=2:attack=15:release=180"

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

def master(source, dest, force):
    streams = probe(source)
    if not any(s["codec_type"] == "audio" for s in streams):
        return {"source": str(source), "status": "skipped_no_audio"}
    wav = dest / (source.stem + ".mastered.wav")
    video = dest / (source.stem + ".mastered.mp4")
    if not force and (wav.exists() or video.exists()):
        return {"source": str(source), "status": "skipped_output_exists"}
    m = measure(source, FILTER)
    second = (f"{FILTER},loudnorm=I=-16:LRA=11:TP=-1.5:"
              f"measured_I={m['input_i']}:measured_LRA={m['input_lra']}:"
              f"measured_TP={m['input_tp']}:measured_thresh={m['input_thresh']}:"
              f"offset={m['target_offset']}:linear=true")
    wav_tmp = dest / (source.stem + ".mastered.tmp.wav")
    video_tmp = dest / (source.stem + ".mastered.tmp.mp4")
    try:
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
             "-map", "0:a:0", "-vn", "-af", second, "-ar", "48000", "-ac", "2",
             "-c:a", "pcm_s24le", str(wav_tmp)])
        # Re-encode video only if source codec is incompatible with MP4 stream-copy.
        codec = next((s.get("codec_name") for s in streams if s["codec_type"] == "video"), None)
        video_codec = "copy" if codec in {"h264", "hevc", "av1", "mpeg4"} else "libx264"
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
             "-i", str(wav_tmp), "-map", "0:v:0", "-map", "1:a:0",
             "-c:v", video_codec, "-c:a", "aac", "-b:a", "192k",
             "-map_metadata", "0", "-movflags", "+faststart", "-shortest", str(video_tmp)])
        wav_tmp.replace(wav)
        video_tmp.replace(video)
        return {"source": str(source), "status": "ok", "audio": str(wav),
                "video": str(video), "input_loudness": m,
                "output_loudness": measure(wav, "")}
    finally:
        for tmp in (wav_tmp, video_tmp):
            if tmp.exists():
                tmp.unlink()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--folder", type=Path, required=True)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if not args.folder.is_dir():
        ap.error("--folder must be a directory")
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            ap.error(binary + " not found on PATH")
    dest = args.folder / "audio-mastered"
    dest.mkdir(exist_ok=True)
    results = []
    for source in sorted(args.folder.iterdir()):
        if not source.is_file() or source.suffix.lower() not in EXTS:
            continue
        try:
            result = master(source, dest, args.force)
        except Exception as exc:
            result = {"source": str(source), "status": "error", "error": str(exc)}
        results.append(result)
        print(result["status"], source.name, flush=True)
    (dest / "manifest.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 1 if any(r["status"] == "error" for r in results) else 0

if __name__ == "__main__":
    sys.exit(main())
