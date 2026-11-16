"""Survey a source end to end and seed a reconstruction inventory before authoring."""

import argparse
import json
import math
from pathlib import Path
import subprocess

from PIL import Image, ImageChops, ImageDraw

from compare import inspect, scan_cut_candidates
from frame_trace import motion_pixels, parse_region


def windows(duration, cuts, maximum):
    boundaries = [0.0]
    for item in cuts:
        at = item["seconds"]
        if at - boundaries[-1] >= 0.4 and at < duration - 0.2:
            boundaries.append(at)
    boundaries.append(duration)
    for start, end in zip(boundaries, boundaries[1:]):
        for index in range(max(1, math.ceil((end - start) / maximum - 1e-9))):
            yield start + index * maximum, min(end, start + (index + 1) * maximum)


def sheet(samples, roles, output):
    if not samples:
        return {}
    # Keep representative motion from each region plus the entering/settled state.
    picks = {0, len(samples) - 1, len(samples) // 2}
    peaks = {}
    for role in roles:
        best = max(range(len(samples)), key=lambda i: samples[i][2][role])
        picks.add(best)
        peaks[role] = {"seconds": samples[best][0], "change_percent": samples[best][2][role]}
    page = Image.new("RGB", (192 * len(picks), 218), "#262333")
    draw = ImageDraw.Draw(page)
    for column, index in enumerate(sorted(picks)):
        when, picture, _scores = samples[index]
        x = 192 * column
        page.paste(picture.resize((192, 192), Image.Resampling.LANCZOS), (x, 0))
        draw.text((x + 7, 196), f"{when:.3f} s", fill="white")
    page.save(output, quality=90)
    return peaks


def build(video, output, regions, maximum, threshold):
    source = inspect(video)
    cuts = scan_cut_candidates(video, source["stream_index"], threshold)
    spans = list(windows(source["video_seconds"], cuts, maximum))
    output.mkdir(parents=True, exist_ok=False)
    rate, size = 8, 256
    command = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(video),
               "-map", f"0:{source['stream_index']}", "-an", "-vf",
               f"fps={rate},scale={size}:{size}:force_original_aspect_ratio=decrease,"
               f"pad={size}:{size}:(ow-iw)/2:(oh-ih)/2",
               "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
    rows = []
    with subprocess.Popen(command, stdout=subprocess.PIPE) as frames:
        cursor = 0
        samples = []
        last = None
        number = 0

        def close_window():
            filename = f"shot-{len(rows) + 1:03}.jpg"
            motion = sheet(samples, regions, output / filename)
            rows.append({
                "reference": spans[cursor],
                "sheet": filename if samples else None,
                "motion_peaks": motion,
                "observations": {"actors": [], "actions": [], "expression": None,
                                 "camera": None, "transition": None, "sound": None},
            })

        while raw := frames.stdout.read(size * size * 3):
            picture = Image.frombytes("RGB", (size, size), raw)
            luma = picture.convert("L")
            when = number / rate
            while cursor < len(spans) and when >= spans[cursor][1]:
                close_window()
                cursor += 1
                samples = []
            if cursor < len(spans):
                delta = ImageChops.difference(last, luma) if last is not None else None
                scores = {role: motion_pixels(delta, bounds) if delta is not None else 0
                          for role, bounds in regions.items()}
                samples.append((round(when, 3), picture, scores))
            last = luma
            number += 1
        if frames.wait() != 0:
            raise ValueError("Reference frame decode failed")
        while cursor < len(spans):
            close_window()
            cursor += 1
            samples = []
    result = {"reference": source, "inspection_fps": rate, "cut_candidates": cuts,
              "regions": regions, "windows": rows}
    (output / "source-inventory.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return rows


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--reference", required=True, type=Path)
    cli.add_argument("--out", required=True, type=Path)
    cli.add_argument("--max-window", type=float, default=8, metavar="SECONDS")
    cli.add_argument("--cut-threshold", type=float, default=0.22)
    cli.add_argument("--region", action="append", type=parse_region, default=[])
    args = cli.parse_args()
    if not 1 <= args.max_window <= 15 or not 0 < args.cut_threshold < 1:
        cli.error("use a maximum window from 1 to 15 seconds and a cut threshold between 0 and 1")
    try:
        rows = build(args.reference.resolve(), args.out.resolve(),
                     {"full": (0, 0, 1, 1), **dict(args.region)}, args.max_window, args.cut_threshold)
    except (OSError, ValueError, KeyError) as error:
        cli.exit(1, f"Reference survey failed: {error}\n")
    print(f"{len(rows)} reference windows in {args.out}")


if __name__ == "__main__":
    main()
