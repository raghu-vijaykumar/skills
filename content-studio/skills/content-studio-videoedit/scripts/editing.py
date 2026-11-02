"""Frame-accurate vlog cuts and a normalized mixed-camera assembly."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from common import channel_root, select_channels
import ordering


class EditError(RuntimeError):
    pass


def command(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        lines = [line for line in result.stderr.splitlines() if line.strip()]
        raise EditError("FFmpeg failed: " + " | ".join(lines[-4:])[-600:])


def probe(path: Path) -> tuple[float, dict, bool]:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                             "-of", "json", str(path)], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise EditError(f"ffprobe failed for {path.name}: {result.stderr.strip()[-300:]}")
    info = json.loads(result.stdout)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise EditError(f"no video stream: {path}")
    duration = float(info.get("format", {}).get("duration") or video.get("duration") or 0)
    if duration <= 0:
        raise EditError(f"unknown video duration: {path}")
    has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    return duration, video, has_audio


def timestamp(value: str) -> float:
    if not re.fullmatch(r"\d+(?::\d{1,2}){0,2}(?:\.\d+)?", value or ""):
        raise EditError(f"invalid timestamp: {value!r}")
    result = 0.0
    for part in value.split(":"):
        result = result * 60 + float(part)
    return result


def cut_ranges(duration: float, specifications: list[str]) -> list[tuple[float, float]]:
    cuts = []
    for spec in specifications:
        if "-" not in spec:
            raise EditError("--remove must be START-END, e.g. 00:12-00:14.5")
        start_text, end_text = spec.split("-", 1)
        start, end = timestamp(start_text), timestamp(end_text)
        if start < 0 or end > duration + 0.05 or end <= start:
            raise EditError(f"cut is outside video duration ({duration:.3f}s): {spec}")
        cuts.append((start, min(end, duration)))
    cuts.sort()
    if any(b[0] < a[1] - 0.001 for a, b in zip(cuts, cuts[1:])):
        raise EditError("cut ranges overlap")
    keep, position = [], 0.0
    for start, end in cuts:
        if start - position > 0.001:
            keep.append((position, start))
        position = end
    if duration - position > 0.001:
        keep.append((position, duration))
    if not keep:
        raise EditError("cuts remove the entire video")
    return keep


def is_dolby(video: dict) -> bool:
    return any(s.get("side_data_type") == "DOVI configuration record"
               for s in video.get("side_data_list", []))


def tone_map(video: dict) -> str:
    transfer = video.get("color_transfer")
    if transfer not in {"arib-std-b67", "smpte2084"}:
        raise EditError(f"cannot safely convert unknown HDR transfer {transfer!r} to SDR")
    # Work in linear light before mapping HDR into the SDR range. DV profile
    # 8.4 uses the HLG base layer; this export is explicitly SDR, never DV.
    return ("zscale=transfer=linear:npl=100,format=gbrpf32le,"
            "tonemap=tonemap=mobius:desat=0,"
            "zscale=primaries=bt709:transfer=bt709:matrix=bt709,")


def render_ranges(source: Path, target: Path, ranges: list[tuple[float, float]],
                  video: dict, has_audio: bool, sdr: bool = False) -> None:
    dv = is_dolby(video)
    if dv and not sdr:
        raise EditError("Dolby Vision cuts require --sdr; RPU cannot survive a frame-accurate edit")
    hdr = video.get("color_transfer") in {"arib-std-b67", "smpte2084"}
    if hdr and not sdr and video.get("color_transfer") != "arib-std-b67":
        raise EditError("PQ HDR cuts require --sdr")
    graph = []
    for index, (start, end) in enumerate(ranges):
        graph.append(f"[0:v:0]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[v{index}]")
        if has_audio:
            graph.append(f"[0:a:0]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[a{index}]")
    if len(ranges) > 1:
        labels = "".join(f"[v{i}][a{i}]" if has_audio else f"[v{i}]"
                         for i in range(len(ranges)))
        graph.append(f"{labels}concat=n={len(ranges)}:v=1:a={int(has_audio)}[vout]"
                     + ("[aout]" if has_audio else ""))
        vmap, amap = "[vout]", "[aout]"
    else:
        vmap, amap = "[v0]", "[a0]"
    if sdr and hdr:
        # Add the conversion after cuts so only retained frames are encoded.
        graph.append(f"{vmap}{tone_map(video)}format=yuv420p[vfinal]")
        vmap = "[vfinal]"
    elif not hdr or sdr:
        graph.append(f"{vmap}format=yuv420p[vfinal]")
        vmap = "[vfinal]"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or source.resolve() == target.resolve():
        raise EditError(f"output already exists or matches input: {target}")
    # A temporary file prevents a failed encode from being mistaken for a cut.
    with tempfile.TemporaryDirectory(prefix="vlog-edit-", dir=target.parent) as scratch:
        temp = Path(scratch) / ("render" + target.suffix)
        cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
               "-i", str(source), "-filter_complex", ";".join(graph), "-map", vmap]
        if has_audio:
            cmd += ["-map", amap, "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
        if hdr and not sdr:
            cmd += ["-c:v", "libx265", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p10le", "-color_primaries", "bt2020",
                    "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc",
                    "-x265-params", "log-level=error"]
        else:
            cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p"]
            if sdr and hdr:
                cmd += ["-color_primaries", "bt709", "-color_trc", "bt709",
                        "-colorspace", "bt709"]
            else:
                # A single-source SDR cut should keep its camera color tags.
                for option, key in (("-color_primaries", "color_primaries"),
                                    ("-color_trc", "color_transfer"),
                                    ("-colorspace", "color_space")):
                    if video.get(key) not in (None, "unknown"):
                        cmd += [option, video[key]]
        cmd += ["-movflags", "+faststart", str(temp)]
        command(cmd)
        actual, _, _ = probe(temp)
        expected = sum(end - start for start, end in ranges)
        if abs(actual - expected) > max(0.2, expected * 0.005):
            raise EditError(f"edited duration mismatch: expected {expected:.3f}s, got {actual:.3f}s")
        os.replace(temp, target)


def draft_sources(draft: Path, log, utc_offset: str | None = None) -> list[tuple[Path, Path | None]]:
    rows = ordering.ensure_current(draft, log, utc_offset=utc_offset)
    result = []
    for row in rows:
        source = draft / row["new_name"]
        folder = ordering.analysis_folder(draft / "processed-clips", row["original_name"])
        report_path = folder / "report.json"
        sidecar = None
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if report.get("source_bytes") == source.stat().st_size:
                for key in ("cut_output", "processed_output", "voice_only_output"):
                    candidate = folder / (report.get(key) or "")
                    if report.get(key) and candidate.is_file():
                        source = candidate
                        break
                else:
                    candidate = folder / "enhanced-voice.wav"
                    sidecar = candidate if candidate.is_file() else None
        result.append((source, sidecar))
    return result


def normalized_segment(source: Path, sidecar: Path | None, target: Path,
                       ranges: list[tuple[float, float]] | None = None) -> None:
    duration, video, has_audio = probe(source)
    hdr = video.get("color_transfer") in {"arib-std-b67", "smpte2084"}
    if is_dolby(video) and not hdr:
        raise EditError(f"Dolby Vision clip has no supported HDR base layer: {source.name}")
    # The joined master is deliberately BT.709 SDR. Convert tagged SDR camera
    # gamuts as well as HDR rather than just changing the output metadata.
    sdr_convert = ("zscale=primaries=bt709:transfer=bt709:matrix=bt709,"
                   if not hdr and all(video.get(k) not in (None, "unknown") for k in
                                      ("color_primaries", "color_transfer", "color_space"))
                   else "")
    video_filter = (tone_map(video) if hdr else sdr_convert) + (
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p")
    kept = ranges or [(0.0, duration)]
    if not kept or any(end <= start or start < 0 or end > duration + 0.05
                       for start, end in kept):
        raise EditError(f"invalid kept ranges for {source.name}")
    expected = sum(min(end, duration) - start for start, end in kept)
    cmd = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(source)]
    if sidecar:
        cmd += ["-i", str(sidecar)]
    elif not has_audio:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    audio_index = 1 if sidecar or not has_audio else 0
    full_clip = len(kept) == 1 and kept[0][0] <= 0 and kept[0][1] >= duration - 1e-6
    if full_clip:
        cmd += ["-map", "0:v:0", "-map", f"{audio_index}:a:0", "-vf", video_filter,
                "-t", f"{duration:.6f}"]
    else:
        graph = []
        for index, (start, end) in enumerate(kept):
            graph.append(f"[0:v:0]trim=start={start:.6f}:end={end:.6f},"
                         f"setpts=PTS-STARTPTS[v{index}]")
            graph.append(f"[{audio_index}:a:0]atrim=start={start:.6f}:end={end:.6f},"
                         f"asetpts=PTS-STARTPTS[a{index}]")
        if len(kept) > 1:
            graph.append("".join(f"[v{index}][a{index}]" for index in range(len(kept)))
                         + f"concat=n={len(kept)}:v=1:a=1[vc][ac]")
            video_label, audio_label = "[vc]", "[ac]"
        else:
            video_label, audio_label = "[v0]", "[a0]"
        graph.append(f"{video_label}{video_filter}[v]")
        cmd += ["-filter_complex", ";".join(graph), "-map", "[v]", "-map", audio_label,
                "-t", f"{expected:.6f}"]
    cmd += ["-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
            "-color_primaries", "bt709", "-color_trc", "bt709",
            "-colorspace", "bt709", "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(target)]
    command(cmd)
    actual, _, audio = probe(target)
    if not audio or abs(actual - expected) > max(0.25, expected * 0.005):
        raise EditError(f"normalized clip failed duration/audio validation: {source.name}")


def join(sources: list[tuple[Path, Path | None]], target: Path, log) -> None:
    if not sources:
        raise EditError("no clips to join")
    if target.suffix.lower() != ".mp4":
        raise EditError("joined output must use an .mp4 filename")
    if target.exists() or any(source.resolve() == target.resolve() for source, _ in sources):
        raise EditError(f"output already exists or matches an input: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vlog-join-", dir=target.parent) as scratch:
        work = Path(scratch)
        segments = []
        for index, (source, sidecar) in enumerate(sources, 1):
            segment = work / f"{index:05d}.mp4"
            normalized_segment(source, sidecar, segment)
            segments.append(segment)
            log(f"join: normalized {index}/{len(sources)} {source.name}")
        manifest = work / "concat.txt"
        # Use normalized forward-slash paths; FFmpeg's concat demuxer accepts
        # them on Windows and preserves the explicit order of the timeline.
        manifest.write_text("".join("file '" + str(p).replace("\\", "/").replace("'", "'\\''")
                                    + "'\n" for p in segments), encoding="utf-8")
        output = work / "joined.mp4"
        command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                 "-f", "concat", "-safe", "0", "-i", str(manifest), "-c", "copy",
                 "-movflags", "+faststart", str(output)])
        expected = sum(probe(p)[0] for p in segments)
        actual, video, audio = probe(output)
        if not audio or video.get("width") != 1920 or video.get("height") != 1080 \
                or abs(actual - expected) > max(0.5, len(segments) * 0.08):
            raise EditError(f"joined export failed validation: {actual:.3f}s vs {expected:.3f}s")
        os.replace(output, target)


def join_normalized(sources: list[Path], target: Path) -> None:
    """Concatenate already-normalized 1920x1080 SDR clips without re-encoding."""
    if not sources:
        raise EditError("no clips to join")
    if target.suffix.lower() != ".mp4":
        raise EditError("joined output must use an .mp4 filename")
    for source in sources:
        _, video, audio = probe(source)
        if not audio or video.get("width") != 1920 or video.get("height") != 1080:
            raise EditError(f"clip is not a normalized 1920x1080 export: {source.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vlog-join-", dir=target.parent) as scratch:
        work = Path(scratch)
        manifest = work / "concat.txt"
        manifest.write_text("".join(
            "file '" + str(p.resolve()).replace("\\", "/").replace("'", "'\\''") + "'\n"
            for p in sources), encoding="utf-8")
        output = work / "joined.mp4"
        command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                 "-f", "concat", "-safe", "0", "-i", str(manifest), "-c", "copy",
                 "-movflags", "+faststart", str(output)])
        expected = sum(probe(p)[0] for p in sources)
        actual, video, audio = probe(output)
        if not audio or video.get("width") != 1920 or video.get("height") != 1080 \
                or abs(actual - expected) > max(0.5, len(sources) * 0.08):
            raise EditError(f"joined export failed validation: {actual:.3f}s vs {expected:.3f}s")
        os.replace(output, target)


def run(cfg: dict, args, log) -> int:
    try:
        if args.action in {"trim", "cut"}:
            if not args.input or len(args.input) != 1 or not args.out:
                raise EditError("trim/cut require one --input and --out")
            source, target = Path(args.input[0]).expanduser().resolve(), Path(args.out).expanduser().resolve()
            if not source.is_file():
                raise EditError(f"input not found: {source}")
            duration, video, audio = probe(source)
            if args.action == "trim":
                if args.remove or args.start is None or args.end is None:
                    raise EditError("trim requires --start and --end")
                start, end = timestamp(args.start), timestamp(args.end)
                if end <= start or end > duration + 0.05:
                    raise EditError(f"trim must fit within {duration:.3f}s")
                ranges = [(start, min(end, duration))]
            else:
                if args.start or args.end or not args.remove:
                    raise EditError("cut requires one or more --remove START-END")
                ranges = cut_ranges(duration, args.remove)
            render_ranges(source, target, ranges, video, audio, args.sdr)
            log(f"edit {args.action}: {target}")
        else:
            if args.start or args.end or args.remove:
                raise EditError("join accepts --input or --draft, not trim/cut ranges")
            if bool(args.input) == bool(args.draft):
                raise EditError("join requires either --draft or repeated --input files")
            if args.draft:
                slug, _ = select_channels(cfg, args.channel)[0]
                if Path(args.draft).name != args.draft:
                    raise EditError("pass a draft folder name with --draft")
                draft = channel_root(cfg, slug) / "drafts" / args.draft
                if not draft.is_dir():
                    raise EditError(f"draft not found: {draft}")
                sources = draft_sources(draft, log, args.utc_offset)
                target = Path(args.out).expanduser().resolve() if args.out else draft / "video.mp4"
            else:
                if not args.out:
                    raise EditError("join with --input requires --out")
                sources = [(Path(p).expanduser().resolve(), None) for p in args.input]
                target = Path(args.out).expanduser().resolve()
            if any(not source.is_file() for source, _ in sources):
                raise EditError("one or more join inputs are missing")
            join(sources, target, log)
            log(f"edit join: {len(sources)} clips -> {target} (1920x1080 SDR, 30 fps)")
        return 0
    except (EditError, ordering.OrderError, OSError, ValueError) as exc:
        log(f"edit: {exc}")
        return 1
