"""Index every decoded picture in one mapped narrative beat."""

import argparse
import csv
import json
import math
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageChops, ImageDraw, ImageOps

from compare import inspect, validate_map, validate_span
from compare_actor import parse_box


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


def decode(file, stream, start, end, folder, *, detail=None):
    folder.mkdir()
    # Keep the input clock while seeking. No fps filter is allowed here: a VFR
    # shot must retain each actual picture and its display timestamp.
    seek = max(0, start - 0.25)
    # Input seeking can return an adjacent frame on fractional boundaries.
    # Give the decoder a small margin and enforce the half-open range on PTS.
    bounds = f"select='gte(t,{start:.9f})*lt(t,{end:.9f})'"
    filters = [bounds, "showinfo"]
    if detail:
        left, top, right, bottom = detail
        filters.append(f"crop={right-left}:{bottom-top}:{left}:{top}:exact=1")
    filters.append("scale=360:640:force_original_aspect_ratio=decrease:force_divisible_by=2")
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "info",
               "-copyts", "-start_at_zero", "-ss", str(seek), "-t", str(end-seek+0.25),
               "-i", str(file), "-map", f"0:{stream}", "-an",
               "-vf", ",".join(filters),
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


def lane_names(row):
    return ("reference", "previous", "candidate") if "previous" in row else ("reference", "candidate")


def lane_description(lanes):
    return f"{', '.join(lanes[:-1])} and {lanes[-1]}"


def paired_times(row, beats, label, *, allow_start=False):
    lanes = lane_names(row)
    if not isinstance(beats, dict) or set(beats) != set(lanes):
        raise ValueError(f"{label} needs separate {lane_description(lanes)} times")
    for lane, time in beats.items():
        start, end = row[lane]
        if (type(time) not in (int, float) or not math.isfinite(time)
                or not (start <= time < end if allow_start else start < time < end)):
            if allow_start:
                raise ValueError(f"{lane} {label} must be inside its mapped half-open range")
            raise ValueError(f"{lane} {label} must be strictly within its mapped range")
    return beats


def seam_times(row):
    return paired_times(row, row["seam"], "seam") if "seam" in row else None


def named_entries(row, key, label):
    entries = row.get(key, [])
    if not isinstance(entries, list):
        raise ValueError(f"{key} must be a list of named {label} entries")
    anchors = {}
    for item in entries:
        name = item.get("id") if isinstance(item, dict) else None
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,47}", name) or name in anchors:
            raise ValueError(f"Invalid or duplicate {label} ID: {name!r}")
        anchors[name] = {lane: time for lane, time in item.items() if lane != "id"}
    return anchors


def landmark_times(row):
    return {name: paired_times(row, times, f"landmark {name}")
            for name, times in named_entries(row, "landmarks", "landmark").items()}


def word_anchor_times(row, landmarks):
    anchors = named_entries(row, "word_anchors", "word anchor")
    for name in anchors:
        if name not in landmarks:
            raise ValueError(f"Word anchor {name} needs a matching landmark")
    return {name: paired_times(row, times, f"word anchor {name}", allow_start=True)
            for name, times in anchors.items()}


def hold_ranges(row):
    ranges = named_entries(row, "holds", "hold")
    expected = lane_names(row)
    for name, lanes in ranges.items():
        if set(lanes) != set(expected):
            raise ValueError(f"Hold {name} needs separate {lane_description(expected)} ranges")
        for lane, interval in lanes.items():
            start, end = row[lane]
            if (not isinstance(interval, list) or len(interval) != 2
                    or not all(type(t) in (int, float) and math.isfinite(t) for t in interval)
                    or not start <= interval[0] < interval[1] <= end):
                raise ValueError(f"{lane} hold {name} needs a finite increasing range inside its mapped range")
    return ranges


