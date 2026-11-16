"""Track seeded objects in the frame trace for each cut independently."""

import argparse
import csv
import json
import math
from pathlib import Path
import re

import numpy as np
from PIL import Image, ImageDraw


def luma(file):
    with Image.open(file) as image:
        return np.asarray(image.convert("L"), dtype=np.float64)


def windows_sum(values, h, w):
    integral = np.pad(values, ((1, 0), (1, 0))).cumsum(axis=0).cumsum(axis=1)
    return integral[h:, w:] - integral[:-h, w:] - integral[h:, :-w] + integral[:-h, :-w]


def match(image, needle, x, y, radius):
    h, w = needle.shape
    top, left = max(0, y-radius), max(0, x-radius)
    window = image[top:y+h+radius, left:x+w+radius]
    # Zero-mean normalized correlation tolerates a brightness change. Local
    # search limits identity swaps when multiple requests share identical text.
    centered = needle - needle.mean()
    energy = float(np.linalg.norm(centered))
    if energy < 1e-6:
        raise ValueError("Seed box needs visible texture or edges")
    wh, ww = window.shape
    shape = (wh+h-1, ww+w-1)
    product = (np.fft.rfft2(window, s=shape, axes=(0, 1)) *
               np.fft.rfft2(centered[::-1, ::-1], s=shape, axes=(0, 1)))
    correlation = np.fft.irfft2(product, s=shape, axes=(0, 1))[h-1:wh, w-1:ww]
    mass = windows_sum(window, h, w)
    variance = windows_sum(window**2, h, w) - mass**2 / (h*w)
    denominator = np.sqrt(np.maximum(variance, 1e-9)) * energy
    score = correlation / denominator
    row, column = np.unravel_index(np.argmax(score), score.shape)
    best = float(np.clip(score[row, column], -1, 1))
    return int(left + column), int(top + row), best


def follow(root, lane, rows, track):
    first, last = track["first"], track["last"]
    if not isinstance(first, int) or not isinstance(last, int) or not 0 <= first <= last < len(rows):
        raise ValueError("Track bounds must be existing local frame indices")
    radius, threshold = track.get("radius", 18), track.get("threshold", 0.72)
    if not isinstance(radius, int) or not 1 <= radius <= 80 or not 0 < threshold <= 1:
        raise ValueError("Use a radius from 1 to 80 pixels and threshold above 0 through 1")
    seed = luma(root / rows[first]["image"])
    height, width = seed.shape
    x, y, w, h = track["box"]
    if (any(type(n) is not int for n in (x, y, w, h)) or min(w, h) < 4
            or not (0 <= x < x+w <= width and 0 <= y < y+h <= height)):
        raise ValueError(f"Seed must be x,y,width,height in the trace image ({width}x{height})")
    needle = seed[y:y+h, x:x+w].copy()
    origin = ((x+w/2)/width, (y+h/2)/height)
    samples = []
    misses = 0
    for row in rows[first:last+1]:
        image = luma(root / row["image"])
        if image.shape != seed.shape:
            raise ValueError(f"{lane}: frame dimensions changed; split the trace")
        position = None
        score = None
        # Do not reacquire after sustained loss. A new shot needs a new seed.
        if misses < 3:
            next_x, next_y, score = match(image, needle, x, y, radius)
            if score >= threshold:
                x, y = next_x, next_y
                position = ((x+w/2)/width, (y+h/2)/height)
                misses = 0
            else:
                misses += 1
        samples.append({"frame": int(row["frame"]), "time": float(row["time"]),
                        "score": round(score, 4) if score is not None else None,
                        "x": round(position[0], 6) if position else None,
                        "y": round(position[1], 6) if position else None,
                        "dx": round(position[0]-origin[0], 6) if position else None,
                        "dy": round(position[1]-origin[1], 6) if position else None})
    return samples


def trail(root, row, points, file):
    with Image.open(root / row["image"]) as original:
        image = original.convert("RGB")
    draw = ImageDraw.Draw(image)
    w, h = image.size
    previous = None
    for sample in points:
        point = (w*sample["x"], h*sample["y"]) if sample["x"] is not None else None
        if previous and point:
            draw.line((previous, point), fill="#ffdf66", width=3)
        if point and (previous is None or sample is points[-1]):
            x, y = point
            draw.ellipse((x-4, y-4, x+4, y+4), fill="#ffdf66", outline="#121212", width=1)
        previous = point
    image.save(file)


