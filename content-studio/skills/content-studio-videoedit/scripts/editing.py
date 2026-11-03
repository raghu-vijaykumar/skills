"""Frame-accurate vlog cuts and a normalized mixed-camera assembly."""

from __future__ import annotations

import json
import html
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from common import channel_root, select_channels
import draftlayout
import ordering


class EditError(RuntimeError):
    pass


def command(args: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
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


def display_dimensions(video: dict) -> tuple[int, int]:
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    rotation = 0
    for side in video.get("side_data_list", []):
        if "rotation" in side:
            rotation = int(side["rotation"])
    if abs(rotation) % 180 == 90:
        width, height = height, width
    return max(2, width - width % 2), max(2, height - height % 2)


def max_target_size(sources: list[Path]) -> tuple[int, int]:
    """Pick the largest source resolution by pixel area; never choose smaller."""
    best = None
    for source in sources:
        _, video, _ = probe(source)
        width, height = display_dimensions(video)
        key = (width * height, 1 if width >= height else 0)
        if best is None or key > best[0]:
            best = (key, width, height)
    if best is None:
        raise EditError("no sources for target resolution")
    return best[1], best[2]


def parse_target_size(value: str | None, sources: list[Path]) -> tuple[int, int]:
    if not value or str(value).strip().lower() in {"auto", "max", "source"}:
        return max_target_size(sources)
    match = re.fullmatch(r"(\d+)x(\d+)", str(value).strip().lower())
    if not match:
        raise EditError("size must be auto, max, or WxH")
    width, height = int(match.group(1)), int(match.group(2))
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise EditError("size must be positive even dimensions")
    return width, height


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
    draftlayout.ensure_layout(draft)
    for moved in draftlayout.migrate(draft, log):
        log(f"layout: {moved}")
    rows = ordering.ensure_current(draft, log, utc_offset=utc_offset)
    originals = draftlayout.original_dir(draft)
    result = []
    for row in rows:
        source = originals / row["new_name"]
        folder = ordering.analysis_folder(draftlayout.processed_dir(draft), row["original_name"])
        report_path = folder / "report.json"
        sidecar = None
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if report.get("source_bytes") == source.stat().st_size:
                for key in ("final_output", "cut_output", "processed_output", "voice_only_output"):
                    candidate = folder / (report.get(key) or "")
                    if report.get(key) and candidate.is_file():
                        source = candidate
                        break
                else:
                    candidate = folder / "enhanced-voice.wav"
                    sidecar = candidate if candidate.is_file() else None
        result.append((source, sidecar))
    return result


def orientation(width: int, height: int) -> str:
    if width > height:
        return "landscape"
    if height > width:
        return "portrait"
    return "square"


def filter_orientation(sources: list[tuple[Path, Path | None]], target: str,
                       include_mismatched: bool = False, allow: list[str] | None = None,
                       log=None) -> list[tuple[Path, Path | None]]:
    if target in (None, "", "any"):
        return sources
    allowed = {name.lower() for name in (allow or [])}
    kept = []
    for source, sidecar in sources:
        _, video, _ = probe(source)
        value = orientation(int(video.get("width") or 0), int(video.get("height") or 0))
        names = {source.name.lower(), source.parent.name.lower()}
        if value == target or include_mismatched or names & allowed:
            kept.append((source, sidecar))
        elif log:
            log(f"join: skipped {source.name} ({value}, target {target})")
    return kept


def parse_size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)x(\d+)", str(value).strip().lower())
    if not match:
        raise EditError("size must look like 1920x1080")
    width, height = int(match.group(1)), int(match.group(2))
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise EditError("size must be positive even dimensions")
    return width, height


