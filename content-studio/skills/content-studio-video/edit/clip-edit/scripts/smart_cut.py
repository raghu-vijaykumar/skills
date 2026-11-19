"""Guarded H.264 cuts-only comparison with copied interior GOPs.

This is an opt-in candidate, not the default delivery timeline renderer. A
failed guard or verification leaves the accurate edit route in charge.
"""

from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
import os
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

import editing


class SmartCutError(RuntimeError):
    pass


def run_command(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                            errors="replace")
    if result.returncode:
        tail = [line for line in result.stderr.splitlines() if line.strip()]
        raise SmartCutError("command failed: " + " | ".join(tail[-3:])[-600:])
    return result.stdout


def ffprobe(path: Path, *options: str) -> dict:
    return json.loads(run_command(["ffprobe", "-v", "error", *options,
                                   "-of", "json", str(path)]))


def source_profile(path: Path) -> tuple[dict, dict | None, list[dict], Fraction]:
    info = ffprobe(path, "-show_format", "-show_streams")
    videos = [s for s in info["streams"] if s["codec_type"] == "video"]
    audios = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if len(videos) != 1 or len(audios) > 1 or len(info["streams"]) != len(videos) + len(audios):
        raise SmartCutError("requires one video stream and at most one audio stream")
    video = videos[0]
    audio = audios[0] if audios else None
    if video.get("codec_name") != "h264" or video.get("pix_fmt") != "yuv420p":
        raise SmartCutError("requires 8-bit yuv420p H.264")
    if video.get("color_transfer") in {"arib-std-b67", "smpte2084"} or editing.is_dolby(video):
        raise SmartCutError("HDR and Dolby Vision require the accurate timeline route")
    if video.get("color_transfer") not in {"bt709", "smpte170m", "bt470bg",
                                            "iec61966-2-1", "gamma22", "gamma28"}:
        raise SmartCutError("SDR transfer must be explicitly identified")
    if any(int(item.get("rotation", 0)) for item in video.get("side_data_list", [])):
        raise SmartCutError("display rotation requires the accurate timeline route")
    if audio and (audio.get("codec_name") != "aac" or int(audio.get("sample_rate", 0)) <= 0):
        raise SmartCutError("audio must be AAC for this comparison")
    rate = Fraction(video.get("avg_frame_rate", "0/1"))
    if not rate or rate != Fraction(video.get("r_frame_rate", "0/1")) or rate > 120:
        raise SmartCutError("variable or unknown frame rate")
    frames = ffprobe(path, "-select_streams", "v:0", "-show_frames",
                     "-show_entries", "frame=best_effort_timestamp_time,key_frame").get("frames", [])
    if len(frames) < 3:
        raise SmartCutError("too few video frames")
    step = float(1 / rate)
    for index, frame in enumerate(frames):
        pts = float(frame["best_effort_timestamp_time"])
        if abs(pts - index * step) > min(0.002, step * 0.08):
            raise SmartCutError("variable frame timing or nonzero picture start")
    if not int(frames[0]["key_frame"]):
        raise SmartCutError("first frame is not a keyframe")
    return video, audio, frames, rate


def frame_index(value: float, rate: Fraction, count: int) -> int:
    index = round(value * float(rate))
    if not 0 <= index <= count or abs(value - index / float(rate)) > 0.002:
        raise SmartCutError("cut boundary must align to a decoded frame")
    return index


def retained_frames(duration: float, removals: list[str], rate: Fraction,
                    count: int) -> list[tuple[int, int]]:
    ranges = editing.cut_ranges(duration, removals)
    result = [(frame_index(start, rate, count), frame_index(end, rate, count))
              for start, end in ranges]
    if any(end <= start for start, end in result):
        raise SmartCutError("empty retained frame range")
    return result


def segments(ranges: list[tuple[int, int]], keyframes: list[int]) -> list[tuple[str, int, int]]:
    result = []
    for start, end in ranges:
        first = next((key for key in keyframes if key >= start), end)
        last = end if end > keyframes[-1] else max(
            (key for key in keyframes if key < end), default=start)
        if start < first:
            result.append(("encode", start, min(first, end)))
        middle_start = first if start < first else start
        middle_end = last if last > middle_start else middle_start
        if middle_start < middle_end:
            result.append(("copy", middle_start, middle_end))
        if middle_end < end:
            result.append(("encode", middle_end, end))
    if not any(kind == "copy" for kind, _, _ in result):
        raise SmartCutError("no complete GOP to copy; use the accurate edit route")
    return result


