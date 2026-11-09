#!/usr/bin/env python3
"""Compose a reviewed SDR intro, HLG edit, ASS cues, and alpha CTA once."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT_FIELDS = {"schema_version", "revision", "plan", "source", "intro", "cues",
               "sidecar", "stock", "intro_seconds", "stock_start", "stock_duration",
               "video", "audio_policy"}
VIDEO_FIELDS = {"width", "height", "fps", "codec", "color"}
ASSET_FIELDS = {"path", "sha256"}
# Convert the intro through linear RGB so its SDR colors survive the HLG transfer.
INTRO_HLG = ("zscale=rangein=full:matrixin=bt470bg:transferin=bt709:"
             "primariesin=bt709:matrix=gbr:transfer=linear:primaries=bt709,"
             "format=gbrpf32le,"
             "zscale=matrixin=gbr:transferin=linear:primariesin=bt709:"
             "matrix=bt2020nc:transfer=arib-std-b67:primaries=bt2020:"
             "range=limited,format=p010le")
HLG_FLAGS = ["-pix_fmt", "p010le", "-color_primaries", "bt2020",
             "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc"]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def probe(path: Path) -> dict:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration:stream=codec_type,codec_name,width,height,"
                             "pix_fmt,avg_frame_rate,color_range,color_primaries,color_transfer,"
                             "color_space,sample_rate,channels,nb_frames", "-of", "json",
                             str(path)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def streams(meta: dict) -> tuple[dict, dict]:
    video = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in meta.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not video or not audio:
        raise ValueError("Every picture input needs video and audio")
    return video, audio


def asset(data: dict, key: str) -> Path:
    entry = data[key]
    if not isinstance(entry, dict) or set(entry) != ASSET_FIELDS:
        raise ValueError(f"{key} must have only path and sha256")
    path = Path(entry["path"]).resolve()
    if not path.is_file() or digest(path) != entry["sha256"]:
        raise ValueError(f"{key} is missing or has changed: {path}")
    return path


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if set(data) != ROOT_FIELDS or data.get("schema_version") != 1 or data.get("revision") != 1:
        raise ValueError("Unsupported manifest fields or revision")
    if set(data["video"]) != VIDEO_FIELDS or data["video"] != {
        "width": 3840, "height": 2160, "fps": 30, "codec": "hevc-main10", "color": "bt2020-hlg"}:
        raise ValueError("This composer supports only 3840x2160/30 HEVC Main10 HLG")
    if data["audio_policy"] != "concat-original":
        raise ValueError("Unsupported audio policy")
    if (float(data["intro_seconds"]) != 5.0 or float(data["stock_duration"]) != 5.0
            or float(data["stock_start"]) < 0):
        raise ValueError("This revision requires a 5-second intro and CTA")
    for key in ("plan", "source", "intro", "cues", "sidecar", "stock"):
        asset(data, key)
    plan = Path(data["plan"]["path"])
    approval = plan.parent / "approval.json"
    if not approval.is_file() or json.loads(approval.read_text(encoding="utf-8")).get("plan_sha256") != data["plan"]["sha256"]:
        raise ValueError("The reviewed preflight plan is not approved")
    source_video, source_audio = streams(probe(Path(data["source"]["path"])))
    intro_video, intro_audio = streams(probe(Path(data["intro"]["path"])))
    stock_video = next((s for s in probe(Path(data["stock"]["path"]))["streams"]
                        if s.get("codec_type") == "video"), None)
    if not stock_video:
        raise ValueError("CTA stock has no video")
    for name, v in (("source", source_video), ("intro", intro_video), ("stock", stock_video)):
        if (v.get("width"), v.get("height"), v.get("avg_frame_rate")) != (3840, 2160, "30/1"):
            raise ValueError(f"{name} is not UHD 30 fps")
    if (source_video.get("color_transfer") != "arib-std-b67" or
            source_video.get("color_primaries") != "bt2020" or
            source_video.get("color_space") != "bt2020nc" or
            "10" not in source_video.get("pix_fmt", "")):
        raise ValueError("Source is not 10-bit BT.2020 HLG")
    if (intro_video.get("color_space") != "bt470bg" or
            intro_video.get("color_range") != "pc" or
            intro_video.get("color_transfer") in {"arib-std-b67", "smpte2084"}):
        raise ValueError("Intro needs full-range SDR bt470bg matrix for this conversion")
    if "a" not in stock_video.get("pix_fmt", ""):
        raise ValueError("CTA stock lost its alpha channel")
    if source_audio.get("sample_rate") != "48000" or intro_audio.get("sample_rate") != "48000":
        raise ValueError("Both audio inputs need 48 kHz sound")
    duration = float(probe(Path(data["source"]["path"]))["format"]["duration"])
    if float(data["stock_start"]) + 5.0 > duration + 0.02:
        raise ValueError("CTA extends past source video")
    # A generated sidecar must match the approved cue data, preventing a stale overlay.
    import overlay
    cues = json.loads(Path(data["cues"]["path"]).read_text(encoding="utf-8"))
    if Path(data["sidecar"]["path"]).read_text(encoding="utf-8") != overlay.ass(cues, canvas=(1920, 1080)):
        raise ValueError("ASS sidecar differs from cue sheet")
    return data


def fingerprint(manifest: Path) -> str:
    # Code changes invalidate a visual approval as surely as cue or asset changes.
    value = hashlib.sha256(manifest.read_bytes() + Path(__file__).read_bytes())
    return value.hexdigest()


def encode_args(output: Path) -> list[str]:
    return ["-c:v", "hevc_nvenc", "-profile:v", "main10", "-preset", "p5",
            "-rc", "vbr", "-cq", "18", "-b:v", "0", *HLG_FLAGS,
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", str(output)]


def final_command(data: dict, output: Path) -> tuple[list[str], Path]:
    intro, source, stock = (Path(data[key]["path"]) for key in ("intro", "source", "stock"))
    sidecar = Path(data["sidecar"]["path"])
    at = float(data["stock_start"])
    graph = (f"[0:v]{INTRO_HLG},trim=duration=5,setpts=PTS-STARTPTS[iv];"
             f"[1:v]ass={sidecar.name},format=p010le[main];"
             f"[2:v]format=yuva444p10le,setpts=PTS-STARTPTS+{at}/TB[cta];"
             "[main][cta]overlay=shortest=0:eof_action=pass:repeatlast=0:format=auto,format=p010le[mv];"
             "[iv][mv]concat=n=2:v=1:a=0[v];"
             "[0:a]aresample=48000,atrim=duration=5,apad=whole_dur=5,atrim=duration=5,asetpts=PTS-STARTPTS[ia];"
             "[1:a]aresample=48000,asetpts=PTS-STARTPTS[ma];"
             "[ia][ma]concat=n=2:v=0:a=1[a]")
    return (["ffmpeg", "-nostdin", "-v", "warning", "-nostats", "-i", str(intro),
             "-i", str(source), "-i", str(stock), "-filter_complex", graph,
             "-map", "[v]", "-map", "[a]", *encode_args(output)], sidecar.parent)


def run(command: list[str], cwd: Path, log: Path) -> None:
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
        useful = [line for line in lines if not line.startswith("frame=")]
        raise RuntimeError("FFmpeg failed:\n" + "\n".join(useful[-12:]))


def preview(data: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    source, intro, stock = (Path(data[key]["path"]) for key in ("source", "intro", "stock"))
    sidecar = Path(data["sidecar"]["path"])
    made: list[Path] = []
    # The intro seam includes all 150 intro frames and the first three source seconds.
    seam = out_dir / "intro-seam.mp4"
    graph = (f"[0:v]{INTRO_HLG},trim=duration=5,setpts=PTS-STARTPTS[iv];"
             f"[1:v]ass={sidecar.name},trim=duration=3,setpts=PTS-STARTPTS,format=p010le[mv];"
             "[iv][mv]concat=n=2:v=1:a=0[v];"
             "[0:a]aresample=48000,atrim=duration=5,apad=whole_dur=5,atrim=duration=5,asetpts=PTS-STARTPTS[ia];"
             "[1:a]aresample=48000,atrim=duration=3,asetpts=PTS-STARTPTS[ma];"
             "[ia][ma]concat=n=2:v=0:a=1[a]")
    command = ["ffmpeg", "-nostdin", "-v", "warning", "-nostats", "-y", "-i", str(intro),
               "-i", str(source), "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
               *encode_args(seam)]
    run(command, sidecar.parent, out_dir / "intro-seam.log")
    made.append(seam)
    for label, start, length in (("ingredients", 20.0, 5.0), ("closing-cta", 480.0, 9.0)):
        output = out_dir / f"{label}.mp4"
        args = ["ffmpeg", "-nostdin", "-v", "warning", "-nostats", "-y", "-ss", str(start),
                "-i", str(source)]
        if label == "closing-cta":
            args += ["-itsoffset", str(float(data["stock_start"]) - start), "-i", str(stock)]
            # Restore source-global timestamps for ASS, then reset them for the preview.
            graph = (f"[0:v]setpts=PTS-STARTPTS+{start}/TB,ass={sidecar.name},"
                     "setpts=PTS-STARTPTS,format=p010le[base];"
                     "[1:v]format=yuva444p10le[cta];"
                     "[base][cta]overlay=shortest=0:eof_action=pass:repeatlast=0:format=auto,format=p010le[v]")
            args += ["-filter_complex", graph, "-map", "[v]", "-map", "0:a:0"]
        else:
            args += ["-vf", f"setpts=PTS-STARTPTS+{start}/TB,ass={sidecar.name},"
                     "setpts=PTS-STARTPTS,format=p010le", "-map", "0:v:0", "-map", "0:a:0"]
        args += ["-t", str(length), *encode_args(output)]
        run(args, sidecar.parent, out_dir / f"{label}.log")
        made.append(output)
    return made


def verify(data: dict, video: Path, evidence_dir: Path) -> dict:
    meta = probe(video)
    picture, sound = streams(meta)
    expected = 5.0 + float(probe(Path(data["source"]["path"]))["format"]["duration"])
    actual = float(meta["format"]["duration"])
    if abs(actual - expected) > 0.12:
        raise ValueError(f"Output duration {actual:.3f} differs from {expected:.3f}")
    if (picture.get("codec_name"), picture.get("width"), picture.get("height"),
        picture.get("avg_frame_rate"), picture.get("color_primaries"),
        picture.get("color_transfer"), picture.get("color_space")) != (
            "hevc", 3840, 2160, "30/1", "bt2020", "arib-std-b67", "bt2020nc"):
        raise ValueError("Output geometry, frame rate, or HLG tags mismatch")
    if ("10" not in picture.get("pix_fmt", "") or sound.get("sample_rate") != "48000"
            or sound.get("channels") != 2):
        raise ValueError("Output is not 10-bit with 48 kHz stereo audio")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, second in (("intro", 2), ("first-main", 6), ("ingredients", 27),
                         ("cta", 489), ("closing", 500)):
        frame = evidence_dir / f"{name}.jpg"
        result = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(second),
                                 "-i", str(video), "-frames:v", "1", "-vf", "scale=960:-1",
                                 "-y", str(frame)], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f"Could not sample {name}: {result.stderr[-500:]}")
    report = {"video": str(video), "sha256": digest(video), "duration": actual,
              "width": picture["width"], "height": picture["height"],
              "pixel_format": picture["pix_fmt"], "color": "bt2020-hlg",
              "audio_sample_rate": sound["sample_rate"],
              "human_review": "pending: inspect full output and affected picture/audio"}
    (evidence_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "fingerprint", "preview", "render", "verify"])
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    data = load(args.manifest)
    if args.command == "validate":
        print("Valid HLG composition manifest")
    elif args.command == "fingerprint":
        print(fingerprint(args.manifest))
    elif args.command == "preview":
        if not args.out_dir:
            parser.error("preview requires --out-dir")
        print("Rendered previews: " + ", ".join(str(p) for p in preview(data, args.out_dir)))
    elif args.command == "render":
        if not args.approval or not args.output:
            parser.error("render requires --approval and --output")
        if args.output.exists():
            raise ValueError("Final output already exists")
        approval = json.loads(args.approval.read_text(encoding="utf-8"))
        if (approval.get("actor") != "human" or not approval.get("review_note") or
                approval.get("fingerprint") != fingerprint(args.manifest)):
            raise ValueError("Exact manifest human approval is missing or stale")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        partial = args.output.with_name(args.output.stem + ".partial.mp4")
        if partial.exists():
            raise ValueError("Partial output already exists")
        command, cwd = final_command(data, partial)
        try:
            run(command, cwd, args.output.with_suffix(".render.log"))
            os.replace(partial, args.output)
        except Exception:
            partial.unlink(missing_ok=True)
            raise
        print(f"Rendered HLG-base master: {args.output}")
    else:
        if not args.video or not args.evidence_dir:
            parser.error("verify requires --video and --evidence-dir")
        report = verify(data, args.video, args.evidence_dir)
        print(f"Verified {report['duration']:.2f}s UHD HLG video; human review remains pending")


if __name__ == "__main__":
    main()
