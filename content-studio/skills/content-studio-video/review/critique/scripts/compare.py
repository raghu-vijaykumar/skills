"""Build local motion evidence for independently timed narrative beats."""

import argparse
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageDraw


def run(*args):
    result = subprocess.run(args, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"{args[0]}: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def inspect(file):
    probe = json.loads(run("ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(file)))
    video = next((s for s in probe["streams"] if s["codec_type"] == "video" and
                  not s.get("disposition", {}).get("attached_pic")), None)
    if video is None:
        raise ValueError(f"No timed video stream: {file}")
    # ffprobe rounds the displayed decimal duration, so use the exact video
    # clock when a beat map ends at a rational frame boundary.
    try:
        duration = float(int(video["duration_ts"]) * Fraction(video["time_base"]))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        duration = float(video.get("duration") or probe["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"No positive video duration: {file}")
    with file.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"file": file.name, "sha256": checksum, "video_seconds": duration,
            "width": video["width"], "height": video["height"], "stream_index": video["index"],
            "fps": video["avg_frame_rate"], "has_audio": any(s["codec_type"] == "audio" for s in probe["streams"])}


def validate_span(name, role, span, seconds):
    if not isinstance(span, list) or len(span) != 2 or not all(
        type(point) in (int, float) and math.isfinite(point) for point in span
    ):
        raise ValueError(f"{name}: {role} needs two finite times")
    start, end = span
    if not (0 <= start < end <= seconds and end - start <= 15):
        raise ValueError(f"{name}: {role} range must be within 0–{seconds:g} and at most 15 seconds")


def validate_map(data, reference_seconds, candidate_seconds):
    rows = data.get("beats") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("The map needs a nonempty beats list")
    ids = set()
    for row in rows:
        name = row.get("id") if isinstance(row, dict) else None
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", name) or name in ids:
            raise ValueError(f"Invalid or duplicate beat ID: {name!r}")
        ids.add(name)
        for role, seconds in (("reference", reference_seconds), ("candidate", candidate_seconds)):
            if role not in row:
                raise ValueError(f"{name}: missing {role} field")
            span = row[role]
            if role == "candidate" and span is None:
                continue
            validate_span(name, role, span, seconds)
    return rows


def coverage(spans, duration):
    # Multiple diagnostic rows may overlap. Count the union only once.
    cursor = 0.0
    gaps = []
    for start, end in sorted(spans):
        if start > cursor:
            gaps.append([cursor, start])
        cursor = max(cursor, end)
    if cursor < duration:
        gaps.append([cursor, duration])
    return {"mapped_seconds": round(duration - sum(end - start for start, end in gaps), 6),
            "uncovered_ranges": gaps}


def seek_args(file, time):
    return ("-ss", f"{time:.6f}", "-i", str(file))


def scan_cut_candidates(file, stream, threshold):
    """Flag abrupt picture changes on native timestamps for manual review."""
    graph = (
        "setpts=PTS-STARTPTS,scale=256:256:force_original_aspect_ratio=decrease,"
        f"select='gt(scene,{threshold})',metadata=print:key=lavfi.scene_score:file=-"
    )
    log = run("ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(file),
              "-map", f"0:{stream}", "-an", "-vf", graph, "-f", "null", "-").decode()
    return [{"seconds": float(at), "score": float(score)} for at, score in
            re.findall(r"pts_time:([\d.eE+\-]+)\s*\r?\n\s*lavfi.scene_score=([\d.]+)", log)]


def still_sheet(files, streams, row, output):
    width, height, label_height = 224, 280, 24
    fractions = (0.08, 0.28, 0.50, 0.72, 0.92)
    sheet = Image.new("RGB", (width * len(fractions), (height + label_height) * 2), "#1d2026")
    draw = ImageDraw.Draw(sheet)
    for i, role in enumerate(("reference", "candidate")):
        start, end = row[role]
        for j, fraction in enumerate(fractions):
            time = start + (end - start) * fraction
            encoded = run("ffmpeg", "-nostdin", "-loglevel", "error", *seek_args(files[i], time),
                          "-map", f"0:{streams[i]}", "-an", "-frames:v", "1",
                          "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease",
                          "-f", "image2pipe", "-c:v", "png", "-threads", "1", "pipe:1")
            with Image.open(io.BytesIO(encoded)) as frame:
                x, y = j * width, i * (height + label_height)
                sheet.paste(frame.convert("RGB"), (x + (width - frame.width) // 2, y + (height - frame.height) // 2))
                draw.text((x + 8, y + height + 4), f"{role} {time:.3f} s", fill="white")
    sheet.save(output, quality=91)


def paired_motion(files, streams, row, output):
    spans = [row["reference"], row["candidate"]]
    lengths = [end - start for start, end in spans]
    duration = max(lengths)
    inputs = [arg for file, (start, _end) in zip(files, spans) for arg in seek_args(file, start)]
    filters = []
    for i, (length, stream) in enumerate(zip(lengths, streams)):
        filters.append(
            f"[{i}:{stream}]trim=duration={length:.6f},setpts=PTS-STARTPTS,fps=12,"
            "scale=240:320:force_original_aspect_ratio=decrease,pad=240:320:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,tpad=stop_mode=add:stop_duration={max(0, duration-length):.6f}[v{i}]"
        )
    graph = ";".join(filters) + ";[v0][v1]hstack=shortest=1,split[a][b];[b]palettegen[p];[a][p]paletteuse=dither=bayer[out]"
    run("ffmpeg", "-nostdin", "-loglevel", "error", *inputs, "-filter_complex_threads", "1",
        "-filter_complex", graph, "-map", "[out]", "-an", "-loop", "0", str(output))


def build(reference, candidate, mapping, output, cut_threshold=None):
    media = {role: inspect(file) for role, file in (("reference", reference), ("candidate", candidate))}
    lengths = [media[role]["video_seconds"] for role in ("reference", "candidate")]
    rows = validate_map(mapping, *lengths)
    # Refuse populated outputs so a retry cannot mix evidence from different masters.
    output.mkdir(parents=True, exist_ok=False)
    mapped = [row for row in rows if row["candidate"] is not None]
    streams = [media[role]["stream_index"] for role in ("reference", "candidate")]
    for row in mapped:
        prefix = row["id"]
        still_sheet((reference, candidate), streams, row, output / f"{prefix}.jpg")
        paired_motion((reference, candidate), streams, row, output / f"{prefix}.gif")
    evidence = {
        "schema_version": 1, **media,
        "coverage": {role: coverage([row[role] for row in mapped], length)
                     for role, length in zip(("reference", "candidate"), lengths)},
        "rows": [{**row, "sheet": f"{row['id']}.jpg", "motion": f"{row['id']}.gif"}
                 if row["candidate"] is not None else row for row in rows],
    }
    if cut_threshold is not None:
        # Scan each master once. Keep a single timestamp list so overlapping
        # diagnostic rows do not count the same reference cut twice.
        evidence["cut_survey"] = {
            "threshold": cut_threshold,
            **{role: scan_cut_candidates(file, stream, cut_threshold)
               for role, file, stream in zip(("reference", "candidate"), (reference, candidate), streams)},
        }
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return len(mapped)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for flag in ("reference", "candidate", "map", "out"):
        cli.add_argument("--" + flag, type=Path, required=True)
    cli.add_argument("--cut-threshold", type=float, metavar="SCORE",
                     help="Also survey both exact videos for abrupt picture changes (0 < SCORE < 1).")
    args = cli.parse_args()
    if args.cut_threshold is not None and not 0 < args.cut_threshold < 1:
        cli.error("--cut-threshold must be between 0 and 1, exclusive")
    try:
        count = build(args.reference.resolve(), args.candidate.resolve(),
                      json.loads(args.map.read_text(encoding="utf-8-sig")), args.out.resolve(), args.cut_threshold)
    except (OSError, KeyError, ValueError) as error:
        cli.exit(1, f"Critique evidence failed: {error}\n")
    print(f"{count} mapped beat comparisons in {args.out}")


if __name__ == "__main__":
    main()