def fit_graph(label: str, width: int, height: int, fit: str, out: str) -> list[str]:
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise EditError("target size must be positive even dimensions")
    fit = fit.lower()
    if fit == "pad":
        return [f"{label}scale={width}:{height}:force_original_aspect_ratio=decrease:"
                f"force_divisible_by=2,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                f"fps=30,format=yuv420p{out}"]
    if fit == "crop":
        return [f"{label}scale={width}:{height}:force_original_aspect_ratio=increase:"
                f"force_divisible_by=2,crop={width}:{height},fps=30,format=yuv420p{out}"]
    if fit == "blur":
        return [
            f"{label}split=2[bg][fg]",
            f"[bg]scale={width}:{height}:force_original_aspect_ratio=increase:"
            f"force_divisible_by=2,crop={width}:{height},gblur=sigma=20[bgblur]",
            f"[fg]scale={width}:{height}:force_original_aspect_ratio=decrease:"
            f"force_divisible_by=2[fgfit]",
            f"[bgblur][fgfit]overlay=(W-w)/2:(H-h)/2,fps=30,format=yuv420p{out}",
        ]
    raise EditError(f"unknown fit mode: {fit}")


def detect_stabilization(source: Path, work: Path) -> None:
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(source), "-map", "0:v:0",
             "-vf", "vidstabdetect=shakiness=5:accuracy=9:result=transforms.trf",
             "-an", "-f", "null", os.devnull], cwd=work)