def hold_pictures(lane, name, interval, pictures, rows):
    start, end = interval
    # Keep a half-open PTS range even when the two cuts run at different rates.
    inside = [(i, t) for i, (_, t) in enumerate(pictures) if start - 1e-9 <= t < end - 1e-9]
    if not inside:
        raise ValueError(f"No decoded picture in {lane} hold {name}; widen the hold range")
    midpoint = (start + end) / 2
    middle, _ = min(inside, key=lambda entry: abs(entry[1] - midpoint))
    return {"seconds": interval, "duration_seconds": round(end - start, 6), "decoded_frames": len(inside),
            "first": rows[inside[0][0]], "middle": rows[middle], "last": rows[inside[-1][0]]}


def seam_pictures(lane, anchor, pictures, rows, label="seam", word_onset=None):
    # Compare the source PTS with the anchor before rounding for display.
    cut = next((i for i, (_, time) in enumerate(pictures) if time >= anchor - 1e-9), 0)
    if cut < 1:
        raise ValueError(f"Widen the {lane} range to include decoded frames on both sides of {label}")
    result = {"seconds": anchor, "before": rows[cut - 1], "after": rows[cut]}
    if word_onset is not None:
        # Measure from the supplied speech clock to the exact displayed picture PTS.
        result["word_onset_seconds"] = word_onset
        result["word_to_picture_ms"] = round((pictures[cut][1] - word_onset) * 1000, 1)
    return result


def detail_boxes(row, meta):
    if "details" not in row:
        return {}
    boxes = row["details"]
    if not isinstance(boxes, dict) or set(boxes) != set(meta):
        raise ValueError(f"Details need separate {lane_description(tuple(meta))} boxes")
    return {lane: parse_box(box, meta[lane]["width"], meta[lane]["height"]) for lane, box in boxes.items()}


