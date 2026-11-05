"""Render reusable, source-timed motion cards over an edited video."""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path


def probe(source: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,pix_fmt,color_primaries,color_transfer,color_space:"
         "stream_side_data=side_data_type,dv_profile,rpu_present_flag",
         "-of", "json", str(source)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def validate(data: dict) -> tuple[Path, float, list[dict], dict, bool]:
    source = Path(data["source"]).resolve()
    if not source.is_file():
        raise ValueError(f"Source video does not exist: {source}")
    meta = probe(source)
    duration = float(meta["format"]["duration"])
    streams = meta.get("streams", [])
    if not any(s.get("codec_type") == "video" for s in streams):
        raise ValueError("Source needs a video stream")
    video = next(s for s in streams if s.get("codec_type") == "video")
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    events = data.get("events", [])
    if not events:
        raise ValueError("At least one event is required")
    for index, event in enumerate(events):
        start, end = float(event["start"]), float(event["end"])
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= duration + 0.02):
            raise ValueError(f"Event {index} is outside the source duration")
        if event.get("kind") not in {"ingredient", "ingredient_list", "leaves", "title", "cta", "effect"}:
            raise ValueError(f"Event {index} has an unsupported motion-graphic kind")
        if event["kind"] == "effect":
            if event.get("preset") not in {"flash", "swipe", "shutter", "speed-lines", "frame-pop"}:
                raise ValueError(f"Effect {index} has an unsupported preset")
            # Cut covers need a hold long enough to survive output-frame sampling.
            minimum = 0.30 if event["preset"] in {"flash", "swipe", "shutter"} else 0.18
            if end - start + 1e-9 < minimum:
                raise ValueError(f"Effect {index} must last at least {minimum:.2f} seconds")
            for field in ("color", "accent"):
                if field in event and not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(event[field])):
                    raise ValueError(f"Effect {index} has an invalid {field} color")
        if event["kind"] == "ingredient" and not all(event.get(key) for key in ("label", "action", "evidence")):
            raise ValueError(f"Ingredient event {index} needs label, action, and evidence")
        if event["kind"] == "title" and len(str(event.get("label", "")).split(maxsplit=1)) != 2:
            raise ValueError(f"Title event {index} needs a two-part label")
        if event["kind"] == "ingredient_list":
            items = event.get("items", [])
            if not 1 <= len(items) <= 12:
                raise ValueError(f"Ingredient list {index} needs 1–12 items")
            if any(not item.get("label") or not start <= float(item.get("at", -1)) < end for item in items):
                raise ValueError(f"Ingredient list {index} has an untimed item")
            if [float(item["at"]) for item in items] != sorted(float(item["at"]) for item in items):
                raise ValueError(f"Ingredient list {index} must be chronological")
        if event["kind"] == "leaves":
            pairs = event.get("pairs", [])
            if len(pairs) != 3 or any(not pair.get("english") or not pair.get("kannada") for pair in pairs):
                raise ValueError(f"Leaf event {index} needs three English and Kannada names")
        if event["kind"] == "cta":
            beats = event.get("beats", [{"label": "LIKE", "emoji": "👍"},
                                        {"label": "SHARE", "emoji": "📤"},
                                        {"label": "SUBSCRIBE", "emoji": "🔔"}])
            if not 1 <= len(beats) <= 3 or any(not beat.get("label") or not beat.get("emoji") for beat in beats):
                raise ValueError(f"CTA event {index} needs 1–3 labeled emoji beats")
    return source, duration, events, video, has_audio


def has_dolby_vision(video: dict) -> bool:
    return any(item.get("side_data_type") == "DOVI configuration record" and
               item.get("rpu_present_flag") == 1 for item in video.get("side_data_list", []))


def require_preview_color_decision(video: dict, allow_dv_preview: bool) -> None:
    if has_dolby_vision(video) and not allow_dv_preview:
        raise ValueError("Dolby Vision RPU cannot survive this re-encode; use sidecar for exact source color or --allow-dv-preview")