def retarget(points, settings):
    """Produce scene-local MotionObject keys with displacement from the seed."""
    fps, width, height, start = (settings[k] for k in ("fps", "width", "height", "start_frame"))
    if any(type(v) is not int or v <= 0 for v in (fps, width, height)) or type(start) is not int or start < 0:
        raise ValueError("Retargeting needs positive integer fps and canvas dimensions, and nonnegative start_frame")
    time_scale = settings.get("time_scale", 1)
    if not isinstance(time_scale, (int, float)) or not math.isfinite(time_scale) or time_scale <= 0:
        raise ValueError("time_scale must be finite and positive")
    segments = []
    segment = {}
    for point in points:
        if point["x"] is None:
            if segment:
                segments.append(list(segment.values()))
                segment = {}
            continue
        frame = start + round((point["time"] - points[0]["time"]) * fps * time_scale)
        segment[frame] = {"frame": frame, "x": round(point["dx"] * width, 3), "y": round(point["dy"] * height, 3),
                          "ease": "linear"}
    if segment:
        segments.append(list(segment.values()))
    return segments


def measure_relative(tracks, requests):
    if not isinstance(requests, list):
        raise ValueError("relative_tracks must be a list")
    by_id = {track["id"]: track for track in tracks}
    ids = set()
    results = []
    for request in requests:
        name = request["id"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,47}", name) or name in ids:
            raise ValueError("Relative tracks need unique lowercase IDs")
        ids.add(name)
        subject = by_id[request["subject"]]
        anchor = by_id[request["anchor"]]
        if subject is anchor or subject["lane"] != anchor["lane"]:
            raise ValueError(f"{name}: choose two distinct tracks from the same lane")
        start = max(subject["first"], anchor["first"])
        end = min(subject["last"], anchor["last"])
        if end < start:
            raise ValueError(f"{name}: the tracks need overlapping frames")
        fixed = {p["frame"]: p for p in anchor["samples"]}
        baseline = None
        samples = []
        for point in subject["samples"]:
            if not start <= point["frame"] <= end:
                continue
            other = fixed[point["frame"]]
            dx, dy = None, None
            if point["x"] is not None and other["x"] is not None:
                # Subtract simultaneous anchor position, then measure change from the first joint frame.
                offset = point["x"] - other["x"], point["y"] - other["y"]
                if baseline is None:
                    baseline = offset
                dx, dy = (round(value - initial, 6) for value, initial in zip(offset, baseline))
            samples.append({"frame": point["frame"], "time": point["time"], "dx": dx, "dy": dy})
        visible = [p for p in samples if p["dx"] is not None]
        results.append({**request, "lane": subject["lane"], "range": [start, end],
                        "tracked_frames": len(visible),
                        "max_abs_dx": max((abs(p["dx"]) for p in visible), default=None),
                        "max_abs_dy": max((abs(p["dy"]) for p in visible), default=None),
                        "samples": samples})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("trace", "seeds", "out"):
        parser.add_argument("--"+flag, required=True, type=Path)
    args = parser.parse_args()
    root = args.trace.resolve()
    try:
        manifest = json.loads((root / "frame-trace.json").read_text(encoding="utf-8"))
        rows = {}
        for lane in ("reference", "candidate"):
            with (root / f"{lane}.csv").open(encoding="utf-8", newline="") as stream:
                rows[lane] = list(csv.DictReader(stream))
        seeds = json.loads(args.seeds.read_text(encoding="utf-8-sig"))
        tracks = seeds["tracks"]
        ids = [track["id"] for track in tracks]
        if not ids or len(ids) != len(set(ids)) or not all(re.fullmatch(r"[a-z][a-z0-9-]{0,47}", name) for name in ids):
            raise ValueError("Tracks need unique lowercase IDs")
        args.out.mkdir(parents=True, exist_ok=False)
        report = []
        for track in tracks:
            lane = track["lane"]
            points = follow(root, lane, rows[lane], track)
            path = f"track-{track['id']}.jpg"
            trail(root, rows[lane][track["first"]], points, args.out / path)
            tracked = sum(p["x"] is not None for p in points)
            record = {**track, "tracked_frames": tracked, "trail": path, "samples": points}
            if "retarget" in track:
                record["motion_key_segments"] = retarget(points, track["retarget"])
            report.append(record)
            print(f"{track['id']}: {tracked}/{len(points)} tracked")
        data = {"schema_version": 1, "beat": manifest["beat"], "inputs": manifest["inputs"], "tracks": report}
        if "relative_tracks" in seeds:
            data["relative_tracks"] = measure_relative(report, seeds["relative_tracks"])
        (args.out / "tracks.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Object trace failed: {error}\n")


if __name__ == "__main__":
    main()