def normalized_segment(source: Path, sidecar: Path | None, target: Path,
                       ranges: list[tuple[float, float]] | None = None,
                       size: tuple[int, int] = (1920, 1080),
                       fit: str = "blur", stabilize: bool = False) -> None:
    duration, video, has_audio = probe(source)
    hdr = video.get("color_transfer") in {"arib-std-b67", "smpte2084"}
    if is_dolby(video) and not hdr:
        raise EditError(f"Dolby Vision clip has no supported HDR base layer: {source.name}")
    work = None
    try:
        if stabilize:
            work = Path(tempfile.mkdtemp(prefix="vlog-stab-", dir=target.parent))
            detect_stabilization(source, work)
        # The joined master is deliberately BT.709 SDR. Convert tagged SDR camera
        # gamuts as well as HDR rather than just changing the output metadata.
        sdr_convert = ("zscale=primaries=bt709:transfer=bt709:matrix=bt709,"
                       if not hdr and all(video.get(k) not in (None, "unknown") for k in
                                          ("color_primaries", "color_transfer", "color_space"))
                       else "")
        color_filter = tone_map(video) if hdr else sdr_convert
        width, height = size
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
        stabilizer = "vidstabtransform=input=transforms.trf:smoothing=15:optzoom=1"
        video_in = "[0:v:0]"
        graph = []
        if stabilize:
            graph.append(f"[0:v:0]{stabilizer}[stab]")
            video_in = "[stab]"
        if full_clip:
            graph.append(f"{video_in}{color_filter.rstrip(',') if color_filter else 'null'}[src]")
            graph += fit_graph("[src]", width, height, fit, "[v]")
            cmd += ["-filter_complex", ";".join(graph), "-map", "[v]",
                    "-map", f"{audio_index}:a:0", "-t", f"{duration:.6f}"]
        else:
            for index, (start, end) in enumerate(kept):
                graph.append(f"{video_in}trim=start={start:.6f}:end={end:.6f},"
                             f"setpts=PTS-STARTPTS[v{index}]")
                graph.append(f"[{audio_index}:a:0]atrim=start={start:.6f}:end={end:.6f},"
                             f"asetpts=PTS-STARTPTS[a{index}]")
            if len(kept) > 1:
                graph.append("".join(f"[v{index}][a{index}]" for index in range(len(kept)))
                             + f"concat=n={len(kept)}:v=1:a=1[vc][ac]")
                video_label, audio_label = "[vc]", "[ac]"
            else:
                video_label, audio_label = "[v0]", "[a0]"
            graph.append(f"{video_label}{color_filter.rstrip(',') if color_filter else 'null'}[src]")
            graph += fit_graph("[src]", width, height, fit, "[v]")
            cmd += ["-filter_complex", ";".join(graph), "-map", "[v]", "-map", audio_label,
                    "-t", f"{expected:.6f}"]
        cmd += ["-c:v", "libx264", "-preset", "medium",
                "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
                "-color_primaries", "bt709", "-color_trc", "bt709",
                "-colorspace", "bt709", "-c:a", "aac", "-b:a", "192k",
                "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(target)]
        command(cmd, cwd=work)
        actual, rendered, audio = probe(target)
        if not audio or rendered.get("width") != width or rendered.get("height") != height \
                or abs(actual - expected) > max(0.25, expected * 0.005):
            raise EditError(f"normalized clip failed duration/audio/size validation: {source.name}")
    finally:
        if work is not None:
            shutil.rmtree(work, ignore_errors=True)


def join(sources: list[tuple[Path, Path | None]], target: Path, log,
         fit: str = "blur", size: tuple[int, int] = (1920, 1080),
         scratch: Path | None = None) -> None:
    if not sources:
        raise EditError("no clips to join")
    if target.suffix.lower() != ".mp4":
        raise EditError("joined output must use an .mp4 filename")
    if target.exists() or any(source.resolve() == target.resolve() for source, _ in sources):
        raise EditError(f"output already exists or matches an input: {target}")
    width, height = size
    target.parent.mkdir(parents=True, exist_ok=True)
    scratch_root = scratch or target.parent
    scratch_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vlog-join-", dir=scratch_root) as scratch_dir:
        work = Path(scratch_dir)
        segments = []
        for index, (source, sidecar) in enumerate(sources, 1):
            segment = work / f"{index:05d}.mp4"
            normalized_segment(source, sidecar, segment, size=size, fit=fit)
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
        if not audio or video.get("width") != width or video.get("height") != height \
                or abs(actual - expected) > max(0.5, len(segments) * 0.08):
            raise EditError(f"joined export failed validation: {actual:.3f}s vs {expected:.3f}s")
        os.replace(output, target)


def join_normalized(sources: list[Path], target: Path, scratch: Path | None = None,
                    size: tuple[int, int] = (1920, 1080)) -> None:
    """Concatenate already-normalized SDR clips without re-encoding."""
    if not sources:
        raise EditError("no clips to join")
    if target.suffix.lower() != ".mp4":
        raise EditError("joined output must use an .mp4 filename")
    width, height = size
    for source in sources:
        _, video, audio = probe(source)
        if not audio or video.get("width") != width or video.get("height") != height:
            raise EditError(f"clip is not a normalized {width}x{height} export: {source.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    scratch_root = scratch or target.parent
    scratch_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vlog-join-", dir=scratch_root) as scratch_dir:
        work = Path(scratch_dir)
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
        if not audio or video.get("width") != width or video.get("height") != height \
                or abs(actual - expected) > max(0.5, len(sources) * 0.08):
            raise EditError(f"joined export failed validation: {actual:.3f}s vs {expected:.3f}s")
        os.replace(output, target)


def strip_audio(source: Path, target: Path) -> None:
    """Write a video-only copy without re-encoding the picture."""
    target.parent.mkdir(parents=True, exist_ok=True)
    command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(source), "-map", "0:v:0", "-c:v", "copy", "-an",
             "-movflags", "+faststart", str(target)])


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def write_edit_timeline(entries: list[dict], output: Path, master: Path, root: Path) -> Path:
    """Write the ordered contribution of each source to the rendered master."""
    document = {
        "schema": "content-studio.edit-timeline.v1",
        "master": _relative(master, root),
        "duration_seconds": round(sum(float(item["duration"]) for item in entries), 3),
        "clips": entries,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "edit-timeline.json").write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8")
    rows = "".join(
        "<tr>"
        f"<td>{item['order']}</td>"
        f"<td>{float(item['timeline_start']):.2f}–{float(item['timeline_end']):.2f}</td>"
        f"<td>{html.escape(item.get('source') or '')}</td>"
        f"<td>{float(item['source_in']):.2f}–{float(item['source_out']):.2f}</td>"
        f"<td>{float(item['duration']):.2f}</td>"
        f"<td>{html.escape(item.get('note') or '')}</td>"
        "</tr>" for item in entries)
    page = ("<!doctype html><meta charset='utf-8'><title>Edit timeline</title>"
            "<style>body{font:15px/1.5 system-ui,sans-serif;margin:2rem;color:#0f172a}"
            "h1{margin:0 0 .25rem}p{color:#475569;margin:0 0 1.25rem}"
            "table{border-collapse:collapse;width:100%}th,td{padding:.55rem .7rem;"
            "border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}"
            "th{background:#f8fafc;font-size:.8rem;letter-spacing:.04em;text-transform:uppercase;color:#475569}"
            "tr:hover td{background:#f8fafc}code{font-family:ui-monospace,monospace}</style>"
            "<h1>Edit timeline</h1>"
            f"<p>{len(entries)} source contribution(s) · {document['duration_seconds']:.2f}s master · "
            f"<code>{html.escape(document['master'])}</code></p>"
            "<table><thead><tr><th>#</th><th>Master time (s)</th><th>Source</th>"
            "<th>Source in–out (s)</th><th>Duration (s)</th><th>Note</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>")
    (output / "edit-timeline.html").write_text(page, encoding="utf-8")
    return output / "edit-timeline.json"


