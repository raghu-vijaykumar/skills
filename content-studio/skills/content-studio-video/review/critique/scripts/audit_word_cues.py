"""Check full scene/word coverage and flag quiet word onsets in an exact render."""

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageChops, ImageDraw

from compare import inspect


VISIBLE_CUE_KINDS = {"object", "character", "continuation", "editorial"}


def tokens(text):
    return re.findall(r"[^\W_]+(?:['’\-][^\W_]+)*", text.casefold())


def read_plan(plan):
    fps, duration = plan["fps"], plan["durationFrames"]
    rapid_take = plan.get("style") == "rapid-take"
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
            word_tokens = tokens(word["text"])
            if rapid_take:
                if len(word_tokens) != 1:
                    raise ValueError(f"{actor}: use one spoken word per Rapid Take cue for {word['text']!r}")
                kind = word.get("cueKind")
                if not isinstance(kind, str) or kind not in VISIBLE_CUE_KINDS:
                    kinds = ", ".join(sorted(VISIBLE_CUE_KINDS))
                    raise ValueError(f"{actor}: Rapid Take word {word['text']!r} needs a cueKind ({kinds})")
            actual.extend(word_tokens)
            previous = onset
            cues.append({**word, "shot": start, "shot_end": end})
        if not actual or tokens(shot["script"]) != actual:
            raise ValueError(f"{actor}: spoken words differ from the authored line")
        cursor = end
    if cursor != duration or not cues:
        raise ValueError("The shot ranges must cover the entire timeline")
    return fps, duration, cues