def render_command(source: Path, output: Path, overlay: Path, start: float,
                   length: float, video: dict, encoder: str, has_audio: bool = True) -> list[str]:
    # Burn the graphics into the native video signal; never tone-map or resize the footage.
    ten_bit = "10" in video.get("pix_fmt", "") or video.get("color_transfer") in {"arib-std-b67", "smpte2084"}
    pixel_format = "p010le" if ten_bit and encoder == "nvenc" else "yuv420p10le" if ten_bit else "yuv420p"
    command = ["ffmpeg", "-nostdin", "-v", "warning", "-ss", str(start), "-i", str(source),
               "-t", str(length), "-map", "0:v:0"]
    if has_audio:
        command += ["-map", "0:a:0"]
    command += ["-vf", f"ass={overlay.name},format={pixel_format}"]
    if ten_bit and encoder == "nvenc":
        command += ["-c:v", "hevc_nvenc", "-profile:v", "main10", "-preset", "p5",
                    "-rc", "vbr", "-cq", "18", "-b:v", "0"]
    elif ten_bit:
        command += ["-c:v", "libx265", "-preset", "medium", "-crf", "18"]
    else:
        command += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]
    command += ["-pix_fmt", pixel_format]
    for source_key, flag in (("color_primaries", "-color_primaries"),
                             ("color_transfer", "-color_trc"), ("color_space", "-colorspace")):
        value = video.get(source_key)
        if value and value != "unknown":
            command += [flag, value]
    if has_audio:
        command += ["-c:a", "copy"]
    return command + ["-movflags", "+faststart", str(output)]


def stamp(seconds: float) -> str:
    centis = round(seconds * 100)
    return f"{centis // 360000}:{centis // 6000 % 60:02d}:{centis // 100 % 60:02d}.{centis % 100:02d}"


def clean(value: object) -> str:
    # ASS control syntax must never come from a cue label.
    return str(value).replace("{", "(").replace("}", ")").replace("\\", "/").replace("\n", " ")


def line(layer: int, start: float, end: float, body: str) -> str:
    return f"Dialogue: {layer},{stamp(start)},{stamp(end)},Default,,0,0,0,,{body}"


def motion(x: int, y: int, entering_from: int, duration_ms: int = 250) -> str:
    return f"\\an7\\move({entering_from},{y},{x},{y},0,{duration_ms})\\fad(75,150)"


def bounce(x: int, y: int, entering_y: int, duration_ms: int = 220) -> str:
    return (f"\\an7\\move({x},{entering_y},{x},{y},0,{duration_ms})\\fad(65,140)"
            f"\\fscx82\\fscy82\\t(0,160,\\fscx110\\fscy110)"
            f"\\t(160,300,\\fscx100\\fscy100)")


def ass_color(hex_color: str) -> str:
    # ASS stores colors in blue-green-red order, unlike cue-sheet hex colors.
    return f"&H{hex_color[5:7]}{hex_color[3:5]}{hex_color[1:3]}&"