def draft_join_timeline(draft: Path, sources: list[tuple[Path, Path | None]],
                        master: Path) -> Path:
    """Describe how each ordered draft clip contributes to the joined master."""
    processed = draftlayout.processed_dir(draft)
    originals = draftlayout.original_dir(draft)
    entries = []
    cursor = 0.0
    for index, (source, sidecar) in enumerate(sources, 1):
        duration, _, has_audio = probe(source)
        folder = source.parent if source.parent.parent == processed else None
        original = None
        note = []
        removed = []
        if folder is not None:
            report_path = folder / "report.json"
            if report_path.exists():
                report = json.loads(report_path.read_text(encoding="utf-8"))
                original = report.get("source")
                removed = report.get("final_cuts") or report.get("stored_cuts") or []
                if removed:
                    note.append(f"{len(removed)} blur span(s) removed")
                if report.get("final_output"):
                    note.append("final video")
                elif report.get("processed_output"):
                    note.append("processed video")
        if original is None:
            candidate = originals / ordering.original_name(source.name)
            original = str(candidate if candidate.exists() else source)
        entries.append({
            "order": index,
            "source": _relative(Path(original), draft),
            "rendered_source": _relative(source, draft),
            "timeline_start": round(cursor, 3),
            "timeline_end": round(cursor + duration, 3),
            "source_in": 0.0,
            "source_out": round(duration, 3),
            "duration": round(duration, 3),
            "has_audio": has_audio,
            "removed_ranges": removed,
            "note": "; ".join(note),
        })
        cursor += duration
    return write_edit_timeline(entries, draftlayout.rough_cut_dir(draft), master, draft)


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
            if bool(args.input) == bool(args.draft or getattr(args, "folder", None)):
                raise EditError("join requires either --draft, --folder, or repeated --input files")
            draft_dir = None
            if args.draft or getattr(args, "folder", None):
                if getattr(args, "folder", None):
                    draft = Path(args.folder).expanduser().resolve()
                else:
                    if Path(args.draft).name != args.draft:
                        raise EditError("pass a draft folder name with --draft")
                    slug, _ = select_channels(cfg, args.channel)[0]
                    draft = channel_root(cfg, slug) / "drafts" / args.draft
                if not draft.is_dir():
                    raise EditError(f"draft not found: {draft}")
                draft_dir = draft
                draftlayout.ensure_layout(draft)
                sources = draft_sources(draft, log, args.utc_offset)
                target = (Path(args.out).expanduser().resolve() if args.out
                          else draftlayout.final_path(draft))
            else:
                if not args.out:
                    raise EditError("join with --input requires --out")
                sources = [(Path(p).expanduser().resolve(), None) for p in args.input]
                target = Path(args.out).expanduser().resolve()
            if any(not source.is_file() for source, _ in sources):
                raise EditError("one or more join inputs are missing")
            sources = filter_orientation(
                sources, getattr(args, "orientation", "any"),
                getattr(args, "include_mismatched", False),
                getattr(args, "allow", None), log)
            if not sources:
                raise EditError("no clips match the requested orientation")
            size = parse_target_size(getattr(args, "size", None),
                                     [source for source, _ in sources])
            join(sources, target, log, fit=getattr(args, "fit", "blur"),
                 size=size,
                 scratch=draftlayout.scratch_dir(draft_dir) if draft_dir else None)
            if draft_dir is not None:
                timeline = draft_join_timeline(draft_dir, sources, target)
                log(f"edit join: timeline -> {timeline}")
            log(f"edit join: {len(sources)} clips -> {target} "
                f"({size[0]}x{size[1]} SDR, 30 fps, fit {getattr(args, 'fit', 'blur')})")
        return 0
    except (EditError, ordering.OrderError, OSError, ValueError) as exc:
        log(f"edit: {exc}")
        return 1