def cue_signature(fps, duration, cues):
    # Include the paint-independent word clock and bindings, with scene cuts.
    fields = ("shot", "shot_end", "startFrame", "endFrame", "text", "line", "actor", "action", "cueKind")
    rows = [[cue.get(field) for field in fields] for cue in cues]
    clock = json.dumps([fps, duration, rows], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(clock.encode("utf-8")).hexdigest()


def valid_region(bounds):
    if not isinstance(bounds, (list, tuple)) or len(bounds) != 4 or not all(
            type(value) in (int, float) and math.isfinite(value) for value in bounds):
        return False
    left, top, right, bottom = bounds
    return 0 <= left < right <= 1 and 0 <= top < bottom <= 1 and right-left >= .02 and bottom-top >= .02


def read_targets(manifest, cues):
    entries = manifest.get("targets") if isinstance(manifest, dict) else None
    if not isinstance(entries, list) or not entries:
        raise ValueError("Expected a nonempty targets list")
    onsets = {cue["startFrame"] for cue in cues}
    targets = {}
    for entry in entries:
        frame = entry.get("frame") if isinstance(entry, dict) else None
        if type(frame) is not int or frame not in onsets or frame in targets:
            raise ValueError(f"Expected a unique word onset frame, got {frame!r}")
        bounds = entry.get("region")
        if not valid_region(bounds):
            raise ValueError(f"Invalid target region at word onset {frame}")
        targets[frame] = bounds
    return targets


def crop_region(image, region):
    width, height = image.size
    l, t, r, b = region
    left, top = int(l * width), int(t * height)
    return image.crop((left, top, max(left + 1, round(r * width)), max(top + 1, round(b * height))))


def changed(first, second, region, *, color=False):
    if color:
        # A vivid hue can change without changing the luma. Count that pixel once.
        red, green, blue = ImageChops.difference(first, second).split()
        diff = ImageChops.lighter(red, ImageChops.lighter(green, blue))
    else:
        diff = ImageChops.difference(first.convert("L"), second.convert("L"))
    patch = crop_region(diff, region)
    return round(100 * sum(patch.histogram()[12:]) / (patch.width * patch.height), 3)


def inspect_frames(video, rows, fps, duration, region, output, *, color=False, targets=None):
    media = inspect(video)
    if Fraction(media["fps"]) != fps:
        raise ValueError(f"Expected {fps} fps, found {media['fps']}")
    scale = 256 / max(media["width"], media["height"])
    width, height = (max(1, round(media[key] * scale)) for key in ("width", "height"))
    pixels = width * height * 3
    refs = {}
    for index, row in enumerate(rows):
        before = max(row["shot"], row["startFrame"] - 1)
        limit = min(row["shot_end"], row["startFrame"] + 4)
        if index + 1 < len(rows):
            limit = min(limit, rows[index + 1]["startFrame"])
        row.update(before=before, inspection_end=limit - 1)
        refs[before] = None
        for frame in range(row["startFrame"], limit):
            refs[frame] = None
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
    def strongest(row, bounds):
        before = refs[row["before"]]
        return max(((at, changed(before, refs[at], bounds, color=color))
                    for at in range(row["startFrame"], row["inspection_end"] + 1)),
                   key=lambda result: result[1])

    focused = []
    target_regions = targets or {}
    for row in rows:
        # The target may peak on a different frame than the overall shot.
        at, score = strongest(row, region)
        row.update(after=at, region_change_percent=score)
        bounds = target_regions.get(row["startFrame"])
        if bounds is not None:
            at, score = strongest(row, bounds)
            row.update(target_region=bounds, target_after=at, target_change_percent=score)
            focused.append(row)
    build_sheets(rows, refs, output)
    build_sheets(focused, refs, output, targeted=True)
    return media


def build_sheets(rows, refs, output, *, targeted=False):
    prefix = "targets" if targeted else "words"
    after = "target_after" if targeted else "after"
    field = "target_change_percent" if targeted else "region_change_percent"
    for batch in range(0, len(rows), 24):
        group = rows[batch:batch + 24]
        page = Image.new("RGB", (1152, math.ceil(len(group) / 8) * 186), "#252131")
        draw = ImageDraw.Draw(page)
        for i, row in enumerate(group):
            x, y = i % 8 * 144, i // 8 * 186
            for side in ("before", after):
                frame = refs[row[side]].copy()
                if targeted:
                    frame = crop_region(frame, row["target_region"])
                frame.thumbnail((72, 128), Image.Resampling.LANCZOS)
                left = x + (72 if side == after else 0) + (72 - frame.width) // 2
                page.paste(frame, (left, y + (128 - frame.height) // 2))
            draw.text((x + 3, y + 131), f"{row['startFrame']} · {row['text']}"[:23], fill="white")
            draw.text((x + 3, y + 151), f"{row[field]:.1f}% region change", fill="#c5abdd")
        page.save(output / f"{prefix}-{batch//24+1:03}.jpg", quality=89)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--plan", required=True, type=Path)
    cli.add_argument("--out", required=True, type=Path)
    cli.add_argument("--video", type=Path)
    cli.add_argument("--target-regions", type=Path, help="independent actor regions for selected word onsets")
    cli.add_argument("--same-cues-as", type=Path, help="check only the word clock and actor/action bindings against another plan")
    cli.add_argument("--region", nargs=4, type=float, default=(.06, .32, .94, .74),
                     metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    args = cli.parse_args()
    if not valid_region(args.region):
        cli.error("use normalized LEFT TOP RIGHT BOTTOM coordinates")
    if args.target_regions and not args.video:
        cli.error("--target-regions requires --video")
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
        fps, duration, cues = read_plan(plan)
        targets = (read_targets(json.loads(args.target_regions.read_text(encoding="utf-8-sig")), cues)
                   if args.target_regions else {})
        signature = cue_signature(fps, duration, cues)
        if args.same_cues_as:
            baseline = json.loads(args.same_cues_as.read_text(encoding="utf-8-sig"))
            if signature != cue_signature(*read_plan(baseline)):
                raise ValueError("The word clock or actor/action bindings differ from the baseline plan")
        args.out.mkdir(parents=True, exist_ok=False)
        rapid_take = plan.get("style") == "rapid-take"
        media = (inspect_frames(args.video, cues, fps, duration, args.region, args.out, color=rapid_take, targets=targets)
                 if args.video else None)
        evidence = {
            "fps": fps, "durationFrames": duration, "shot_count": len(plan["shots"]), "word_count": len(cues),
            "cue_sha256": signature,
            "video": media, "region": args.region,
            "change_basis": ("rgb-channel" if rapid_take else "luma") if media else None,
            "low_motion_onsets": sum(row.get("region_change_percent", 100) < 1 for row in cues) if media else None,
            "rows": cues,
        }
        if isinstance(plan.get("artPreset"), str):
            evidence["artPreset"] = plan["artPreset"]
        if targets:
            evidence["targeted_onsets"] = len(targets)
            evidence["low_target_motion_onsets"] = sum(row["target_change_percent"] < 1 for row in cues
                                                       if "target_change_percent" in row)
        if rapid_take:
            evidence["style"] = "rapid-take"
            evidence["cue_counts"] = {kind: sum(cue["cueKind"] == kind for cue in cues)
                                      for kind in sorted(VISIBLE_CUE_KINDS)}
        (args.out / "word-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as error:
        cli.exit(1, f"Word cue audit failed: {error}\n")
    print(f"{len(cues)} word cues across {len(plan['shots'])} contiguous shots")


if __name__ == "__main__":
    main()