def packet_hashes(path: Path) -> list[dict]:
    packets = ffprobe(path, "-select_streams", "v:0", "-show_packets",
                      "-show_entries", "packet=data_hash,flags", "-show_data_hash", "sha256")
    return [packet for packet in packets.get("packets", []) if packet.get("data_hash")]


def copy_proof(source: Path, candidate: Path,
               chunks: list[tuple[int, int, Path]], expected_count: int) -> dict:
    original, delivered = packet_hashes(source), packet_hashes(candidate)
    if len(delivered) != expected_count:
        raise SmartCutError("candidate packet count differs from retained frame count")
    copied = 0
    rewritten_headers = 0
    source_hashes = [packet["data_hash"] for packet in original]
    for offset, expected, path in chunks:
        hashes = packet_hashes(path)
        if len(hashes) != expected or not hashes:
            raise SmartCutError("copied GOP packet count differs from the plan")
        sequence = tuple(packet["data_hash"] for packet in hashes)
        if not any(tuple(source_hashes[i:i + len(hashes)]) == sequence
                   for i in range(len(original) - len(hashes) + 1)):
            raise SmartCutError("copied GOP packets do not match source")
        for index, packet in enumerate(hashes):
            actual = delivered[offset + index]
            if actual["data_hash"] == packet["data_hash"]:
                copied += 1
            elif "K" in packet.get("flags", ""):
                # MP4 concat may rewrite SPS/PPS at any keyframe, while the
                # untouched interframes must remain byte-identical.
                rewritten_headers += 1
            else:
                raise SmartCutError("copied GOP interior packets changed in candidate")
    return {"identical_interior_packets": copied, "rewritten_first_packets": rewritten_headers}


