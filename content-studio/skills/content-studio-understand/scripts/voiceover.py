#!/usr/bin/env python3
"""Validate, time, and render an evidence-linked voiceover script for review.

The script author is still the vision-capable agent and the human. This tool
checks the authored JSON against the evidence manifest, estimates speaking
pace, and produces a clean review copy plus a teleprompter text file.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def timecode(seconds):
    seconds = max(0.0, float(seconds))
    minutes, remainder = divmod(int(round(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{remainder:02d}"
    return f"{minutes:02d}:{remainder:02d}"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def count_words(text):
    return len(
        [token for token in str(text).split() if any(char.isalnum() for char in token)]
    )


def validate(script, evidence=None, max_wps=3.4, min_wps=0.4, max_gap=30.0):
    """Return a review report; never mutates the source script."""
    errors = []
    warnings = []

    if not isinstance(script, dict):
        return {
            "status": "fail",
            "errors": ["voiceover script must be a JSON object"],
            "warnings": [],
            "segments": [],
        }

    segments = script.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("segments must be a non-empty array")
        segments = []

    duration = None
    evidence_frames = {}
    source_sha = script.get("source_sha256")
    if evidence is not None:
        if not isinstance(evidence, dict):
            errors.append("evidence must be a JSON object")
        else:
            if evidence.get("duration_seconds") is not None:
                try:
                    duration = float(evidence["duration_seconds"])
                except (TypeError, ValueError):
                    errors.append("evidence duration_seconds is not a number")
            if (
                source_sha
                and evidence.get("source_sha256")
                and source_sha != evidence["source_sha256"]
            ):
                errors.append("source_sha256 does not match the evidence manifest")
            for frame in evidence.get("frames", []):
                if isinstance(frame, dict) and frame.get("id"):
                    evidence_frames[frame["id"]] = frame

    if duration is None and script.get("duration_seconds") is not None:
        try:
            duration = float(script["duration_seconds"])
        except (TypeError, ValueError):
            errors.append("duration_seconds is not a number")
    if duration is None:
        warnings.append("No duration available; segment ends were not range-checked")

    details = []
    seen_ids = set()
    previous_end = None
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            errors.append(f"segment {index + 1} must be an object")
            continue
        segment_id = str(segment.get("id") or f"v{index + 1:02d}")
        if segment_id in seen_ids:
            errors.append(f"{segment_id}: duplicate segment id")
        seen_ids.add(segment_id)

        text = str(segment.get("text") or "").strip()
        if not text:
            errors.append(f"{segment_id}: text is empty")

        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"{segment_id}: start and end must be numbers")
            continue

        if start < 0:
            errors.append(f"{segment_id}: start is before zero")
        if end <= start:
            errors.append(f"{segment_id}: end must be after start")
        if duration is not None and start > duration + 0.5:
            errors.append(f"{segment_id}: start is after the video ends")
        if duration is not None and end > duration + 0.5:
            errors.append(f"{segment_id}: end is after the video ends")
        if previous_end is not None and start < previous_end - 0.05:
            errors.append(
                f"{segment_id}: overlaps the previous segment "
                f"(starts {start:.2f}s, previous ends {previous_end:.2f}s)"
            )
        previous_end = max(previous_end or end, end)

        slot = max(0.0, end - start)
        words = count_words(text)
        wps = words / slot if slot else 0.0
        if wps > max_wps:
            errors.append(
                f"{segment_id}: {wps:.2f} words/sec exceeds {max_wps:.2f}; "
                "shorten the text or extend the slot"
            )
        if slot >= 5 and wps < min_wps:
            warnings.append(
                f"{segment_id}: only {wps:.2f} words/sec; add detail or shorten the slot"
            )

        evidence_ids = segment.get("evidence_frame_ids") or []
        if not isinstance(evidence_ids, list):
            errors.append(f"{segment_id}: evidence_frame_ids must be an array")
            evidence_ids = []
        for frame_id in evidence_ids:
            if evidence_frames and frame_id not in evidence_frames:
                errors.append(f"{segment_id}: unknown evidence frame {frame_id}")
        if not evidence_ids:
            warnings.append(f"{segment_id}: no evidence_frame_ids")

        needs_review = bool(segment.get("needs_review", True))
        details.append(
            {
                "id": segment_id,
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(slot, 3),
                "text": text,
                "words": words,
                "words_per_second": round(wps, 3),
                "evidence_frame_ids": evidence_ids,
                "needs_review": needs_review,
                "direction": str(segment.get("direction") or "").strip(),
                "notes": str(segment.get("notes") or "").strip(),
            }
        )

    if details:
        if details[0]["start"] > max_gap:
            warnings.append(
                f"{details[0]['start']:.1f}s of silence before the first line"
            )
        for previous, current in zip(details, details[1:]):
            gap = current["start"] - previous["end"]
            if gap > max_gap:
                warnings.append(
                    f"{gap:.1f}s gap between {previous['id']} and {current['id']}"
                )
        if duration is not None and duration - details[-1]["end"] > max_gap:
            warnings.append(
                f"{duration - details[-1]['end']:.1f}s of silence after the last line"
            )

    narrated = sum(segment["duration"] for segment in details)
    total_words = sum(segment["words"] for segment in details)
    review_segments = [
        segment["id"] for segment in details if segment["needs_review"]
    ]
    status = "fail" if errors else (
        "review" if warnings or review_segments else "pass"
    )
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "source_sha256": source_sha,
        "duration_seconds": duration,
        "segment_count": len(details),
        "narrated_seconds": round(narrated, 3),
        "total_words": total_words,
        "average_words_per_second": round(total_words / narrated, 3)
        if narrated
        else None,
        "coverage_ratio": round(narrated / duration, 3)
        if duration
        else None,
        "review_segments": review_segments,
        "segments": details,
    }


def _quoted(text):
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines())


def render_markdown(script, report, title=None):
    script_title = title or script.get("title") or "Voiceover script"
    language = script.get("language") or "not specified"
    lines = [
        f"# {script_title}",
        "",
        f"**Status:** {report['status'].upper()}",
        f"**Language:** {language}",
        f"**Source duration:** {timecode(report['duration_seconds'])}"
        if report.get("duration_seconds")
        else "**Source duration:** unknown",
        f"**Segments:** {report.get('segment_count', 0)}",
        f"**Narrated:** {timecode(report.get('narrated_seconds', 0))}",
        f"**Average pace:** {report.get('average_words_per_second', 0):.2f} words/sec"
        if report.get("average_words_per_second")
        else "**Average pace:** unknown",
    ]
    if report.get("review_segments"):
        lines.append(
            "**Review flags:** " + ", ".join(report["review_segments"])
        )
    lines += [
        "",
        "Timestamps are start cues, not hard cuts. Read naturally; leave a short",
        "breath between sections. Lines marked `REVIEW` need a human fact-check.",
        "",
    ]
    if report.get("errors"):
        lines += ["## Errors", ""] + [f"- {item}" for item in report["errors"]] + [""]
    if report.get("warnings"):
        lines += ["## Warnings", ""] + [f"- {item}" for item in report["warnings"]] + [""]

    for segment in report.get("segments", []):
        heading = (
            f"## {timecode(segment['start'])}-{timecode(segment['end'])}"
            f" · {segment['id']}"
        )
        if segment["needs_review"]:
            heading += " · REVIEW"
        lines += [heading, ""]
        if segment.get("direction"):
            lines += [f"*Direction:* {segment['direction']}", ""]
        lines += [_quoted(segment["text"]), ""]
        meta = (
            f"*Pace:* {segment['words']} words / "
            f"{segment['duration']:.1f}s = {segment['words_per_second']:.2f} wps"
        )
        if segment["evidence_frame_ids"]:
            meta += " · *Evidence:* " + ", ".join(segment["evidence_frame_ids"])
        lines += [meta, ""]
        if segment.get("notes"):
            lines += [f"*Note:* {segment['notes']}", ""]
    return "\n".join(lines).rstrip() + "\n"


def render_teleprompter(report):
    lines = []
    for segment in report.get("segments", []):
        lines += [f"[{timecode(segment['start'])}] {segment['text']}", ""]
    return "\n".join(lines).rstrip() + "\n"


def render_csv(report, path):
    with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "id",
                "start",
                "end",
                "start_timecode",
                "end_timecode",
                "text",
                "needs_review",
            ]
        )
        for segment in report.get("segments", []):
            writer.writerow(
                [
                    segment["id"],
                    segment["start"],
                    segment["end"],
                    timecode(segment["start"]),
                    timecode(segment["end"]),
                    segment["text"],
                    segment["needs_review"],
                ]
            )


def write_outputs(script, report, out, title=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    markdown_path = out / "voiceover.md"
    teleprompter_path = out / "voiceover-teleprompter.txt"
    csv_path = out / "voiceover.csv"
    report_path = out / "voiceover-report.json"
    markdown_path.write_text(
        render_markdown(script, report, title=title), encoding="utf-8"
    )
    teleprompter_path.write_text(render_teleprompter(report), encoding="utf-8")
    render_csv(report, csv_path)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return {
        "markdown": str(markdown_path),
        "teleprompter": str(teleprompter_path),
        "csv": str(csv_path),
        "report": str(report_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate and render an evidence-linked voiceover script."
    )
    parser.add_argument("--input", required=True, help="authored voiceover JSON")
    parser.add_argument("--evidence", help="evidence.json from understand.py")
    parser.add_argument(
        "--out", help="output folder (defaults to the voiceover JSON folder)"
    )
    parser.add_argument("--title")
    parser.add_argument("--max-wps", type=float, default=3.4)
    parser.add_argument("--min-wps", type=float, default=0.4)
    parser.add_argument("--max-gap", type=float, default=30.0)
    parser.add_argument(
        "--allow-errors",
        action="store_true",
        help="write review files even when validation finds errors",
    )
    args = parser.parse_args()

    script_path = Path(args.input).resolve()
    script = load_json(script_path)
    evidence = load_json(args.evidence) if args.evidence else None
    report = validate(
        script,
        evidence,
        max_wps=args.max_wps,
        min_wps=args.min_wps,
        max_gap=args.max_gap,
    )
    out = Path(args.out).resolve() if args.out else script_path.parent
    outputs = write_outputs(script, report, out, title=args.title)
    print(
        json.dumps(
            {
                "status": report["status"],
                "errors": len(report["errors"]),
                "warnings": len(report["warnings"]),
                "segments": report.get("segment_count", 0),
                "outputs": outputs,
            },
            indent=2,
        )
    )
    if report["status"] == "fail" and not args.allow_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
