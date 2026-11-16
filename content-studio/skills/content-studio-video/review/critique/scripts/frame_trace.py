"""Index every decoded picture in one mapped narrative beat."""

import argparse
import csv
import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageChops, ImageDraw, ImageOps

from compare import inspect, validate_map


def parse_region(value):
    name, colon, coordinates = value.partition(":")
    try:
        x0, y0, x1, y1 = map(float, coordinates.split(","))
        reserved = {"frame", "time", "image", "full"}
        if (colon and name not in reserved and re.fullmatch(r"[a-z][a-z0-9-]*", name)
                and 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            return name, (x0, y0, x1, y1)
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("use name:x0,y0,x1,y1 with normalized coordinates from 0 to 1")


def decode(file, stream, start, end, folder):
    folder.mkdir()
    # Keep the input clock while seeking. No fps filter is allowed here: a VFR
    # shot must retain each actual picture and its display timestamp.
    seek = max(0, start - 0.25)
    # Input seeking can return an adjacent frame on fractional boundaries.
    # Give the decoder a small margin and enforce the half-open range on PTS.
    bounds = f"select='gte(t,{start:.9f})*lt(t,{end:.9f})'"
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "info",
               "-copyts", "-start_at_zero", "-ss", str(seek), "-t", str(end-seek+0.25),
               "-i", str(file), "-map", f"0:{stream}", "-an",
               "-vf", f"{bounds},showinfo,scale=360:640:force_original_aspect_ratio=decrease:force_divisible_by=2",
               "-fps_mode", "passthrough", "-q:v", "2", str(folder / "%06d.jpg")]
    result = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise ValueError("\n".join(result.stderr.splitlines()[-8:]))
    # showinfo prints the floating point display timestamp as well as the
    # underlying integer PTS. Use the latter to preserve fractional frame times.
    base = re.search(r"config in time_base:\s*(\d+)/(\d+)", result.stderr)
    timestamps = re.findall(r"\bn:\s*\d+\s+pts:\s*(-?\d+)\s+pts_time:", result.stderr)
    files = sorted(folder.glob("*.jpg"))
    if not base or not files or len(timestamps) != len(files):
        raise ValueError(f"Cannot reconcile decoded frames and timestamps for {file.name}")
    step = int(base.group(1)) / int(base.group(2))
    pairs = list(zip(files, (int(t) * step for t in timestamps)))
    if any(t < start - 1e-6 or t >= end + 1e-6 for _, t in pairs):
        raise ValueError(f"Decoded timestamps fall outside the requested range for {file.name}")
    return pairs


def motion_pixels(difference, region):
    # Report the percentage of luma pixels that changed by at least 16/255.
    # Camera moves and lighting can also raise the number.
    width, height = difference.size
    x0, y0, x1, y1 = region
    left, top = int(x0 * width), int(y0 * height)
    right = min(width, max(left + 1, round(x1 * width)))
    bottom = min(height, max(top + 1, round(y1 * height)))
    patch = difference.crop((left, top, right, bottom))
    return round(100 * sum(patch.histogram()[16:]) / (patch.width * patch.height), 3)


def index_frames(pairs, root, lane, regions):
    rows = []
    previous = None
    for number, (file, time) in enumerate(pairs):
        with Image.open(file) as frame:
            luma = frame.convert("L")
        delta = ImageChops.difference(previous, luma) if previous is not None else None
        rows.append({"frame": number, "time": round(time, 6), "image": file.relative_to(root).as_posix(),
                     **{name: motion_pixels(delta, bounds) if delta is not None else None
                        for name, bounds in regions.items()}})
        previous = luma
    with (root / f"{lane}.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def consecutive_sheets(rows, root, lane):
    # Each tile is a consecutive frame, including holds and tiny in-betweens.
    # The HTML viewer provides larger inspection of an individual picture.
    for start in range(0, len(rows), 30):
        page = rows[start:start+30]
        sheet = Image.new("RGB", (1140, 3*210), "#1b1d24")
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(page):
            x, y = index % 10 * 114, index // 10 * 210
            with Image.open(root / row["image"]) as source:
                image = ImageOps.contain(source.convert("RGB"), (112, 186))
                sheet.paste(image, (x+(114-image.width)//2, y))
            draw.text((x+3, y+189), f"{row['frame']:03d} / {row['time']:.3f}s", fill="white")
        sheet.save(root / f"{lane}-{start//30:02d}.jpg", quality=91)


def viewer(root, lanes):
    template = Path(__file__).with_name("frame-viewer.html").read_text(encoding="utf-8")
    # Only generated relative names and numeric timestamps enter this literal.
    frames = {name: [{key: row[key] for key in ("frame", "time", "image")} for row in rows]
              for name, rows in lanes.items()}
    (root / "frames.html").write_text(template.replace("/* FRAME_DATA */", json.dumps(frames)), encoding="utf-8")


def build(reference, candidate, mapping, beat, output, regions):
    files = {"reference": reference, "candidate": candidate}
    meta = {lane: inspect(file) for lane, file in files.items()}
    rows = validate_map(mapping, *[meta[lane]["video_seconds"] for lane in files])
    row = next((row for row in rows if row["id"] == beat and row["candidate"] is not None), None)
    if row is None:
        raise ValueError(f"Expected a paired beat in the map: {beat}")
    output.mkdir(parents=True, exist_ok=False)
    lanes = {}
    for lane, file in files.items():
        pairs = decode(file, meta[lane]["stream_index"], *row[lane], output / lane)
        lanes[lane] = index_frames(pairs, output, lane, regions)
        consecutive_sheets(lanes[lane], output, lane)
    viewer(output, lanes)
    manifest = {"schema_version": 1, "beat": row, "regions": regions,
                "inputs": meta, "decoded_frames": {lane: len(frames) for lane, frames in lanes.items()}}
    (output / "frame-trace.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest["decoded_frames"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("reference", "candidate", "map", "out"):
        parser.add_argument("--"+flag, required=True, type=Path)
    parser.add_argument("--beat", required=True)
    parser.add_argument("--region", action="append", type=parse_region, default=[])
    args = parser.parse_args()
    regions = {"full": (0, 0, 1, 1), **dict(args.region)}
    try:
        counts = build(args.reference.resolve(), args.candidate.resolve(),
                       json.loads(args.map.read_text(encoding="utf-8-sig")), args.beat, args.out.resolve(), regions)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Frame trace failed: {error}\n")
    print(f"{args.beat}: {counts['reference']} reference frames, {counts['candidate']} candidate frames")


if __name__ == "__main__":
    main()
