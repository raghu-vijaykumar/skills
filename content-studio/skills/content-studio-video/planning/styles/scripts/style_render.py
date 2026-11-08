#!/usr/bin/env python3
"""Apply approved style profile to an exported SDR master (non-destructive)."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

BUNDLE_ROOT = next(parent for parent in Path(__file__).resolve().parents if parent.name == "content-studio")
sys.path.insert(0, str(BUNDLE_ROOT / "skills" / "content-studio-video" / "edit" / "clip-edit" / "scripts"))

from filters import PRESETS, ensure_sdr, look_graph  # noqa: E402
from style_consistency import profile_for  # noqa: E402

def build_look(profile, duration):
    return [{"start": 0, "end": duration, "preset": profile["look"], "fade": 0}]

def duration_of(source):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(source)],
                       check=True, capture_output=True, text=True)
    return float(p.stdout.strip())

def render(source, target, profile, captions=None, apply_audio=False):
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target or not source.is_file() or target.exists():
        raise ValueError("Input must exist; output must be a new path")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe required")
    ensure_sdr(source)
    if profile["look"] not in PRESETS:
        raise ValueError("Unsupported built-in look in profile")
    duration = duration_of(source)
    vf = look_graph(build_look(profile, duration), PRESETS)
    if captions:
        cap = Path(captions).resolve()
        if not cap.is_file() or cap.suffix.lower() not in (".srt", ".ass"):
            raise ValueError("Captions must be an existing SRT or ASS file")
        # libass subtitles filter accepts escaped path; render uses FFmpeg fonts.
        path = cap.as_posix().replace(":", "\\:").replace("'", "\\'")
        margin = int(profile["safe_margin_percent"] * 10)
        position = 8 if profile["caption_position"] == "top" else 2
        vf += f";[vout]subtitles=filename='{path}':force_style='FontName={profile['font_family']},Alignment={position},MarginV={margin}'[styled]"
        video = "[styled]"
    else:
        video = "[vout]"
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-n", "-i", str(source),
           "-filter_complex", vf, "-map", video, "-map", "0:a?"]
    if apply_audio:
        cmd += ["-af", f"loudnorm=I={profile['audio_target_lufs']}:TP=-1.5:LRA=11",
                "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-c:a", "copy"]
    cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target)]
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True)
    return target

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--profile", choices=["travel-vlog", "daily-vlog", "technical-explainer"], required=True)
    p.add_argument("--overrides", type=Path)
    p.add_argument("--captions", type=Path)
    p.add_argument("--master-audio", action="store_true", help="One-pass loudnorm, requires human listening review")
    args = p.parse_args()
    overrides = json.loads(args.overrides.read_text(encoding="utf-8")) if args.overrides else None
    profile = profile_for(args.profile, overrides)
    render(args.input, args.output, profile, args.captions, args.master_audio)

if __name__ == "__main__":
    main()
