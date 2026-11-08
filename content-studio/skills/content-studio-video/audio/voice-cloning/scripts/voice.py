#!/usr/bin/env python3
"""Consented voice enrollment and local IndicF5 narration synthesis."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import narration  # noqa: E402

SAMPLE_RATE = 24000


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path):
    p = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate,channels:format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if p.returncode or not p.stdout.strip():
        raise ValueError("Cannot decode audio: " + str(path))
    data = json.loads(p.stdout)
    if not data.get("streams"):
        raise ValueError("No audio stream: " + str(path))
    return float(data.get("format", {}).get("duration", 0))


def media_duration(path):
    p = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if p.returncode or not p.stdout.strip():
        raise SystemExit("Cannot read media duration: " + str(path))
    return float(p.stdout.strip())


BUNDLED_PROFILES = Path(__file__).resolve().parents[1] / "profiles"


def local_profile_dir(workspace, profile):
    return (
        Path(workspace).expanduser().resolve()
        / ".content-studio"
        / "voice"
        / "profiles"
        / profile
    )


def profile_dir(workspace, profile):
    """Prefer a workspace profile, then fall back to a bundled profile."""
    local = local_profile_dir(workspace, profile)
    if local.exists():
        return local
    bundled = BUNDLED_PROFILES / profile
    if bundled.exists():
        return bundled
    return local


def require_consent(profile_root):
    manifest = profile_root / "profile.json"
    if not manifest.is_file():
        raise SystemExit("No enrolled voice profile: " + str(manifest))
    data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    if not data.get("consent", {}).get("affirmed"):
        raise SystemExit("Profile has no affirmed consent; refusing to clone")
    missing = [
        sample["file"]
        for sample in data.get("samples", [])
        if not (profile_root / sample["file"]).is_file()
    ]
    if missing:
        raise SystemExit("Profile samples are missing: " + ", ".join(missing))
    return data


def _fail(message):
    raise SystemExit(message)


def cmd_synthesize(workspace, args):
    voice_root = Path(workspace).expanduser().resolve() / ".content-studio" / "voice"
    require_consent(profile_dir(workspace, args.profile))

    script_path = Path(args.script).expanduser().resolve()
    if not script_path.is_file():
        _fail("Narration script not found: " + str(script_path))
    segments = narration.validate_script(narration.load_json(script_path))
    if args.only:
        wanted = {item.strip() for item in args.only.split(",") if item.strip()}
        unknown = wanted - {segment["id"] for segment in segments}
        if unknown:
            _fail("Unknown segment ids: " + ", ".join(sorted(unknown)))
        segments = [segment for segment in segments if segment["id"] in wanted]

    reference = Path(args.reference).expanduser().resolve()
    if not reference.is_file():
        _fail("Reference audio not found: " + str(reference))
    if not args.reference_text.strip():
        _fail("--reference-text must match the reference clip exactly")

    params = {
        "backend": "indicf5",
        "nfe_step": args.nfe_step,
        "cfg_strength": args.cfg_strength,
        "speed": args.speed,
        "seed_base": 20261107,
        "reference_sha256": narration.sha256_file(reference),
    }
    narration_root = voice_root / "narration"
    segments_dir = narration_root / "segments"
    manifest_path = narration_root / "manifest.json"
    manifest = (
        narration.load_json(manifest_path)
        if manifest_path.is_file()
        else {"schema_version": 1, "segments": {}}
    )
    manifest.setdefault("segments", {})
    manifest["params"] = params

    if args.dry_run:
        plan = []
        for segment in segments:
            audio_path = segments_dir / f"{segment['id']}.wav"
            plan.append(
                {
                    "id": segment["id"],
                    "reuse": narration.is_reusable(
                        manifest["segments"].get(segment["id"]),
                        segment["text"],
                        params,
                        audio_path,
                    ),
                    "audio": str(audio_path),
                }
            )
        print(json.dumps({"params": params, "segments": plan}, indent=2))
        return

    import indicf5_backend

    indicf5_backend.keep_system_awake()
    print("Loading IndicF5...", flush=True)
    model, vocoder = indicf5_backend.load_backend(
        Path(args.model_dir),
        device=args.device,
        allow_partial_weights=args.allow_partial_weights,
    )
    reference_audio, reference_text = indicf5_backend.prepare_reference(
        reference, args.reference_text
    )
    segments_dir.mkdir(parents=True, exist_ok=True)

    failures = []
    for index, segment in enumerate(segments, start=1):
        segment_id = segment["id"]
        audio_path = segments_dir / f"{segment_id}.wav"
        if (
            narration.is_reusable(
                manifest["segments"].get(segment_id),
                segment["text"],
                params,
                audio_path,
            )
            and not args.force
        ):
            print(
                f"[{index}/{len(segments)}] {segment_id} reuse "
                f"{manifest['segments'][segment_id]['seconds']}s",
                flush=True,
            )
            continue
        started = time.time()
        print(
            f"[{index}/{len(segments)}] {segment_id} chars={len(segment['text'])}",
            flush=True,
        )
        try:
            import numpy as np
            import soundfile as sf
            import torch

            audio, sample_rate = indicf5_backend.synthesize(
                model,
                vocoder,
                reference_audio,
                reference_text,
                segment["text"],
                nfe_step=args.nfe_step,
                cfg_strength=args.cfg_strength,
                speed=args.speed,
                device=args.device,
                seed=params["seed_base"] + index,
            )
            peak = float(np.max(np.abs(audio))) if audio.size else 0.0
            if peak > 0.99:
                audio = audio / peak * 0.99
            sf.write(str(audio_path), audio, sample_rate, subtype="PCM_16")
            manifest["segments"][segment_id] = {
                "text_hash": narration.sha256_text(segment["text"]),
                "params": params,
                "seconds": round(len(audio) / sample_rate, 3),
                "sample_rate": sample_rate,
                "slot": [segment["start"], segment["end"]],
                "render_seconds": round(time.time() - started, 1),
                "rendered_at": datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat(),
            }
            narration.write_json(manifest_path, manifest)
            print(
                f"[{index}/{len(segments)}] {segment_id} done "
                f"{manifest['segments'][segment_id]['seconds']}s",
                flush=True,
            )
        except Exception as error:  # keep going so one bad section is not fatal
            failures.append({"id": segment_id, "error": repr(error)})
            print(f"[{index}/{len(segments)}] {segment_id} FAILED {error!r}", flush=True)
            narration.write_json(manifest_path, manifest)
        finally:
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

    narration.write_json(manifest_path, manifest)
    print(json.dumps({"failures": failures}, ensure_ascii=False), flush=True)
    if failures:
        raise SystemExit(1)


def _run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            "Command failed: " + " ".join(command) + "\n" + result.stderr[-3000:]
        )


def cmd_assemble(workspace, args):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        _fail("FFmpeg and FFprobe are required")

    voice_root = Path(workspace).expanduser().resolve() / ".content-studio" / "voice"
    narration_root = voice_root / "narration"
    segments_dir = narration_root / "segments"
    manifest_path = narration_root / "manifest.json"
    if not manifest_path.is_file():
        _fail("No narration manifest; run synthesize first")
    manifest = narration.load_json(manifest_path)

    script_path = Path(args.script).expanduser().resolve()
    if not script_path.is_file():
        _fail("Narration script not found: " + str(script_path))
    segments = narration.validate_script(narration.load_json(script_path))

    missing = [
        segment["id"]
        for segment in segments
        if segment["id"] not in manifest["segments"]
        or not (segments_dir / f"{segment['id']}.wav").is_file()
    ]
    if missing:
        _fail("Missing rendered segments: " + ", ".join(missing))

    video = Path(args.video).expanduser().resolve()
    if not video.is_file():
        _fail("Video not found: " + str(video))
    video_seconds = media_duration(video)
    durations = {
        segment["id"]: float(manifest["segments"][segment["id"]]["seconds"])
        for segment in segments
    }
    placed = narration.fit_timeline(
        segments,
        durations,
        video_seconds,
        max_tempo=args.max_tempo,
        gap=args.gap,
    )
    summary = narration.timeline_summary(placed, video_seconds)

    mix_seconds = summary["mix_seconds"]
    inputs = [
        "-f",
        "lavfi",
        "-t",
        f"{mix_seconds:.3f}",
        "-i",
        "anullsrc=r=24000:cl=mono",
    ]
    filters = [f"[0:a]atrim=0:{mix_seconds:.3f},asetpts=PTS-STARTPTS[base]"]
    labels = ["[base]"]
    for index, item in enumerate(placed, start=1):
        source = segments_dir / f"{item['id']}.wav"
        inputs.extend(["-i", str(source)])
        chain = [f"[{index}:a]"]
        if abs(item["tempo"] - 1.0) > 1e-4:
            chain.append(f"atempo={item['tempo']:.6f},")
        delay = int(round(item["start"] * 1000))
        if delay > 0:
            chain.append(f"adelay={delay},")
        chain.append(f"aresample={SAMPLE_RATE},aformat=channel_layouts=mono[a{index}]")
        filters.append("".join(chain))
        labels.append(f"[a{index}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,"
        + "alimiter=limit=0.95[out]"
    )
    mix_24k = narration_root / "narration-24k.wav"
    _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[out]",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(mix_24k),
        ]
    )

    output = narration_root / "narration.wav"
    _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(mix_24k),
            "-af",
            f"loudnorm=I={args.lufs}:TP=-1.5:LRA=11,aresample=48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            str(output),
        ]
    )

    report = {"schema_version": 1, **summary, "segments": placed}
    narration.write_json(narration_root / "timeline.json", report)
    print(json.dumps(summary, ensure_ascii=False), flush=True)

    if args.preview:
        extra = max(0.0, summary["mix_seconds"] - video_seconds)
        filters = [f"scale=-2:{args.preview_height}"]
        if extra > 0.05:
            filters.append(f"tpad=stop_mode=clone:stop_duration={extra:.3f}")
        preview = narration_root / "preview.mp4"
        _run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(video),
                "-i",
                str(output),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-vf",
                ",".join(filters),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "21",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-t",
                f"{summary['mix_seconds']:.3f}",
                "-movflags",
                "+faststart",
                str(preview),
            ]
        )
        print(json.dumps({"preview": str(preview)}), flush=True)


def main():
    ap = argparse.ArgumentParser(
        description="Bootstrap a consented local voice profile and synthesize narration"
    )
    ap.add_argument("--workspace", required=True)
    sub = ap.add_subparsers(dest="action", required=True)

    init = sub.add_parser("enroll")
    init.add_argument("--samples", nargs="+", required=True)
    init.add_argument("--profile", default="my-voice")
    init.add_argument("--language", default="kn-en")
    init.add_argument(
        "--consent",
        action="store_true",
        help="I own this voice or have explicit permission to clone it",
    )
    init.add_argument("--consent-note", required=True)

    status = sub.add_parser("status")
    status.add_argument("--profile", default="my-voice")

    synth = sub.add_parser("synthesize")
    synth.add_argument("--profile", default="my-voice")
    synth.add_argument("--script", required=True)
    synth.add_argument("--model-dir", required=True)
    synth.add_argument("--reference", required=True)
    synth.add_argument("--reference-text", required=True)
    synth.add_argument("--nfe-step", type=int, default=32)
    synth.add_argument("--cfg-strength", type=float, default=2.0)
    synth.add_argument("--speed", type=float, default=1.0)
    synth.add_argument("--device", default="cuda")
    synth.add_argument("--only", default="")
    synth.add_argument("--force", action="store_true")
    synth.add_argument("--allow-partial-weights", action="store_true")
    synth.add_argument("--dry-run", action="store_true")

    assemble = sub.add_parser("assemble")
    assemble.add_argument("--script", required=True)
    assemble.add_argument("--video", required=True)
    assemble.add_argument("--max-tempo", type=float, default=1.12)
    assemble.add_argument("--gap", type=float, default=0.3)
    assemble.add_argument("--lufs", type=float, default=-16.0)
    assemble.add_argument("--preview", action="store_true")
    assemble.add_argument("--preview-height", type=int, default=1080)

    args = ap.parse_args()
    root = local_profile_dir(args.workspace, getattr(args, "profile", "my-voice"))

    if args.action == "status":
        root = profile_dir(args.workspace, args.profile)
        manifest = root / "profile.json"
        if not manifest.exists():
            raise SystemExit("No enrolled voice profile")
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        missing = [
            sample["file"]
            for sample in data["samples"]
            if not (root / sample["file"]).exists()
        ]
        print(
            json.dumps(
                {
                    "profile": args.profile,
                    "path": str(root),
                    "samples": len(data["samples"]),
                    "duration_seconds": data["total_duration_seconds"],
                    "consent": data["consent"],
                    "missing_samples": missing,
                    "synthesis_ready": bool(
                        data.get("consent", {}).get("affirmed")
                    ),
                },
                indent=2,
            )
        )
        return

    if args.action == "synthesize":
        cmd_synthesize(args.workspace, args)
        return

    if args.action == "assemble":
        cmd_assemble(args.workspace, args)
        return

    if not args.consent:
        raise SystemExit("Explicit --consent is required")
    if not args.consent_note.strip():
        raise SystemExit("Consent note must not be empty")
    if (root / "profile.json").exists():
        raise SystemExit("Profile exists; use another name (no implicit overwrite)")
    samples = [Path(s).expanduser().resolve() for s in args.samples]
    if not all(s.is_file() for s in samples):
        raise SystemExit("One or more samples do not exist")
    durations = [probe(s) for s in samples]
    if any(d < 3 for d in durations):
        raise SystemExit("Each sample must contain at least 3 seconds of audio")
    if sum(durations) < 20:
        raise SystemExit("Provide at least 20 seconds of total speech samples")
    root.mkdir(parents=True, exist_ok=True)
    records = []
    try:
        for i, (src, duration) in enumerate(zip(samples, durations)):
            dest = root / f"sample-{i:03d}.wav"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostdin",
                    "-n",
                    "-i",
                    str(src),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    str(SAMPLE_RATE),
                    "-c:a",
                    "pcm_s16le",
                    str(dest),
                ],
                check=True,
            )
            records.append(
                {
                    "file": dest.name,
                    "sha256": sha(dest),
                    "duration_seconds": round(duration, 2),
                    "source_name": src.name,
                }
            )
        data = {
            "schema_version": 1,
            "name": args.profile,
            "language": args.language,
            "samples": records,
            "total_duration_seconds": round(sum(durations), 2),
            "consent": {
                "affirmed": True,
                "note": args.consent_note,
                "recorded_at": datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat(),
            },
            "backend": {
                "name": "IndicF5",
                "configured": False,
                "defaults": {
                    "nfe_step": 32,
                    "cfg_strength": 2.0,
                    "speed": 1.0,
                },
            },
            "synthesis_ready": True,
        }
        narration.write_json(root / "profile.json", data)
    except Exception:
        for record in records:
            (root / record["file"]).unlink(missing_ok=True)
        raise
    print("Enrolled locally:", root / "profile.json")
    print("Synthesize with: voice.py --workspace <draft> synthesize --profile", args.profile)


if __name__ == "__main__":
    main()
