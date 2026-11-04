"""Render reusable, source-timed motion cards over an edited video."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path


def probe(source: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,color_transfer",
         "-of", "json", str(source)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def validate(data: dict) -> tuple[Path, float, list[dict], bool]:
    source = Path(data["source"]).resolve()
    if not source.is_file():
        raise ValueError(f"Source video does not exist: {source}")
    meta = probe(source)
    duration = float(meta["format"]["duration"])
    streams = meta.get("streams", [])
    if not any(s.get("codec_type") == "video" for s in streams) or not any(s.get("codec_type") == "audio" for s in streams):
        raise ValueError("Source needs video and audio")
    hdr = any(s.get("color_transfer") in {"arib-std-b67", "smpte2084"} for s in streams)
    events = data.get("events", [])
    if not events:
        raise ValueError("At least one event is required")
    for index, event in enumerate(events):
        start, end = float(event["start"]), float(event["end"])
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= duration + 0.02):
            raise ValueError(f"Event {index} is outside the source duration")
        if event.get("kind") not in {"ingredient", "cta"}:
            raise ValueError(f"Event {index} needs ingredient or cta kind")
        if event["kind"] == "ingredient" and not all(event.get(key) for key in ("label", "action", "evidence")):
            raise ValueError(f"Ingredient event {index} needs label, action, and evidence")
    return source, duration, events, hdr


def stamp(seconds: float) -> str:
    centis = round(seconds * 100)
    return f"{centis // 360000}:{centis // 6000 % 60:02d}:{centis // 100 % 60:02d}.{centis % 100:02d}"


def clean(value: object) -> str:
    # ASS control syntax must never come from a cue label.
    return str(value).replace("{", "(").replace("}", ")").replace("\\", "/").replace("\n", " ")


def line(layer: int, start: float, end: float, body: str) -> str:
    return f"Dialogue: {layer},{stamp(start)},{stamp(end)},Default,,0,0,0,,{body}"


def motion(x: int, y: int, entering_from: int, duration_ms: int = 430) -> str:
    return f"\\an7\\move({entering_from},{y},{x},{y},0,{duration_ms})\\fad(170,260)"


def ass(data: dict, offset: float = 0, length: float | None = None) -> str:
    header = """[Script Info]
