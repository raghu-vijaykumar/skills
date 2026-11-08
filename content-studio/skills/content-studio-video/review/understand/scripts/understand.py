#!/usr/bin/env python3
"""Extract review frames, timestamped contact sheets, and an evidence manifest.

The tool never interprets content. It produces visual evidence for a
vision-capable agent and a template for an evidence-linked voiceover.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

SCHEMA_VERSION = 2
DEFAULT_INTERVAL = 8.0
DEFAULT_FRAME_WIDTH = 480
DEFAULT_GRID_COLUMNS = 5
DEFAULT_GRID_ROWS = 4


def run(cmd):
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-2000:])
    return result


def probe(video):
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(video),
        ]
    )
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Could not read video duration: {video}") from error


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def timecode(seconds):
    seconds = max(0.0, float(seconds))
    minutes, remainder = divmod(int(round(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{remainder:02d}"
    return f"{minutes:02d}:{remainder:02d}"


def parse_range(duration, start, end):
    start = max(0.0, float(start))
    end = duration if end is None else min(float(end), duration)
    if start >= end:
        raise ValueError("start must be before end")
    return start, end


def clear_outputs(folder, pattern):
    if folder.is_dir():
        for path in folder.glob(pattern):
            if path.is_file():
                path.unlink()


def extract_frames(video, frames_dir, start, end, interval, width, quality):
    """Extract low-resolution frames in one FFmpeg pass and read their PTS."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    clear_outputs(frames_dir, "frame-*.jpg")
    # Select the first frame and then one frame per interval. The fps filter
    # drops the final sample at EOF; select keeps it.
    vf = (
        f"select='isnan(prev_selected_t)+gte(t-prev_selected_t,{interval:g})',"
        f"scale={width}:-2,showinfo"
    )
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y", "-loglevel", "info"]
    if start > 0:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += [
        "-i",
        str(video),
        "-t",
        f"{end - start:.3f}",
        "-an",
        "-vf",
        vf,
        "-fps_mode",
        "vfr",
        "-q:v",
        str(quality),
        "-start_number",
        "0",
        str(frames_dir / "frame-%04d.jpg"),
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode and "-fps_mode" in cmd:
        stderr = result.stderr or ""
        if "Unrecognized option 'fps_mode'" in stderr or "Option 'fps_mode' not found" in stderr:
            # Older FFmpeg releases use -vsync instead of -fps_mode.
            fallback = [part for part in cmd if part not in ("-fps_mode", "vfr")]
            fallback[fallback.index("-q:v"):fallback.index("-q:v")] = ["-vsync", "vfr"]
            result = subprocess.run(
                fallback,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-2000:])

    paths = sorted(frames_dir.glob("frame-*.jpg"))
    if not paths:
        raise RuntimeError("FFmpeg produced no frames")

    times = [
        float(value)
        for value in re.findall(r"pts_time:([0-9]+(?:\.[0-9]+)?)", result.stderr)
    ]
    if len(times) != len(paths):
        times = [index * interval for index in range(len(paths))]
    elif start > 0 and min(times) < start - 0.01:
        # Input seeking normally resets PTS; add the seek offset when it does not.
        times = [start + value for value in times]
    times = [min(end, max(start, value)) for value in times]
    return list(zip(paths, times))


def _font(size, bold=False):
    from PIL import ImageFont

    names = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for name in names:
        if Path(name).is_file():
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # pragma: no cover - older Pillow
        return ImageFont.load_default()


def build_contact_sheets(
    out,
    frames,
    source_name,
    interval,
    columns=DEFAULT_GRID_COLUMNS,
    rows=DEFAULT_GRID_ROWS,
    quality=85,
):
    """Compose timestamped thumbnail grids so a human can review the edit fast."""
    try:
        from PIL import Image, ImageDraw
    except ImportError as error:  # pragma: no cover - dependency check
        raise RuntimeError(
            "Contact sheets need Pillow. Install it with: python -m pip install Pillow"
        ) from error

    if columns < 1 or rows < 1:
        raise ValueError("grid columns and rows must be positive")

    sheets_dir = out / "sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    clear_outputs(sheets_dir, "sheet-*.jpg")

    per_sheet = columns * rows
    total_sheets = (len(frames) + per_sheet - 1) // per_sheet
    header_font = _font(18, bold=True)
    label_font = _font(15)
    sheet_records = []

    for sheet_index in range(total_sheets):
        chunk = frames[sheet_index * per_sheet : (sheet_index + 1) * per_sheet]
        first_path = out / chunk[0]["path"]
        with Image.open(first_path) as first_image:
            thumb_width, thumb_height = first_image.size

        margin = 16
        gap = 8
        label_height = 26
        header_height = 38
        sheet_width = margin * 2 + columns * thumb_width + (columns - 1) * gap
        sheet_height = (
            header_height
            + margin
            + rows * (thumb_height + label_height)
            + (rows - 1) * gap
            + margin
        )
        canvas = Image.new("RGB", (sheet_width, sheet_height), (18, 18, 20))
        draw = ImageDraw.Draw(canvas)

        start = chunk[0]["at_seconds"]
        end = chunk[-1]["at_seconds"]
        sheet_id = f"sheet-{sheet_index + 1:04d}"
        header = (
            f"{source_name}  |  every {interval:g}s  |  "
            f"{sheet_id} {sheet_index + 1}/{total_sheets}  |  "
            f"{timecode(start)}-{timecode(end)}"
        )
        draw.text((margin, 10), header, font=header_font, fill=(235, 235, 240))

        for position, frame in enumerate(chunk):
            row, column = divmod(position, columns)
            x = margin + column * (thumb_width + gap)
            y = header_height + margin + row * (thumb_height + label_height + gap)
            with Image.open(out / frame["path"]) as image:
                image = image.convert("RGB")
                if image.size != (thumb_width, thumb_height):
                    image = image.resize(
                        (thumb_width, thumb_height), Image.Resampling.LANCZOS
                    )
                canvas.paste(image, (x, y))
            draw.rectangle(
                [x, y + thumb_height, x + thumb_width, y + thumb_height + label_height],
                fill=(0, 0, 0),
            )
            label = f"{frame['id']}   {timecode(frame['at_seconds'])}"
            draw.text(
                (x + 7, y + thumb_height + 5),
                label,
                font=label_font,
                fill=(245, 245, 245),
            )
            frame["sheet_id"] = sheet_id

        path = sheets_dir / f"{sheet_id}.jpg"
        canvas.save(path, "JPEG", quality=quality, optimize=True)
        sheet_records.append(
            {
                "id": sheet_id,
                "path": str(path.relative_to(out)),
                "start_seconds": round(start, 3),
                "end_seconds": round(end, 3),
                "frame_ids": [frame["id"] for frame in chunk],
            }
        )

    return sheet_records