def effect_rows(event: dict, start: float, end: float, width: int, height: int) -> list[str]:
    preset = event["preset"]
    base = event.get("color", "#F6EDE0" if preset == "flash" else "#106A60")
    accent = event.get("accent", "#FFB54A")
    color, edge = ass_color(base), ass_color(accent)
    duration_ms = round((end - start) * 1000)
    close = start + (end - start) * 0.42
    release = start + (end - start) * 0.58
    close_ms = round(duration_ms * 0.42)
    release_ms = round(duration_ms * 0.58)
    rows: list[str] = []
    if preset == "flash":
        # A short opaque hold covers adjacent frames around a known hard cut.
        body = ("{\\an7\\pos(0,0)\\1c" + color + "\\alpha&HFF&"
                + f"\\t(0,{close_ms},\\alpha&H00&)\\t({release_ms},{duration_ms},\\alpha&HFF&)\\p1}}"
                + f"m 0 0 l {width} 0 l {width} {height} l 0 {height}{{\\p0}}")
        rows.append(line(8, start, end, body))
    elif preset == "swipe":
        # Arrive by 42%, hold across the cut, then leave after 58%.
        panel = f"m 0 0 l {width} 0 l {width} {height} l 0 {height}{{\\p0}}"
        rows.append(line(8, start, release, "{\\an7" + f"\\move({-width},0,0,0,0,{close_ms})"
                         + "\\1c" + color + "\\p1}" + panel))
        rows.append(line(8, release, end, "{\\an7" + f"\\move(0,0,{width},0,0,{round((end-release)*1000)})"
                         + "\\1c" + color + "\\p1}" + panel))
        stripe = max(12, round(width * 0.025))
        slim = f"m 0 0 l {stripe} 0 l {stripe} {height} l 0 {height}{{\\p0}}"
        rows.append(line(9, start, release, "{\\an7" + f"\\move({-stripe},0,{width-stripe},0,0,{close_ms})"
                         + "\\1c" + edge + "\\p1}" + slim))
        rows.append(line(9, release, end, "{\\an7" + f"\\move({width-stripe},0,{2*width-stripe},0,0,{round((end-release)*1000)})"
                         + "\\1c" + edge + "\\p1}" + slim))
    elif preset == "shutter":
        # Top and bottom halves close on the cut, then reveal the next shot.
        upper = (f"m 0 0 l {width} 0 l {width} {height // 2} l 0 {height // 2}{{\\p0}}")
        lower = (f"m 0 0 l {width} 0 l {width} {height - height // 2} l 0 {height - height // 2}{{\\p0}}")
        for a, b, from_y, to_y, shape in (
            (start, release, -height // 2, 0, upper),
            (start, release, height, height // 2, lower),
            (release, end, 0, -height // 2, upper),
            (release, end, height // 2, height, lower),
        ):
            move_ms = close_ms if a == start else round((b-a)*1000)
            rows.append(line(8, a, b, "{\\an7" + f"\\move(0,{from_y},0,{to_y},0,{move_ms})"
                             + "\\1c" + color + "\\p1}" + shape))
        seam = max(8, round(height * 0.015))
        rows.append(line(9, close, release, "{\\an7\\pos(0,0)\\1c" + edge
                         + "\\p1}" + f"m 0 {height//2-seam//2} l {width} {height//2-seam//2} l {width} {height//2+seam//2} l 0 {height//2+seam//2}{{\\p0}}"))
    elif preset == "speed-lines":
        # Offset streaks create momentum without manipulating the footage.
        strip = max(16, round(height * 0.025))
        for i in range(6):
            y = round(height * (0.14 + i * 0.14))
            a = start + i * min(0.025, (end - start) / 20)
            rows.append(line(8, a, end, "{\\an7" + f"\\move({-width//3},{y},{width + width//3},{y},0,{round((end-a)*1000)})"
                             + "\\1c" + (edge if i % 2 else color) + "\\alpha&H30&\\p1}"
                             + f"m 0 0 l {width//3} 0 l {width//3-strip*2} {strip} l {-strip*2} {strip}{{\\p0}}"))
    else:  # frame-pop
        # Four edge bars arrive from opposite sides, then fade off the frame.
        bar = max(12, round(height * 0.02))
        shapes = [
            (f"m 0 0 l {width} 0 l {width} {bar} l 0 {bar}{{\\p0}}", -width, 0, 0, 0),
            (f"m 0 0 l {width} 0 l {width} {bar} l 0 {bar}{{\\p0}}", width, height-bar, 0, height-bar),
            (f"m 0 0 l {bar} 0 l {bar} {height} l 0 {height}{{\\p0}}", 0, -height, 0, 0),
            (f"m 0 0 l {bar} 0 l {bar} {height} l 0 {height}{{\\p0}}", width-bar, height, width-bar, 0),
        ]
        arrive_ms = min(180, duration_ms // 2)
        for shape, x0, y0, x1, y1 in shapes:
            rows.append(line(8, start, end, "{\\an7" + f"\\move({x0},{y0},{x1},{y1},0,{arrive_ms})"
                             + "\\1c" + edge + "\\fad(30,180)\\p1}" + shape))
    return rows


def ass(data: dict, offset: float = 0, length: float | None = None,
        canvas: tuple[int, int] = (1920, 1080)) -> str:
    width, height = canvas
    header = f"""[Script Info]
Title: Content Studio motion graphics
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
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
        if event["kind"] == "effect":
            rows.extend(effect_rows(event, start, end, width, height))
        elif event["kind"] == "title":
            # Two words hit on separate beats against the open wall beside the presenter.
            x, y = 90, 170
            first, second = str(event["label"]).split(maxsplit=1)
            panel = "m 20 0 l 710 0 l 750 40 l 750 285 l 730 305 l 20 305 l 0 285 l 0 20 l 20 0"
            rows.append(line(0, start, end, "{" + motion(x + 8, y + 10, -842) + "\\1c&H00202C22&\\alpha&HA0&\\p1}" + panel + "{\\p0}"))
            rows.append(line(1, start, end, "{" + motion(x, y, -850) + "\\1c&H003F3F12&\\alpha&H18&\\p1}" + panel + "{\\p0}"))
            rows.append(line(2, start, end, "{" + bounce(x + 38, y + 27, y + 65) + "\\fs26\\1c&H005B70EF&}" + "OUT OF OFFICE MODE  /  COOK"))
            rows.append(line(3, start + 0.12, end, "{" + bounce(x + 38, y + 76, y + 145) + "\\fs67\\1c&H00E9F3F7&}" + clean(first).upper()))
            rows.append(line(4, start + 0.34, end, "{" + bounce(x + 34, y + 138, y + 238) + "\\fs124\\1c&H006BD6FF&}" + clean(second).upper()))
            rows.append(line(4, start + 0.72, end, "{" + bounce(x + 42, y + 253, y + 300) + "\\fnNirmala UI\\fs43\\1c&H00E9F3F7&}" + clean(event.get("kannada", ""))))
        elif event["kind"] == "ingredient_list":
            # Each chip is a continuing list item, so earlier ingredients stay on screen.
            x, y = 46, 787
            upper = "m 18 0 l 1810 0 l 1828 18 l 1828 121 l 1810 139 l 18 139 l 0 121 l 0 18 l 18 0"
            lower = "m 18 0 l 1810 0 l 1828 18 l 1828 71 l 1810 89 l 18 89 l 0 71 l 0 18 l 18 0"
            rows.append(line(0, start, end, "{" + motion(x, y, -1850) + "\\1c&H003F3F12&\\alpha&H34&\\p1}" + upper + "{\\p0}"))
            rows.append(line(1, start, end, "{" + motion(x + 24, y + 15, -1826) + "\\fs33\\1c&H006BD6FF&}" + "INGREDIENTS  /  ONE BY ONE"))
            items = event["items"]
            if len(items) > 6:
                lower_start = max(0, float(items[6]["at"]) - offset)
                if lower_start < end:
                    rows.append(line(0, lower_start, end, "{" + motion(x, 919, -1850) + "\\1c&H003F3F12&\\alpha&H34&\\p1}" + lower + "{\\p0}"))
            for item_index, item in enumerate(items):
                item_start = max(0, float(item["at"]) - offset)
                if item_start >= end:
                    continue
                cx, cy = 73 + (item_index % 6) * 294, 851 + (item_index // 6) * 75
                chip = "m 11 0 l 260 0 b 270 0 276 7 276 17 l 276 48 b 276 58 270 64 260 64 l 11 64 b 3 64 0 58 0 48 l 0 17 b 0 7 3 0 11 0"
                rows.append(line(1, item_start, end, "{" + bounce(cx, cy, cy + 30) + "\\1c&H006BD6FF&\\t(0,360,\\1c&H00E9F3F7&)\\alpha&H08&\\p1}" + chip + "{\\p0}"))
                english_y = cy + (5 if item.get("kannada") else 12)
                rows.append(line(2, item_start, end, "{" + bounce(cx + 15, english_y, english_y + 30) + "\\fs29\\1c&H005B70EF&\\t(0,330,\\1c&H002D3020&)}" + clean(item["label"])))
                if item.get("kannada"):
                    rows.append(line(2, item_start + 0.10, end, "{" + bounce(cx + 15, cy + 35, cy + 55) + "\\fnNirmala UI\\fs24\\1c&H00686A17&}" + clean(item["kannada"])))
                hero_end = min(end, item_start + 0.92)
                rows.append(line(3, item_start, hero_end, "{" + bounce(82, 683, 766) + "\\fs86\\1c&H006BD6FF&\\bord2\\3c&H003F3F12&}" + clean(item["label"]).upper()))
                next_at = float(items[item_index + 1]["at"]) - offset if item_index + 1 < len(items) else end
                counter_end = min(end, next_at)
                if counter_end > item_start:
                    rows.append(line(2, item_start, counter_end, "{\\an7\\pos(1740,805)\\fs31\\1c&H006BD6FF&}" + f"{item_index + 1:02d} / {len(items):02d}"))
        elif event["kind"] == "leaves":
            # The same text position cycles through three English/Kannada leaf names.
            x, y = 72, 92
            panel = "m 18 0 l 725 0 l 745 20 l 745 305 l 725 325 l 18 325 l 0 305 l 0 18 l 18 0"
            rows.append(line(0, start, end, "{" + motion(x, y, -760) + "\\1c&H003F3F12&\\alpha&H1C&\\p1}" + panel + "{\\p0}"))
            rows.append(line(1, start, end, "{" + motion(x + 36, y + 27, -724) + "\\fs28\\1c&H006BD6FF&}" + "THREE FRESH LEAVES  🌿"))
            span = (float(event["end"]) - float(event["start"])) / 3
            for leaf_index, pair in enumerate(event["pairs"]):
                a = max(0, float(event["start"]) - offset + leaf_index * span)
                b = min(end, float(event["start"]) - offset + (leaf_index + 1) * span)
                if b - a < 0.1:
                    continue
                rows.append(line(2, a, b, "{" + bounce(x + 38, y + 93, y + 165) + "\\fs78\\1c&H00E9F3F7&}" + clean(pair["english"]).upper()))
                rows.append(line(3, a + 0.12, b, "{" + bounce(x + 41, y + 207, y + 272) + "\\fnNirmala UI\\fs48\\1c&H006BD6FF&}" + clean(pair["kannada"])))
                rows.append(line(2, a, b, "{\\an7\\pos(690,125)\\fs26\\1c&H005B70EF&}" + f"0{leaf_index + 1} / 03"))
        elif event["kind"] == "ingredient":
            # Cream recipe cards, teal ink, and coral/yellow details borrow from the channel intro.
            x, y = 72, 82
            card = "m 18 0 l 610 0 b 626 0 636 10 636 26 l 636 106 b 636 120 626 130 610 130 l 18 130 b 5 130 0 120 0 106 l 0 22 b 0 10 5 0 18 0"
            rows.append(line(0, start, end, "{" + motion(x + 7, y + 9, -643) + "\\1c&H002B4A39&\\alpha&HB0&\\p1}" + card + "{\\p0}"))
            rows.append(line(1, start, end, "{" + motion(x, y, -650) + "\\1c&H00E9F3F7&\\alpha&H08&\\p1}" + card + "{\\p0}"))
            rows.append(line(2, start, end, "{" + motion(x, y + 117, -650) + "\\1c&H00686A17&\\p1}m 18 0 l 610 0 l 610 5 l 18 5{\\p0}"))
            rows.append(line(3, start, end, "{" + motion(x + 30, y + 17, -620) + "\\fs25\\1c&H005B70EF&}" + clean(event["action"]).upper()))
            rows.append(line(4, start, end, "{" + motion(x + 30, y + 57, -620) + "\\fs49\\1c&H002D3020&\\fscx86\\fscy86\\t(0,170,\\fscx110\\fscy110)\\t(170,300,\\fscx100\\fscy100)}" + clean(event["label"])))
            rows.append(line(3, start, end, "{" + motion(x + 554, y + 17, -96) + "\\fs28\\1c&H005B70EF&}" + f"{index:02d} →"))
        else:
            # Emoji-led prompts arrive on three beats and remain reusable through cue data.
            beats = event.get("beats", [{"label": "LIKE", "emoji": "👍"},
                                        {"label": "SHARE", "emoji": "📤"},
                                        {"label": "SUBSCRIBE", "emoji": "🔔"}])
            for beat, item in enumerate(beats):
                a = max(0, float(event["start"]) - offset + beat * 1.12)
                if a >= end:
                    break
                x, y = 1260, 104 + beat * 112
                card = "m 16 0 l 584 0 b 600 0 610 10 610 26 l 610 70 b 610 86 600 96 584 96 l 16 96 b 4 96 0 86 0 70 l 0 26 b 0 10 4 0 16 0"
                fill = ["&H00E9F3F7&", "&H00DDE9BD&", "&H006BD6FF&"][beat % 3]
                rows.append(line(0, a, end, "{" + motion(x + 7, y + 8, 1977) + "\\1c&H002B4A39&\\alpha&HB0&\\p1}" + card + "{\\p0}"))
                rows.append(line(1, a, end, "{" + motion(x, y, 1970) + f"\\1c{fill}\\alpha&H04&\\p1}}" + card + "{\\p0}"))
                rows.append(line(2, a, end, "{" + bounce(x + 30, y + 8, y + 60) + "\\fnSegoe UI Emoji\\fs71\\1c&H005B70EF&\\frz-12\\t(0,260,\\frz0)}" + clean(item["emoji"])))
                rows.append(line(3, a + 0.08, end, "{" + bounce(x + 145, y + 21, y + 75) + "\\fs55\\1c&H003F3F12&}" + clean(item["label"]).upper()))
            rows.append(line(1, start, end, "{" + motion(1260, 50, 1970) + "\\1c&H0063CFFF&\\alpha&H06&\\p1}m 14 0 l 596 0 l 610 12 l 610 38 l 0 38 l 0 12 l 14 0{\\p0}"))
            rows.append(line(2, start, end, "{" + motion(1282, 57, 1992) + "\\fs26\\1c&H003F3F12&}" + clean(event.get("brand", "OUT OF OFFICE MODE  /  COOK"))))
    return "\n".join(rows) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "sidecar", "render"])
    parser.add_argument("cues", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--encoder", choices=["auto", "nvenc", "x265"], default="auto",
                        help="10-bit video encoder; auto tries NVENC then x265")
    parser.add_argument("--allow-dv-preview", action="store_true",
                        help="permit a combined HLG-base preview that cannot retain Dolby Vision RPU")
    args = parser.parse_args()
    data = json.loads(args.cues.read_text(encoding="utf-8"))
    source, total, events, video, has_audio = validate(data)
    if args.command == "validate":
        dv = ", Dolby Vision RPU present" if has_dolby_vision(video) else ""
        print(f"Valid: {len(events)} cues, {total:.2f}s source, {video.get('color_transfer', 'unknown')} transfer{dv}")
        return
    if not args.output:
        parser.error(f"{args.command} requires --output")
    output = args.output.resolve()
    if output == source or output.exists():
        raise ValueError("Output must be a new path; the source and existing renders are preserved")
    if args.start < 0 or args.start >= total or (args.duration is not None and args.duration <= 0):
        raise ValueError("Invalid preview range")
    length = min(args.duration or total - args.start, total - args.start)
    output.parent.mkdir(parents=True, exist_ok=True)
    dimensions = (int(video.get("width") or 1920), int(video.get("height") or 1080))
    canvas = (round(1080 * dimensions[0] / dimensions[1]), 1080)
    if args.command == "sidecar":
        if output.suffix.lower() != ".ass":
            raise ValueError("Sidecar output needs an .ass extension")
        output.write_text(ass(data, args.start, length, canvas), encoding="utf-8")
        print(f"Wrote {output} (original video remains bit-for-bit untouched)")
        return
    require_preview_color_decision(video, args.allow_dv_preview)
    overlay = output.with_suffix(".ass")
    overlay.write_text(ass(data, args.start, length, canvas), encoding="utf-8")
    ten_bit = "10" in video.get("pix_fmt", "") or video.get("color_transfer") in {"arib-std-b67", "smpte2084"}
    encoders = (["nvenc", "x265"] if args.encoder == "auto" and ten_bit
                else [args.encoder if ten_bit else "x264"])
    log_path = output.with_suffix(".render.log")
    for attempt, encoder in enumerate(encoders):
        command = render_command(source, output, overlay, args.start, length, video, encoder, has_audio)
        with log_path.open("a" if attempt else "w", encoding="utf-8") as log:
            result = subprocess.run(command, cwd=output.parent, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode == 0:
            break
        # Only a partial file created by this invocation can be removed for a fallback retry.
        output.unlink(missing_ok=True)
    if result.returncode:
        tail = log_path.read_text(errors="replace").splitlines()[-8:]
        raise RuntimeError("Render failed:\n" + "\n".join(tail))
    color_note = "HLG base-layer preview; Dolby Vision RPU omitted" if has_dolby_vision(video) else "source color format retained"
    print(f"Rendered {output} ({length:.2f}s, {video.get('width')}x{video.get('height')}, {color_note})")


if __name__ == "__main__":
    main()