def comparison_sheet(root, lanes, filename, moments, *, detail=False):
    sheet = Image.new("RGB", (407 * len(moments), 651 * len(lanes)), "#1b1d24")
    draw = ImageDraw.Draw(sheet)
    for y, (lane, frames) in enumerate(lanes.items()):
        for x, key in enumerate(moments):
            frame = frames[key]
            xx, yy = 407 * x, 651 * y
            source_path = f"{lane}-detail/{frame['frame'] + 1:06}.jpg" if detail else frame["image"]
            with Image.open(root / source_path) as source:
                picture = ImageOps.contain(source.convert("RGB"), (394, 615))
            sheet.paste(picture, (xx + (407 - picture.width) // 2, yy + 21 + (615 - picture.height) // 2))
            label = f"{lane} · {key} · {frame['time']:.4f} s"
            if key == "after" and "word_to_picture_ms" in frames:
                label += f" · from cue {frames['word_to_picture_ms']:+.1f} ms"
            draw.text((xx + 8, yy + 5), label, fill="white")
    sheet.save(root / filename, quality=93)


def write_comparison(root, entry, moments, details):
    comparison_sheet(root, entry["lanes"], entry["sheet"], moments)
    if details:
        entry["detail_sheet"] = f"detail-{entry['sheet']}"
        comparison_sheet(root, entry["lanes"], entry["detail_sheet"], moments, detail=True)


def viewer(root, lanes, seams, landmarks, holds):
    template = Path(__file__).with_name("frame-viewer.html").read_text(encoding="utf-8")
    # The script literals contain generated relative names, validated IDs and numbers.
    frames = {name: [{key: row[key] for key in ("frame", "time", "image")} for row in rows]
              for name, rows in lanes.items()}
    cuts = {lane: item["after"]["frame"] for lane, item in (seams or {}).items()}
    jumps = {event["id"]: {lane: item["after"]["frame"] for lane, item in event["lanes"].items()}
             for event in landmarks}
    hold_sheets = {hold["id"]: hold["sheet"] for hold in holds}
    (root / "frames.html").write_text(template.replace("/* FRAME_DATA */", json.dumps(frames))
                                     .replace("/* CUT_DATA */", json.dumps(cuts))
                                     .replace("/* LANDMARK_DATA */", json.dumps(jumps))
                                     .replace("/* HOLD_DATA */", json.dumps(hold_sheets)), encoding="utf-8")


def build(reference, candidate, mapping, beat, output, regions, *, previous=None):
    # Every cut retains its own timestamps and world state across the review.
    files = {"reference": reference}
    if previous is not None:
        files["previous"] = previous
    files["candidate"] = candidate
    meta = {lane: inspect(file) for lane, file in files.items()}
    rows = validate_map(mapping, meta["reference"]["video_seconds"], meta["candidate"]["video_seconds"])
    row = next((row for row in rows if row["id"] == beat and row["candidate"] is not None), None)
    if row is None:
        raise ValueError(f"Expected a paired beat in the map: {beat}")
    if previous is None and "previous" in row:
        raise ValueError(f"{beat}: supply the previous video with --previous")
    if previous is not None:
        validate_span(beat, "previous", row.get("previous"), meta["previous"]["video_seconds"])
    anchors = seam_times(row)
    events = landmark_times(row)
    words = word_anchor_times(row, events)
    landmarks = [{"id": name, "sheet": f"landmark-{name}.jpg", "lanes": {}} for name in events]
    intervals = hold_ranges(row)
    details = detail_boxes(row, meta)
    holds = [{"id": name, "sheet": f"hold-{name}.jpg", "lanes": {}} for name in intervals]
    output.mkdir(parents=True, exist_ok=False)
    lanes = {}
    seams = {}
    for lane, file in files.items():
        pairs = decode(file, meta[lane]["stream_index"], *row[lane], output / lane)
        if details:
            # Crop before the review resize and prove that each crop uses the full-frame clock.
            crops = decode(file, meta[lane]["stream_index"], *row[lane], output / f"{lane}-detail", detail=details[lane])
            if [time for _, time in pairs] != [time for _, time in crops]:
                raise ValueError(f"The {lane} detail trace does not match the full-frame timestamps")
        lanes[lane] = index_frames(pairs, output, lane, regions)
        consecutive_sheets(lanes[lane], output, lane)
        if anchors is not None:
            seams[lane] = seam_pictures(lane, anchors[lane], pairs, lanes[lane])
        for event in landmarks:
            name = event["id"]
            event["lanes"][lane] = seam_pictures(
                lane, events[name][lane], pairs, lanes[lane], name, word_onset=words.get(name, {}).get(lane))
        for hold in holds:
            name = hold["id"]
            hold["lanes"][lane] = hold_pictures(lane, name, intervals[name][lane], pairs, lanes[lane])
    viewer(output, lanes, seams, landmarks, holds)
    manifest = {"schema_version": 1, "beat": row, "regions": regions,
                "inputs": meta, "decoded_frames": {lane: len(frames) for lane, frames in lanes.items()}}
    if details:
        manifest["detail_boxes_pixels"] = details
    if seams:
        manifest["seam"] = {"sheet": "seam.jpg", "lanes": seams}
        write_comparison(output, manifest["seam"], ("before", "after"), details)
    if landmarks:
        for event in landmarks:
            write_comparison(output, event, ("before", "after"), details)
        manifest["landmarks"] = landmarks
    if holds:
        for hold in holds:
            write_comparison(output, hold, ("first", "middle", "last"), details)
        manifest["holds"] = holds
    (output / "frame-trace.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest["decoded_frames"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("reference", "candidate", "map", "out"):
        parser.add_argument("--"+flag, required=True, type=Path)
    parser.add_argument("--beat", required=True)
    parser.add_argument("--previous", type=Path, help="Earlier render for a third, independently mapped lane.")
    parser.add_argument("--region", action="append", type=parse_region, default=[])
    args = parser.parse_args()
    regions = {"full": (0, 0, 1, 1), **dict(args.region)}
    try:
        counts = build(args.reference.resolve(), args.candidate.resolve(),
                       json.loads(args.map.read_text(encoding="utf-8-sig")), args.beat, args.out.resolve(), regions,
                       previous=args.previous.resolve() if args.previous is not None else None)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Frame trace failed: {error}\n")
    print(f"{args.beat}: " + ", ".join(f"{count} {lane} frames" for lane, count in counts.items()))


if __name__ == "__main__":
    main()
