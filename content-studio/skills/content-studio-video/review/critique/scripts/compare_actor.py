"""Build matched actor crops and full-frame staging evidence."""

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageOps

from compare import inspect, run, seek_args


def parse_box(box, width, height):
    if not isinstance(box, list) or len(box) != 4 or any(
        type(value) not in (float, int) or not math.isfinite(value) for value in box
    ):
        raise ValueError("Use normalized [left, top, right, bottom] actor bounds")
    left, top, right, bottom = box
    if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
        raise ValueError("Actor bounds must lie inside the frame")
    pixels = [round(left * width), round(top * height), round(right * width), round(bottom * height)]
    if pixels[0] >= pixels[2] or pixels[1] >= pixels[3]:
        raise ValueError("Actor bounds must cover at least one pixel")
    return pixels


def capture(file, info, timestamp):
    if type(timestamp) not in (int, float) or not math.isfinite(timestamp) or not 0 <= timestamp < info["video_seconds"]:
        raise ValueError("Sample time must be within the video stream")
    data = run("ffmpeg", "-nostdin", "-loglevel", "error", *seek_args(file, timestamp),
               "-an", "-map", f"0:{info['stream_index']}", "-frames:v", "1",
               "-f", "image2pipe", "-c:v", "png", "-threads", "1", "pipe:1")
    with Image.open(io.BytesIO(data)) as image:
        return image.convert("RGB")


def paste_fit(sheet, image, rect):
    x, y, width, height = rect
    fitted = ImageOps.contain(image, (width, height), Image.Resampling.LANCZOS)
    offset = x + (width - fitted.width) // 2, y + (height - fitted.height) // 2
    sheet.paste(fitted, offset)
    return (*offset, fitted.width, fitted.height)


def open_photo(file):
    with Image.open(file) as source:
        if getattr(source, "is_animated", False):
            raise ValueError("Use a single real-world photo per appearance comparison")
        frame = ImageOps.exif_transpose(source).convert("RGB")
    with file.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    return frame, {"kind": "photo", "file": file.name, "sha256": checksum,
                   "width": frame.width, "height": frame.height}


def build(reference, candidate, mapping, output, reference_photo=False, *, previous=None):
    # Keep the source, before and after in reading order for revision reviews.
    sides = {"reference": reference}
    if previous is not None:
        sides["previous"] = previous
    sides["candidate"] = candidate
    photo, source = open_photo(reference) if reference_photo else (None, inspect(reference))
    media = {side: source if side == "reference" else inspect(file) for side, file in sides.items()}
    actors = mapping.get("actors")
    if not isinstance(actors, list) or not actors:
        raise ValueError("Use a nonempty actors list")
    seen = set()
    for actor in actors:
        name = actor.get("id") if isinstance(actor, dict) else None
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", name) or name in seen:
            raise ValueError(f"Invalid or duplicate actor ID {name!r}")
        seen.add(name)
        for side in sides:
            if not isinstance(actor.get(side), dict):
                raise ValueError(f"{name}: provide an independent {side} sample")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for actor in actors:
        name = actor["id"]
        sheet = Image.new("RGB", (640 * len(sides), 824), "#1a1b21")
        draw = ImageDraw.Draw(sheet)
        evidence = {"id": name, "sheet": f"{name}.png"}
        for i, (side, file) in enumerate(sides.items()):
            sample = actor[side]
            if side == "reference" and photo is not None:
                if "seconds" in sample:
                    raise ValueError("Omit seconds for the reference photo")
                frame = photo
                title = "reference photo  |  source framing"
                moment = {}
            else:
                at = sample["seconds"]
                frame = capture(file, media[side], at)
                title = f"{side}  {at:.3f}s  |  full frame"
                moment = {"requested_seconds": at}
            w, h = frame.size
            l, t, r, b = parse_box(sample["box"], w, h)
            x = i * 640
            fx, fy, fw, fh = paste_fit(sheet, frame, (x + 10, 42, 620, 340))
            draw.rectangle((fx+fw*l/w, fy+fh*t/h, fx+fw*r/w, fy+fh*b/h), outline="#68edcc", width=2)
            paste_fit(sheet, frame.crop((l, t, r, b)), (x + 10, 440, 620, 366))
            size = [(r-l)/w, (b-t)/h]
            draw.text((x+20, 16), title, fill="white")
            draw.text((x+20, 403), f"actor crop  |  {size[0]:.1%} of frame width  {size[1]:.1%} of height", fill="#68edcc")
            evidence[side] = {**moment, "box_pixels": [l,t,r,b], "frame_fraction": size}
        sheet.save(output / evidence["sheet"])
        rows.append(evidence)
    (output / "evidence.json").write_text(json.dumps({**media, "actors": rows}, indent=2)+"\n", encoding="utf-8")
    return len(rows)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    reference = cli.add_mutually_exclusive_group(required=True)
    reference.add_argument("--reference", type=Path, help="Local reference video.")
    reference.add_argument("--reference-photo", type=Path, help="Local real-world still for appearance review.")
    for name in ("candidate", "map", "out"):
        cli.add_argument("--"+name, type=Path, required=True)
    cli.add_argument("--previous", type=Path, help="Previous render for a three-column actor retest.")
    args = cli.parse_args()
    try:
        mapping = json.loads(args.map.read_text(encoding="utf-8-sig"))
        count = build(args.reference or args.reference_photo, args.candidate, mapping, args.out,
                      reference_photo=bool(args.reference_photo), previous=args.previous)
    except (OSError, KeyError, TypeError, ValueError) as error:
        cli.exit(1, f"Actor comparison failed: {error}\n")
    print(f"{count} actor comparisons in {args.out}")


if __name__ == "__main__":
    main()
