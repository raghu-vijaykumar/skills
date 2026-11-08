#!/usr/bin/env python3
"""Choose and apply reviewed video transitions at timeline points or clip joins.

Two routes are deliberately separate:

* ``apply`` adds a time-preserving effect at a point on one finished master.
  Narration and total duration stay unchanged.
* ``join`` cross-fades or wipes between ordered clips. The overlap shortens the
  result, so the duration change is reported instead of hidden.

Catalog-only Clipchamp transitions are listed but refused with an explicit
error; this script never fabricates a renderer for a missing asset.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CATALOG = SKILL / "presets" / "transitions.json"
SAMPLE_RATE = 48000


def load_catalog(path: str | Path | None = None) -> dict:
    data = json.loads(Path(path or CATALOG).read_text(encoding="utf-8-sig"))
    transitions = data.get("transitions")
    if not isinstance(transitions, list) or not transitions:
        raise ValueError("Transition catalog must contain a non-empty transitions list")
    return data


def catalog_index(path: str | Path | None = None) -> dict[str, dict]:
    return {item["id"]: item for item in load_catalog(path)["transitions"]}


def defaults(path: str | Path | None = None) -> dict:
    data = load_catalog(path)
    return data.get("defaults") or {}


def list_transitions(
    mode: str | None = None,
    fidelity: str | None = None,
    path: str | Path | None = None,
) -> list[dict]:
    items = load_catalog(path)["transitions"]
    if mode:
        items = [item for item in items if mode in item.get("modes", [])]
    if fidelity:
        items = [item for item in items if item.get("fidelity") == fidelity]
    return items


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def normalize_cues(data: object) -> list[dict]:
    if isinstance(data, dict):
        cues = data.get("transitions")
    else:
        cues = data
    if not isinstance(cues, list) or not cues:
        raise ValueError("Cue sheet needs a non-empty transitions array")
    return cues


def validate_cues(
    data: object,
    mode: str = "point",
    video_seconds: float | None = None,
    path: str | Path | None = None,
) -> tuple[list[str], list[dict]]:
    catalog = catalog_index(path)
    limits = defaults(path)
    minimum = float(limits.get("min_duration", 0.15))
    maximum = float(limits.get("max_duration", 3.0))
    gap = float(limits.get("gap", 0.05))
    issues: list[str] = []
    resolved: list[dict] = []

    for index, cue in enumerate(normalize_cues(data)):
        label = f"transition {index}"
        if not isinstance(cue, dict):
            issues.append(f"{label}: must be an object")
            continue
        transition_id = cue.get("id")
        entry = catalog.get(transition_id)
        if not entry:
            issues.append(f"{label}: unknown transition id {transition_id!r}")
            continue
        try:
            at = _number(cue.get("at"), f"{label} at")
        except ValueError as error:
            issues.append(str(error))
            continue
        try:
            duration = _number(
                cue.get("duration", entry.get("default_duration", 0.6)),
                f"{label} duration",
            )
        except ValueError as error:
            issues.append(str(error))
            continue
        if not minimum <= duration <= maximum:
            issues.append(f"{label}: duration must be {minimum}-{maximum}s")
        if mode not in entry.get("modes", []):
            issues.append(f"{label}: {transition_id} is not available in {mode} mode")
        if entry.get("fidelity") == "catalog-only":
            issues.append(f"{label}: {transition_id} is catalog-only and has no renderer")
        start = at - duration / 2
        end = at + duration / 2
        if start < -1e-9:
            issues.append(f"{label}: starts before 0s")
        if video_seconds is not None and end > video_seconds + 1e-6:
            issues.append(f"{label}: ends after the {video_seconds:.3f}s video")
        resolved.append(
            {
                "id": transition_id,
                "at": round(at, 3),
                "duration": round(duration, 3),
                "start": round(start, 3),
                "end": round(end, 3),
                "fidelity": entry.get("fidelity"),
            }
        )

    resolved.sort(key=lambda item: item["at"])
    for previous, current in zip(resolved, resolved[1:]):
        if current["start"] < previous["end"] + gap - 1e-9:
            issues.append(
                f"transitions at {previous['at']}s and {current['at']}s overlap"
            )
    return issues, resolved


def point_effect_filters(cue: dict, spec: dict) -> list[str]:
    """Timeline-enabled filters for blur and glitch point effects."""
    start, end = cue["start"], cue["end"]
    kind = spec.get("type")
    if kind == "blur":
        sigma = float(spec.get("sigma", 18))
        return [f"gblur=sigma={sigma}:enable='between(t,{start:.6f},{end:.6f})'"]
    if kind == "glitch":
        shift = int(spec.get("shift", 10))
        noise = int(spec.get("noise", 20))
        contrast = float(spec.get("contrast", 1.0))
        enable = f"enable='between(t,{start:.6f},{end:.6f})'"
        chain = [
            f"rgbashift=rh={shift}:bh=-{shift}:{enable}",
            f"noise=alls={noise}:allf=t+u:{enable}",
        ]
        if contrast != 1.0:
            chain.append(f"eq=contrast={contrast}:{enable}")
        return chain
    raise ValueError(f"Unknown point effect {kind!r}")


def point_filtergraph(
    resolved: list[dict],
    width: int,
    height: int,
    fps: float,
    duration: float,
    path: str | Path | None = None,
) -> str:
    """Build a time-preserving graph for point effects.

    A fade is a coloured RGBA overlay whose alpha ramps in and out. Chaining
    ``fade`` directly on the master would black out everything before and after
    the cue, because each fade holds its outside value for the whole stream.
    """
    catalog = catalog_index(path)
    if not resolved:
        raise ValueError("No point transitions to apply")
    parts: list[str] = ["[0:v]format=yuv420p[b0]"]
    current = "b0"
    for index, cue in enumerate(resolved):
        entry = catalog[cue["id"]]
        spec = entry.get("point")
        if not spec:
            raise ValueError(f"{cue['id']} has no point renderer")
        target = f"b{index + 1}"
        if spec.get("type") == "fade":
            color = spec.get("color", "black")
            half = cue["duration"] / 2
            parts.append(
                f"color=c={color}:s={width}x{height}:r={fps}:d={duration:.6f},"
                f"format=rgba,"
                f"fade=t=in:st={cue['start']:.6f}:d={half:.6f}:alpha=1,"
                f"fade=t=out:st={cue['at']:.6f}:d={half:.6f}:alpha=1[o{index}]"
            )
            parts.append(f"[{current}][o{index}]overlay=0:0:shortest=1[{target}]")
        else:
            chain = point_effect_filters(cue, spec)
            parts.append(f"[{current}]" + ",".join(chain) + f"[{target}]")
        current = target
    parts.append(f"[{current}]null[vout]")
    return ";".join(parts)


def _ffprobe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError(f"Cannot probe media: {path}")
    return json.loads(result.stdout)


def display_dimensions(video: dict) -> tuple[int, int]:
    """Return the autorotated frame size FFmpeg will actually filter."""
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    rotation = 0
    for side in video.get("side_data_list", []):
        if "rotation" in side:
            rotation = int(side["rotation"])
    if abs(rotation) % 180 == 90:
        width, height = height, width
    return max(2, width - width % 2), max(2, height - height % 2)


def probe_media(path: Path) -> dict:
    data = _ffprobe(path)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video:
        raise ValueError(f"No video stream: {path}")
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    width, height = display_dimensions(video)
    rate = video.get("r_frame_rate") or "0/1"
    try:
        numerator, denominator = (float(part) for part in rate.split("/", 1))
        fps = numerator / denominator if denominator else 0.0
    except (TypeError, ValueError):
        fps = 0.0
    return {
        "path": path,
        "duration": float(data.get("format", {}).get("duration", 0.0)),
        "width": width,
        "height": height,
        "fps": round(fps, 3) if fps else 30.0,
        "has_audio": bool(audio),
        "audio_codec": (audio or {}).get("codec_name"),
        "color_transfer": video.get("color_transfer"),
        "color_primaries": video.get("color_primaries"),
    }


def ensure_sdr(media: dict) -> None:
    if media.get("color_transfer") in ("smpte2084", "arib-std-b67") or media.get(
        "color_primaries"
    ) == "bt2020":
        raise ValueError("HDR/HLG source unsupported: tone-map to SDR first")


def validate_join(
    data: object, path: str | Path | None = None
) -> tuple[list[str], list[dict], list[str]]:
    catalog = catalog_index(path)
    limits = defaults(path)
    minimum = float(limits.get("min_duration", 0.15))
    maximum = float(limits.get("max_duration", 3.0))
    if not isinstance(data, dict):
        raise ValueError("Join cue sheet must be an object")
    inputs = data.get("inputs")
    cues = data.get("transitions")
    if not isinstance(inputs, list) or len(inputs) < 2:
        raise ValueError("Join needs at least two inputs")
    if not isinstance(cues, list):
        raise ValueError("Join needs a transitions array")
    issues: list[str] = []
    by_after: dict[int, dict] = {}
    for cue in cues:
        if not isinstance(cue, dict):
            issues.append("boundary cue must be an object")
            continue
        after = cue.get("after")
        if (
            not isinstance(after, int)
            or isinstance(after, bool)
            or after < 0
            or after >= len(inputs) - 1
        ):
            issues.append(f"boundary after={after!r} is out of range")
            continue
        if after in by_after:
            issues.append(f"boundary after={after} is duplicated")
            continue
        transition_id = cue.get("id")
        entry = catalog.get(transition_id)
        if not entry:
            issues.append(f"boundary after={after}: unknown transition id {transition_id!r}")
            continue
        if "join" not in entry.get("modes", []):
            issues.append(f"boundary after={after}: {transition_id} is not a join transition")
            continue
        if entry.get("fidelity") == "catalog-only":
            issues.append(f"boundary after={after}: {transition_id} is catalog-only")
            continue
        try:
            duration = _number(
                cue.get("duration", entry.get("default_duration", 0.6)),
                f"boundary after={after} duration",
            )
        except ValueError as error:
            issues.append(str(error))
            continue
        if not minimum <= duration <= maximum:
            issues.append(f"boundary after={after}: duration must be {minimum}-{maximum}s")
        by_after[after] = {
            "after": after,
            "id": transition_id,
            "duration": round(duration, 3),
            "xfade": entry.get("xfade"),
            "fidelity": entry.get("fidelity"),
        }
    missing = [index for index in range(len(inputs) - 1) if index not in by_after]
    if missing:
        issues.append("missing transitions after: " + ", ".join(map(str, missing)))
    resolved = [by_after[index] for index in sorted(by_after)]
    return issues, resolved, [str(item) for item in inputs]


def join_graph(
    media: list[dict],
    resolved: list[dict],
    width: int,
    height: int,
    fps: float,
) -> tuple[str, str, float]:
    parts: list[str] = []
    for index, _item in enumerate(media):
        parts.append(
            f"[{index}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},"
            f"settb=AVTB,format=yuv420p[v{index}]"
        )
    length = float(media[0]["duration"])
    previous = "v0"
    for index, cue in enumerate(resolved, start=1):
        duration = float(cue["duration"])
        if duration >= length or duration >= float(media[index]["duration"]):
            raise ValueError(f"transition after={cue['after']} is longer than a clip")
        offset = length - duration
        label = f"x{index}"
        parts.append(
            f"[{previous}][v{index}]xfade=transition={cue['xfade']}:"
            f"duration={duration:.6f}:offset={offset:.6f}[{label}]"
        )
        length = length + float(media[index]["duration"]) - duration
        previous = label
    return ";".join(parts), previous, length


def join_audio_graph(
    count: int, resolved: list[dict]
) -> tuple[str, str]:
    parts: list[str] = []
    for index in range(count):
        parts.append(
            f"[{index}:a]aresample={SAMPLE_RATE},"
            f"aformat=channel_layouts=stereo[a{index}]"
        )
    previous = "a0"
    for index, cue in enumerate(resolved, start=1):
        label = f"ax{index}"
        parts.append(
            f"[{previous}][a{index}]acrossfade=d={float(cue['duration']):.6f}:"
            f"c1=tri:c2=tri[{label}]"
        )
        previous = label
    return ";".join(parts), previous


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed: "
            + " ".join(command)
            + "\n"
            + (result.stderr or result.stdout)[-3000:]
        )


def render_point(
    input_path: str | Path,
    output_path: str | Path,
    data: object,
    preview_start: float | None = None,
    preview_duration: float | None = None,
    path: str | Path | None = None,
) -> dict:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and FFprobe are required")
    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"Input not found: {source}")
    if target == source or target.exists():
        raise ValueError("Output must be a new file; the source is never overwritten")
    media = probe_media(source)
    ensure_sdr(media)
    issues, resolved = validate_cues(
        data, mode="point", video_seconds=media["duration"], path=path
    )
    if issues:
        raise ValueError("; ".join(issues))
    graph = point_filtergraph(
        resolved,
        media["width"],
        media["height"],
        media["fps"],
        media["duration"] + 0.5,
        path,
    )
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-n",
        "-i",
        str(source),
        "-filter_complex",
        graph,
        "-map",
        "[vout]",
        "-map",
        "0:a?",
    ]
    if preview_start is not None:
        duration = preview_duration if preview_duration is not None else 5.0
        command += ["-ss", f"{preview_start:.6f}", "-t", f"{duration:.6f}"]
    command += [
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        str(target),
    ]
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        _run(command)
    except RuntimeError:
        command[command.index("-c:a") + 1] = "aac"
        _run(command)
    return {
        "mode": "point",
        "output": str(target),
        "source_seconds": round(media["duration"], 3),
        "duration_change_seconds": 0.0,
        "transitions": resolved,
    }


def render_join(
    data: object,
    output_path: str | Path,
    path: str | Path | None = None,
    size: tuple[int, int] | None = None,
    fps: float | None = None,
    audio: str = "auto",
) -> dict:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and FFprobe are required")
    issues, resolved, input_paths = validate_join(data, path)
    if issues:
        raise ValueError("; ".join(issues))
    sources = [Path(item).expanduser().resolve() for item in input_paths]
    for source in sources:
        if not source.is_file():
            raise ValueError(f"Input not found: {source}")
    target = Path(output_path).expanduser().resolve()
    if target in sources or target.exists():
        raise ValueError("Output must be a new file; inputs are never overwritten")
    media = [probe_media(source) for source in sources]
    for item in media:
        ensure_sdr(item)
    width, height = size or (
        max(item["width"] for item in media),
        max(item["height"] for item in media),
    )
    frame_rate = fps or media[0]["fps"] or 30.0
    graph_v, video_label, total = join_graph(media, resolved, width, height, frame_rate)
    has_audio = all(item["has_audio"] for item in media)
    if audio == "none" or not has_audio:
        graph = graph_v
        maps = ["-map", f"[{video_label}]", "-an"]
        audio_args: list[str] = []
    else:
        graph_a, audio_label = join_audio_graph(len(media), resolved)
        graph = graph_v + ";" + graph_a
        maps = ["-map", f"[{video_label}]", "-map", f"[{audio_label}]"]
        audio_args = ["-c:a", "aac", "-b:a", "192k"]
    command = ["ffmpeg", "-hide_banner", "-nostdin", "-n"]
    for source in sources:
        command += ["-i", str(source)]
    command += [
        "-filter_complex",
        graph,
        *maps,
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
        *audio_args,
        "-movflags",
        "+faststart",
        str(target),
    ]
    target.parent.mkdir(parents=True, exist_ok=True)
    _run(command)
    return {
        "mode": "join",
        "output": str(target),
        "size": [width, height],
        "fps": frame_rate,
        "output_seconds": round(total, 3),
        "source_seconds": round(sum(item["duration"] for item in media), 3),
        "duration_change_seconds": round(
            total - sum(item["duration"] for item in media), 3
        ),
        "audio": "crossfade" if has_audio and audio != "none" else "none",
        "transitions": resolved,
    }


def annotate_timeline(
    timeline: dict,
    data: object,
    path: str | Path | None = None,
) -> dict:
    issues, resolved = validate_cues(data, mode="point", path=path)
    if issues:
        raise ValueError("; ".join(issues))
    result = json.loads(json.dumps(timeline))
    result.setdefault("transitions", [])
    for cue in resolved:
        at = float(cue["at"])
        attached = False
        for clip in result.get("clips", []):
            start = float(clip.get("timeline_start", 0))
            end = float(clip.get("timeline_end", 0))
            if start - 1e-6 <= at <= end + 1e-6:
                clip.setdefault("point_transitions", []).append(dict(cue))
                attached = True
                break
        if not attached:
            result["transitions"].append(dict(cue))
    return result


def plan(
    data: object,
    input_path: str | Path | None = None,
    path: str | Path | None = None,
) -> dict:
    if isinstance(data, dict) and data.get("inputs"):
        issues, resolved, _ = validate_join(data, path)
        if issues:
            return {"mode": "join", "issues": issues, "transitions": resolved}
        media = [probe_media(Path(item).expanduser().resolve()) for item in data["inputs"]]
        total = sum(item["duration"] for item in media) - sum(
            float(cue["duration"]) for cue in resolved
        )
        return {
            "mode": "join",
            "inputs": len(media),
            "source_seconds": round(sum(item["duration"] for item in media), 3),
            "output_seconds": round(total, 3),
            "duration_change_seconds": round(
                total - sum(item["duration"] for item in media), 3
            ),
            "transitions": resolved,
            "issues": [],
        }
    video_seconds = None
    if input_path:
        media = probe_media(Path(input_path).expanduser().resolve())
        ensure_sdr(media)
        video_seconds = media["duration"]
    issues, resolved = validate_cues(
        data, mode="point", video_seconds=video_seconds, path=path
    )
    return {
        "mode": "point",
        "source_seconds": None if video_seconds is None else round(video_seconds, 3),
        "duration_change_seconds": 0.0,
        "transitions": resolved,
        "issues": issues,
    }


def _print_catalog(items: list[dict]) -> None:
    header = f"{'id':24} {'modes':12} {'fidelity':12} name"
    print(header)
    print("-" * len(header))
    for item in items:
        modes = ",".join(item.get("modes", [])) or "-"
        print(
            f"{item['id']:24} {modes:12} {item.get('fidelity',''):12} {item.get('name','')}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="List the transition catalog")
    p.add_argument("--mode", choices=["point", "join"])
    p.add_argument("--fidelity", choices=["native", "approximate", "catalog-only"])
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("validate", help="Validate a cue sheet")
    p.add_argument("cues")
    p.add_argument("--mode", choices=["point", "join"], default="point")
    p.add_argument("--input", help="Optional master video for duration checks")

    p = sub.add_parser("plan", help="Resolve timings without rendering")
    p.add_argument("cues")
    p.add_argument("--input")
    p.add_argument("--output")

    p = sub.add_parser("apply", help="Apply point transitions to one master")
    p.add_argument("cues")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--preview-start", type=float)
    p.add_argument("--preview-duration", type=float)

    p = sub.add_parser("join", help="Join clips with boundary transitions")
    p.add_argument("cues")
    p.add_argument("--output", required=True)
    p.add_argument("--size", help="WxH canvas, default largest input")
    p.add_argument("--fps", type=float)
    p.add_argument("--audio", choices=["auto", "none"], default="auto")

    p = sub.add_parser("annotate", help="Annotate a copy of an edit timeline")
    p.add_argument("timeline")
    p.add_argument("--cues", required=True)
    p.add_argument("--output", required=True)

    args = parser.parse_args(argv)

    if args.command == "list":
        items = list_transitions(args.mode, args.fidelity)
        if args.json:
            print(json.dumps(items, indent=2, ensure_ascii=False))
        else:
            _print_catalog(items)
        return 0

    if args.command == "validate":
        data = json.loads(Path(args.cues).read_text(encoding="utf-8-sig"))
        if args.mode == "join":
            issues, resolved, _ = validate_join(data)
        else:
            video_seconds = None
            if args.input:
                video_seconds = probe_media(Path(args.input).expanduser().resolve())[
                    "duration"
                ]
            issues, resolved = validate_cues(
                data, mode="point", video_seconds=video_seconds
            )
        print(json.dumps({"issues": issues, "transitions": resolved}, indent=2))
        return 1 if issues else 0

    if args.command == "plan":
        data = json.loads(Path(args.cues).read_text(encoding="utf-8-sig"))
        result = plan(data, args.input)
        text = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        return 1 if result.get("issues") else 0

    if args.command == "apply":
        data = json.loads(Path(args.cues).read_text(encoding="utf-8-sig"))
        result = render_point(
            args.input,
            args.output,
            data,
            preview_start=args.preview_start,
            preview_duration=args.preview_duration,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "join":
        data = json.loads(Path(args.cues).read_text(encoding="utf-8-sig"))
        size = None
        if args.size:
            width, height = args.size.lower().split("x", 1)
            size = (int(width), int(height))
        result = render_join(data, args.output, size=size, fps=args.fps, audio=args.audio)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "annotate":
        timeline = json.loads(Path(args.timeline).read_text(encoding="utf-8-sig"))
        data = json.loads(Path(args.cues).read_text(encoding="utf-8-sig"))
        result = annotate_timeline(timeline, data)
        Path(args.output).write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(json.dumps({"output": args.output}, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