def analyze(
    video,
    out,
    interval=DEFAULT_INTERVAL,
    start=0.0,
    end=None,
    frame_width=DEFAULT_FRAME_WIDTH,
    grid=True,
    grid_columns=DEFAULT_GRID_COLUMNS,
    grid_rows=DEFAULT_GRID_ROWS,
    frame_quality=4,
    sheet_quality=85,
    context=None,
):
    """Extract frames and sheets; return the evidence manifest."""
    video = Path(video).resolve()
    out = Path(out).resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    if interval <= 0:
        raise ValueError("interval must be positive")
    if frame_width < 64:
        raise ValueError("frame width must be at least 64 pixels")
    if grid and (grid_columns < 1 or grid_rows < 1):
        raise ValueError("grid columns and rows must be positive")

    duration = probe(video)
    start, end = parse_range(duration, start, end)
    out.mkdir(parents=True, exist_ok=True)

    pairs = extract_frames(
        video, out / "frames", start, end, interval, frame_width, frame_quality
    )
    frames = [
        {
            "id": f"f{index:04d}",
            "at_seconds": round(at_seconds, 3),
            "timecode": timecode(at_seconds),
            "path": str(path.relative_to(out)),
        }
        for index, (path, at_seconds) in enumerate(pairs)
    ]

    sheets = []
    if grid:
        sheets = build_contact_sheets(
            out,
            frames,
            video.name,
            interval,
            columns=grid_columns,
            rows=grid_rows,
            quality=sheet_quality,
        )

    human = {}
    if context:
        human = json.loads(Path(context).read_text(encoding="utf-8"))
        if not isinstance(human, dict):
            raise ValueError("context must be a JSON object")

    digest = file_sha256(video)
    result = {
        "schema_version": SCHEMA_VERSION,
        "source": str(video),
        "source_sha256": digest,
        "duration_seconds": duration,
        "interval_seconds": interval,
        "range": {"start_seconds": round(start, 3), "end_seconds": round(end, 3)},
        "frame_width": frame_width,
        "frames": frames,
        "contact_sheets": sheets,
        "human_context": human,
        "observations": [],
        "status": "awaiting_vision_analysis",
    }
    (out / "evidence.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    language = human.get("language", "kn-en") if isinstance(human, dict) else "kn-en"
    (out / "voiceover-template.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source": str(video),
                "source_sha256": digest,
                "duration_seconds": duration,
                "language": language,
                "approval": "pending",
                "segments": [],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (out / "observations-template.json").write_text("[]\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Extract sparse review frames and timestamped contact sheets."
    )
    parser.add_argument("--video", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--end", type=float)
    parser.add_argument("--frame-width", type=int, default=DEFAULT_FRAME_WIDTH)
    parser.add_argument("--frame-quality", type=int, default=4)
    parser.add_argument("--grid-cols", type=int, default=DEFAULT_GRID_COLUMNS)
    parser.add_argument("--grid-rows", type=int, default=DEFAULT_GRID_ROWS)
    parser.add_argument("--no-grid", action="store_true")
    parser.add_argument("--sheet-quality", type=int, default=85)
    parser.add_argument("--context")
    args = parser.parse_args()

    result = analyze(
        args.video,
        args.out,
        interval=args.interval,
        start=args.start,
        end=args.end,
        frame_width=args.frame_width,
        grid=not args.no_grid,
        grid_columns=args.grid_cols,
        grid_rows=args.grid_rows,
        frame_quality=args.frame_quality,
        sheet_quality=args.sheet_quality,
        context=args.context,
    )
    print(
        json.dumps(
            {
                "evidence": str(Path(args.out).resolve() / "evidence.json"),
                "frames": len(result["frames"]),
                "contact_sheets": len(result["contact_sheets"]),
            }
        )
    )


if __name__ == "__main__":
    main()