Title: Content Studio motion graphics
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00F7F4ED,&H00F7F4ED,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""
    rows = [header]
    for index, event in enumerate(data["events"], 1):
        start, end = float(event["start"]) - offset, float(event["end"]) - offset
        if end <= 0 or (length is not None and start >= length):
            continue
        start, end = max(0, start), min(end, length) if length is not None else end
        if end - start < 0.1:
            continue
        if event["kind"] == "ingredient":
            # Cream recipe cards, teal ink, and coral/yellow details borrow from the channel intro.
            x, y = 72, 82
            card = "m 18 0 l 610 0 b 626 0 636 10 636 26 l 636 106 b 636 120 626 130 610 130 l 18 130 b 5 130 0 120 0 106 l 0 22 b 0 10 5 0 18 0"
            rows.append(line(0, start, end, "{" + motion(x + 7, y + 9, -643) + "\\1c&H002B4A39&\\alpha&HB0&\\p1}" + card + "{\\p0}"))
            rows.append(line(1, start, end, "{" + motion(x, y, -650) + "\\1c&H00E9F3F7&\\alpha&H08&\\p1}" + card + "{\\p0}"))
            rows.append(line(2, start, end, "{" + motion(x, y + 117, -650) + "\\1c&H00686A17&\\p1}m 18 0 l 610 0 l 610 5 l 18 5{\\p0}"))
            rows.append(line(3, start, end, "{" + motion(x + 30, y + 17, -620) + "\\fs25\\1c&H005B70EF&}" + clean(event["action"]).upper()))
            rows.append(line(4, start, end, "{" + motion(x + 30, y + 57, -620) + "\\fs49\\1c&H002D3020&\\fscx92\\fscy92\\t(0,480,\\fscx100\\fscy100)}" + clean(event["label"])))
            rows.append(line(3, start, end, "{" + motion(x + 554, y + 17, -96) + "\\fs28\\1c&H005B70EF&}" + f"{index:02d} →"))
        else:
            # Staggered polaroid-like prompts use the same channel colors as the ingredient cards.
            labels = [("LIKE", "♥"), ("SHARE", "↗"), ("SUBSCRIBE", "▶")]
            for beat, (label, icon) in enumerate(labels):
                a = start + beat * 0.45
                if a >= end:
                    break
                x, y = 1370, 92 + beat * 82
                card = "m 14 0 l 454 0 b 465 0 470 6 470 16 l 470 52 b 470 63 464 68 454 68 l 14 68 b 4 68 0 62 0 52 l 0 16 b 0 5 5 0 14 0"
                rows.append(line(0, a, end, "{" + motion(x + 5, y + 6, 1975) + "\\1c&H002B4A39&\\alpha&HB0&\\p1}" + card + "{\\p0}"))
                rows.append(line(1, a, end, "{" + motion(x, y, 1970) + "\\1c&H00E9F3F7&\\alpha&H08&\\p1}" + card + "{\\p0}"))
                rows.append(line(2, a, end, "{" + motion(x + 22, y + 14, 1992) + "\\fs36\\1c&H00686A17&}" + label))
                rows.append(line(2, a, end, "{" + motion(x + 418, y + 12, 2388) + "\\fs38\\1c&H005B70EF&}" + icon))
            rows.append(line(1, start, end, "{" + motion(1370, 44, 1970) + "\\1c&H0063CFFF&\\alpha&H08&\\p1}m 10 0 l 460 0 l 470 10 l 470 35 l 0 35 l 0 10 l 10 0{\\p0}"))
            rows.append(line(2, start, end, "{" + motion(1390, 48, 1990) + "\\fs24\\1c&H00686A17&}" + "OUT OF OFFICE MODE  /  COOK"))
    return "\n".join(rows) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "render"])
    parser.add_argument("cues", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--duration", type=float)
    args = parser.parse_args()
    data = json.loads(args.cues.read_text(encoding="utf-8"))
    source, total, events, hdr = validate(data)
    if args.command == "validate":
        print(f"Valid: {len(events)} cues, {total:.2f}s source, {'HDR' if hdr else 'SDR'}")
        return
    if not args.output:
        parser.error("render requires --output")
    output = args.output.resolve()
    if output == source or output.exists():
        raise ValueError("Output must be a new path; the source and existing renders are preserved")
    if args.start < 0 or args.start >= total or (args.duration is not None and args.duration <= 0):
        raise ValueError("Invalid preview range")
    length = min(args.duration or total - args.start, total - args.start)
    output.parent.mkdir(parents=True, exist_ok=True)
    overlay = output.with_suffix(".ass")
    overlay.write_text(ass(data, args.start, length), encoding="utf-8")
    # Render SDR review media from HDR sources; the original remains the HDR master.
    color = ("zscale=w=1920:h=1080:t=linear:npl=100,format=gbrpf32le,"
             "tonemap=tonemap=mobius:param=0.3:desat=0,"
             "zscale=p=bt709:t=bt709:m=bt709,format=yuv420p," if hdr else "scale=1920:1080:flags=lanczos,")
    filters = color + "setsar=1,ass=" + overlay.name
    command = ["ffmpeg", "-nostdin", "-v", "warning", "-ss", str(args.start), "-i", str(source),
               "-t", str(length), "-vf", filters, "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
               "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)]
    with output.with_suffix(".render.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(command, cwd=output.parent, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        tail = output.with_suffix(".render.log").read_text(errors="replace").splitlines()[-8:]
        raise RuntimeError("Render failed:\n" + "\n".join(tail))
    print(f"Rendered {output} ({length:.2f}s, 1080p SDR review)")


if __name__ == "__main__":
    main()