def frame_proof(source: Path, candidate: Path, ranges: list[tuple[int, int]],
                width: int, height: int) -> tuple[int, float]:
    expected = sum(end - start for start, end in ranges)
    delivered = ffprobe(candidate, "-select_streams", "v:0", "-count_frames",
                        "-show_entries", "stream=nb_read_frames")["streams"][0]
    if int(delivered.get("nb_read_frames", -1)) != expected:
        raise SmartCutError("decoded candidate frame count differs from retained source")
    graph = []
    for index, (start, end) in enumerate(ranges):
        graph.append(f"[0:v]trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS[r{index}]")
    labels = "".join(f"[r{index}]" for index in range(len(ranges)))
    graph.append(f"{labels}concat=n={len(ranges)}:v=1:a=0[reference]")
    shared = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error"]
    source_args = [*shared, "-i", str(source), "-filter_complex", ";".join(graph),
                   "-map", "[reference]"]
    candidate_args = [*shared, "-i", str(candidate), "-map", "0:v:0"]
    tail = ["-fps_mode", "passthrough", "-pix_fmt", "yuv420p", "-f", "rawvideo", "-"]
    frame_bytes = width * height * 3 // 2
    luma_bytes = width * height
    maximum_error = 0.0
    # Compare by decoded frame ordinal. FFmpeg framesync matches by PTS and
    # can pair the wrong frames after mixed timebase concat segments.
    reference = subprocess.Popen([*source_args, *tail], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
    actual = subprocess.Popen([*candidate_args, *tail], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    try:
        assert reference.stdout and actual.stdout
        for _ in range(expected):
            left = reference.stdout.read(frame_bytes)
            right = actual.stdout.read(frame_bytes)
            if len(left) != frame_bytes or len(right) != frame_bytes:
                raise SmartCutError("decoded candidate frame count is incomplete")
            # Sampling luma every 16 pixels bounds comparison cost for 4K
            # media while still checking every decoded frame, including joins.
            error = sum(abs(left[i] - right[i]) for i in range(0, luma_bytes, 16))
            score = error / math.ceil(luma_bytes / 16)
            maximum_error = max(maximum_error, score)
            if score > 4.0:
                raise SmartCutError("candidate frame differs from retained source")
        if reference.stdout.read(1) or actual.stdout.read(1):
            raise SmartCutError("decoded candidate has extra frames")
        if reference.wait() or actual.wait():
            raise SmartCutError("decoded frame comparison failed")
    finally:
        # A failed comparison can leave an encoder blocked on stdout; stop it
        # before waiting so verification itself cannot stall the workflow.
        for process in (reference, actual):
            if process.poll() is None:
                process.kill()
            process.communicate()
    return expected, maximum_error


def pcm_window(path: Path, filter_graph: str | None, label: str | None,
               start: float, end: float) -> array:
    args = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(path)]
    if filter_graph:
        args += ["-filter_complex", filter_graph, "-map", label or "0:a:0"]
    else:
        args += ["-map", "0:a:0", "-af",
                 f"atrim=start={start:.9f}:end={end:.9f},asetpts=PTS-STARTPTS"]
    args += ["-ac", "1", "-ar", "48000", "-f", "s16le", "-"]
    process = subprocess.run(args, capture_output=True)
    if process.returncode:
        raise SmartCutError("audio boundary decode failed")
    samples = array("h")
    samples.frombytes(process.stdout)
    return samples


def audio_proof(source: Path, candidate: Path, ranges: list[tuple[int, int]],
                rate: Fraction, expected: float, has_audio: bool) -> dict:
    info = ffprobe(candidate, "-show_streams")
    streams = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if len(streams) != int(has_audio):
        raise SmartCutError("candidate audio stream count differs")
    if not has_audio:
        return {"status": "not_present"}
    stream = streams[0]
    duration = float(stream.get("duration") or 0)
    start = float(stream.get("start_time") or 0)
    if abs(duration - expected) > max(0.07, float(2 / rate)) or abs(start) > 0.05:
        raise SmartCutError("candidate audio start or duration differs from edit")
    joins = []
    position = 0.0
    for first, last in ranges[:-1]:
        position += (last - first) / float(rate)
        joins.append(position)
    boundaries = [0.0, *joins, expected]
    scores = []
    for boundary in boundaries:
        window_start, window_end = max(0.0, boundary - 0.08), min(expected, boundary + 0.08)
        graph = []
        for index, (first, last) in enumerate(ranges):
            graph.append(f"[0:a:0]atrim=start={first / float(rate):.9f}:"
                         f"end={last / float(rate):.9f},asetpts=PTS-STARTPTS[a{index}]")
        graph.append("".join(f"[a{i}]" for i in range(len(ranges)))
                     + f"concat=n={len(ranges)}:v=0:a=1[whole]")
        graph.append(f"[whole]atrim=start={window_start:.9f}:end={window_end:.9f},"
                     "asetpts=PTS-STARTPTS[window]")
        reference = pcm_window(source, ";".join(graph), "[window]",
                               window_start, window_end)
        actual = pcm_window(candidate, None, None, window_start, window_end)
        count = min(len(reference), len(actual))
        if count < 100 or abs(len(reference) - len(actual)) > 1024:
            raise SmartCutError("audio boundary samples are incomplete")
        left, right = reference[:count], actual[:count]
        left_energy = sum(value * value for value in left)
        right_energy = sum(value * value for value in right)
        if left_energy < count * 100 and right_energy < count * 100:
            score = 1.0  # Both bounded windows are effectively silent.
        elif not left_energy or not right_energy:
            raise SmartCutError("audio boundary has unexpected silence")
        else:
            score = sum(a * b for a, b in zip(left, right)) / math.sqrt(
                left_energy * right_energy)
        if score < 0.94:
            raise SmartCutError("audio boundary correlation failed")
        scores.append({"at_seconds": round(boundary, 6), "correlation": round(score, 5)})
    return {"status": "checked", "start_seconds": start, "duration_seconds": duration,
            "boundary_windows": scores}


def render(source: Path, output: Path, report: Path, removals: list[str]) -> dict:
    if not source.is_file() or output.exists() or output.resolve() == source.resolve():
        raise SmartCutError("source must exist and output must be a new path")
    if output.suffix.lower() != ".mp4" or not removals:
        raise SmartCutError("requires an MP4 candidate and at least one cut")
    video, audio, frames, rate = source_profile(source)
    duration = len(frames) / float(rate)
    ranges = retained_frames(duration, removals, rate, len(frames))
    parts = segments(ranges, [i for i, frame in enumerate(frames) if int(frame["key_frame"])])
    expected = sum(end - start for start, end in ranges) / float(rate)
    retained_count = sum(end - start for start, end in ranges)
    copied_count = sum(end - start for kind, start, end in parts if kind == "copy")
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256()
    with source.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
    digest = sha.hexdigest()
    evidence = {"status": "REVIEW", "source": str(source.resolve()), "source_sha256": digest,
                "candidate": str(output.resolve()), "removed": removals,
                "retained_frames": ranges, "segments": parts,
                "issue": "cuts-only edit would reencode every retained picture frame on the accurate route",
                "baseline": {"route": "accurate-cut", "picture_frames_reencoded": retained_count},
                "candidate_plan": {"picture_frames_reencoded": retained_count - copied_count,
                                   "picture_frames_to_copy": copied_count,
                                   "copy_fraction": round(copied_count / retained_count, 4)},
                "acceptance": {"copied_interior_packets": "byte-identical apart from keyframe headers",
                               "decoded_picture": "every frame sampled-luma MAE <= 4",
                               "audio_joins": "correlation >= 0.94 and start/duration aligned"},
                "human_boundary_review": "pending",
                "exact_master_review": "pending",
                "fallback": "content.py edit cut (accurate timeline route)"}
    if copied_count / retained_count < 0.5:
        evidence.update(status="SKIP", reason="less than half the retained picture can be copied")
        report.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        return evidence
    try:
        with tempfile.TemporaryDirectory(prefix="smart-cut-", dir=output.parent) as temporary:
            scratch = Path(temporary)
            pieces = []
            copied = []
            output_packet_index = 0
            for index, (kind, start, end) in enumerate(parts):
                path = scratch / f"part-{index:03d}.mp4"
                if kind == "copy":
                    # Seeking to an independently decodable keyframe preserves full interior packets.
                    args = ["-ss", f"{start / float(rate):.9f}", "-i", str(source),
                            "-map", "0:v:0", "-an", "-frames:v", str(end - start),
                            "-c:v", "copy", "-avoid_negative_ts", "make_zero"]
                    copied.append((output_packet_index, end - start, path))
                else:
                    args = ["-i", str(source), "-map", "0:v:0", "-an",
                            "-vf", f"trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS",
                            "-frames:v", str(end - start), "-c:v", "libx264", "-preset", "fast",
                            "-crf", "10", "-pix_fmt", "yuv420p", "-r", str(rate)]
                run_command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                             *args, str(path)])
                pieces.append(path)
                output_packet_index += end - start
            playlist = scratch / "pieces.txt"
            playlist.write_text("".join(f"file '{path.as_posix()}'\n" for path in pieces),
                                encoding="utf-8")
            stitched = scratch / "picture.mp4"
            run_command(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                         "-f", "concat", "-safe", "0", "-i", str(playlist),
                         "-map", "0:v:0", "-c:v", "copy", str(stitched)])
            candidate = scratch / "candidate.mp4"
            args = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(stitched)]
            if audio:
                args += ["-i", str(source)]
                graph = []
                for index, (start, end) in enumerate(ranges):
                    graph.append(f"[1:a:0]atrim=start={start / float(rate):.9f}:"
                                 f"end={end / float(rate):.9f},asetpts=PTS-STARTPTS[a{index}]")
                graph.append("".join(f"[a{i}]" for i in range(len(ranges)))
                             + f"concat=n={len(ranges)}:v=0:a=1[aout]")
                args += ["-filter_complex", ";".join(graph), "-map", "0:v:0",
                         "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
            else:
                args += ["-map", "0:v:0"]
            args += ["-c:v", "copy", "-movflags", "+faststart", str(candidate)]
            run_command(args)
            # A comparison candidate is retained even if a proof fails, but is
            # never marked usable without all checks passing.
            os.replace(candidate, output)
            evidence["copied_packets"] = copy_proof(source, output, copied,
                                                   output_packet_index)
            count, maximum = frame_proof(source, output, ranges,
                                         int(video["width"]), int(video["height"]))
            evidence["frame_proof"] = {"decoded_count": count,
                                       "maximum_sampled_luma_mae": maximum}
            evidence["audio_proof"] = audio_proof(source, output, ranges, rate,
                                                  expected, bool(audio))
            sha = hashlib.sha256()
            with output.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    sha.update(block)
            evidence["candidate_sha256"] = sha.hexdigest()
            evidence["status"] = "PASS_CANDIDATE"
    except (SmartCutError, OSError, ValueError) as exc:
        evidence["reason"] = str(exc)
    report.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--remove", required=True, action="append", help="frame-aligned START-END")
    parser.add_argument("--out", required=True, type=Path, help="new MP4 comparison candidate")
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = render(args.input, args.out, args.report, args.remove)
    except SmartCutError as exc:
        result = {"status": "UNSUPPORTED", "source": str(args.input.resolve()),
                  "candidate": str(args.out.resolve()), "removed": args.remove,
                  "reason": str(exc),
                  "fallback": "content.py edit cut (accurate timeline route)"}
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{result['status']}: {result.get('reason', args.report)}")
    return 0 if result["status"] == "PASS_CANDIDATE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
