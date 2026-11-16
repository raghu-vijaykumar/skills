"""Check full scene/word coverage and flag quiet word onsets in an exact render."""

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageChops, ImageDraw

from compare import inspect


def tokens(text):
    return re.findall(r"[^\W_]+(?:['’\-][^\W_]+)*", text.casefold())


def read_plan(plan):
    fps, duration = plan["fps"], plan["durationFrames"]
    if type(fps) is not int or fps < 1 or type(duration) is not int or duration < 1:
        raise ValueError("Expected positive integer fps and durationFrames")
    cursor = 0
    cues = []
    for shot in plan["shots"]:
        start, end, actor = (shot[key] for key in ("startFrame", "endFrame", "asset"))
        if type(start) is not int or type(end) is not int or not cursor == start < end <= duration:
            raise ValueError(f"{actor}: use contiguous integer shot ranges")
        if not all(isinstance(shot.get(key), str) and shot[key].strip()
                   for key in ("asset", "emotion", "inventory", "script")):
            raise ValueError(f"Shot {start}: specify the asset, emotion, inventory, and script")
        actual = []
        previous = start - 1
        for word in shot["words"]:
            onset, offset = word["startFrame"], word["endFrame"]
            if type(onset) is not int or type(offset) is not int or not (
                previous < onset and start <= onset < offset <= end
            ):
                raise ValueError(f"{actor}: invalid or simultaneous onset for {word['text']!r}")
            if not all(isinstance(word.get(key), str) and word[key].strip()
                       for key in ("text", "actor", "action")):
                raise ValueError(f"{actor}: name the visible target and action for {word['text']!r}")
            actual.extend(tokens(word["text"]))
            previous = onset
            cues.append({**word, "shot": start, "shot_end": end})
        if not actual or tokens(shot["script"]) != actual:
            raise ValueError(f"{actor}: spoken words differ from the authored line")
        cursor = end
    if cursor != duration or not cues:
        raise ValueError("The shot ranges must cover the entire timeline")
    return fps, duration, cues


def crop_region(image, region):
    width, height = image.size
    l, t, r, b = region
    return image.crop((int(l * width), int(t * height), round(r * width), round(b * height)))


def changed(first, second, region):
    patch = crop_region(ImageChops.difference(first.convert("L"), second.convert("L")), region)
    return round(100 * sum(patch.histogram()[12:]) / (patch.width * patch.height), 3)


def inspect_frames(video, rows, fps, duration, region, output):
    media = inspect(video)
    if Fraction(media["fps"]) != fps:
        raise ValueError(f"Expected {fps} fps, found {media['fps']}")
    width, height = 144, 256
    pixels = width * height * 3
    refs = {}
    for row in rows:
        before = max(row["shot"], row["startFrame"] - 1)
        after = min(row["shot_end"] - 1, row["startFrame"] + 3)
        row.update(before=before, after=after)
        refs[before] = refs[after] = None
    process = subprocess.Popen([
        "ffmpeg", "-nostdin", "-v", "error", "-i", str(video), "-map", f"0:{media['stream_index']}",
        "-vf", f"scale={width}:{height}", "-an", "-pix_fmt", "rgb24", "-fps_mode", "passthrough",
        "-f", "rawvideo", "pipe:1",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    frame = 0
    while raw := process.stdout.read(pixels):
        if len(raw) != pixels:
            process.kill()
            process.communicate()
            raise ValueError("Incomplete decoded frame")
        if frame in refs:
            refs[frame] = Image.frombytes("RGB", (width, height), raw)
        frame += 1
    _rest, errors = process.communicate()
    if process.returncode or frame != duration:
        raise ValueError(f"Expected {duration} frames, decoded {frame}. {errors.decode(errors='replace')}")
    # This measures visible movement in a chosen screen region. It cannot identify the actor.
    for row in rows:
        row["region_change_percent"] = changed(refs[row["before"]], refs[row["after"]], region)
    build_sheets(rows, refs, output)
    return media


def build_sheets(rows, refs, output):
    for batch in range(0, len(rows), 24):
        group = rows[batch:batch + 24]
        page = Image.new("RGB", (1152, math.ceil(len(group) / 8) * 186), "#252131")
        draw = ImageDraw.Draw(page)
        for i, row in enumerate(group):
            x, y = i % 8 * 144, i // 8 * 186
            for side in ("before", "after"):
                frame = refs[row[side]].resize((72, 128), Image.Resampling.LANCZOS)
                page.paste(frame, (x + (72 if side == "after" else 0), y))
            draw.text((x + 3, y + 131), f"{row['startFrame']} · {row['text']}"[:23], fill="white")
            draw.text((x + 3, y + 151), f"{row['region_change_percent']:.1f}% region change", fill="#c5abdd")
        page.save(output / f"words-{batch//24+1:03}.jpg", quality=89)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--plan", required=True, type=Path)
    cli.add_argument("--out", required=True, type=Path)
    cli.add_argument("--video", type=Path)
    cli.add_argument("--region", nargs=4, type=float, default=(.06, .32, .94, .74),
                     metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    args = cli.parse_args()
    l, t, r, b = args.region
    if not (0 <= l < r <= 1 and 0 <= t < b <= 1 and r-l >= .02 and b-t >= .02):
        cli.error("use normalized LEFT TOP RIGHT BOTTOM coordinates")
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
        fps, duration, cues = read_plan(plan)
        args.out.mkdir(parents=True, exist_ok=False)
        media = inspect_frames(args.video, cues, fps, duration, args.region, args.out) if args.video else None
        evidence = {
            "fps": fps, "durationFrames": duration, "shot_count": len(plan["shots"]), "word_count": len(cues),
            "video": media, "region": args.region,
            "low_motion_onsets": sum(row.get("region_change_percent", 100) < 1 for row in cues) if media else None,
            "rows": cues,
        }
        (args.out / "word-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as error:
        cli.exit(1, f"Word cue audit failed: {error}\n")
    print(f"{len(cues)} word cues across {len(plan['shots'])} contiguous shots")


if __name__ == "__main__":
    main()
