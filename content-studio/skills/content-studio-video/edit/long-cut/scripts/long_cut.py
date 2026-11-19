"""Plan a source-order long cut from reviewed blur, pan, and tilt candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path

SCHEMA = "content-studio.long-cut.v1"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def write_new(path: Path, value: dict) -> None:
    # Keep each review revision available; a rerun must choose a new file.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def probe(source: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(source)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise ValueError(f"ffprobe failed for {source.name}: {result.stderr[-400:]}")
    data = json.loads(result.stdout)
    video = next((item for item in data.get("streams", []) if item.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError(f"No video in {source.name}")
    fps = Fraction(video.get("avg_frame_rate", "0/1"))
    nominal = Fraction(video.get("r_frame_rate", "0/1"))
    duration = float(data.get("format", {}).get("duration", 0))
    if not fps or fps != nominal or not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"Long cut needs positive-duration constant-frame-rate media: {source.name}")
    if (video.get("color_transfer") in {"smpte2084", "arib-std-b67"}
            or video.get("color_primaries") == "bt2020"
            or "dovi" in json.dumps(video.get("side_data_list", [])).lower()
            or "10" in str(video.get("pix_fmt", ""))
            or "12" in str(video.get("pix_fmt", ""))):
        raise ValueError(f"HDR/Dolby Vision picture cuts lack a supported one-render route: {source.name}")
    if (int(video.get("tags", {}).get("rotate", 0))
            or any(int(side.get("rotation", 0)) for side in video.get("side_data_list", []))):
        raise ValueError(f"Display rotation needs a reviewed normalization route: {source.name}")
    # A container duration can include a few audio samples beyond picture.
    # Use the reported frame count for exact cut bounds when it exists.
    frames = video.get("nb_frames")
    frames = int(frames) if str(frames).isdigit() else round(duration * float(fps))
    return {"fps": float(fps), "duration_s": duration, "frames": frames,
            "width": int(video["width"]), "height": int(video["height"])}


def ordered_sources(draft: Path) -> tuple[Path, list[tuple[Path, str]]]:
    order_file = draft / ".content-studio" / "_timeline.csv"
    with order_file.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not {"order", "new_name", "original_name"}.issubset(reader.fieldnames or []):
            raise ValueError("Capture-order CSV lacks required columns")
        rows = list(reader)
    if not rows:
        raise ValueError("Capture-order CSV is empty")
    numbers = [int(row["order"]) for row in rows]
    if sorted(numbers) != list(range(1, len(rows) + 1)):
        raise ValueError("Capture order must be unique and consecutive")
    ordered = []
    names = set()
    original_root = (draft / "original").resolve()
    for row in sorted(rows, key=lambda item: int(item["order"])):
        name = row["new_name"]
        source = (original_root / name).resolve()
        if (not name or Path(name).name != name or source.parent != original_root
                or source.suffix.lower() not in VIDEO_EXTENSIONS or not source.is_file()
                or name.casefold() in names):
            raise ValueError(f"Unsafe, duplicate, or missing ordered source: {name}")
        names.add(name.casefold())
        stable = row["original_name"]
        if not stable or Path(stable).name != stable:
            raise ValueError(f"Invalid original camera name: {stable}")
        ordered.append((source, stable))
    actual = {p.name.casefold() for p in original_root.iterdir()
              if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS}
    if actual != names:
        raise ValueError("Capture-order CSV does not cover exactly the camera files in original/")
    return order_file.resolve(), ordered


def report_index(folder: Path, kind: str) -> dict[Path, tuple[Path, dict]]:
    index = {}
    for path in folder.glob("*.json"):
        report = read_json(path)
        if not report.get("source") or not isinstance(report.get("candidates"), list):
            continue
        if report.get("schema") != f"content-studio.{kind}-candidates.v1":
            raise ValueError(f"Wrong {kind} scan schema: {path}")
        source = Path(report["source"]).resolve()
        if source in index:
            raise ValueError(f"Multiple {kind} reports for {source.name}; choose one report set")
        index[source] = (path.resolve(), report)
    return index


def add_candidate(candidates: list[dict], *, kind: str, identity: str,
                  start: int, end: int, frames: int, evidence: Path,
                  evidence_sha256: str) -> None:
    if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= frames:
        raise ValueError(f"Invalid {kind} candidate bounds: {identity}")
    candidates.append({"id": f"{kind}-{identity}", "kind": kind,
                       "start_frame": start, "end_frame": end,
                       "cut_start_frame": start, "cut_end_frame": end,
                       "evidence": str(evidence), "evidence_sha256": evidence_sha256,
                       "decision": "pending_review", "actor": "", "reviewer": "",
                       "review_note": ""})


def proposal_value(draft: Path, fastpan_dir: Path, tilt_dir: Path) -> dict:
    draft = draft.resolve(strict=True)
    order_file, ordered = ordered_sources(draft)
    indexes = {"fastpan": report_index(fastpan_dir.resolve(strict=True), "fastpan"),
               "tilt": report_index(tilt_dir.resolve(strict=True), "tilt")}
    sources = []
    for source, stable in ordered:
        info = probe(source)
        digest = sha256_file(source)
        candidates = []
        blur_dir = draft / ".content-studio" / "analysis" / "source-review" / stable
        blur_report = read_json(blur_dir / "report.json")
        blur_csv = blur_dir / "review.csv"
        if blur_report.get("source_sha256") != digest or not blur_csv.is_file():
            raise ValueError(f"Blur evidence changed or is missing: {source.name}")
        blur_hash = sha256_file(blur_csv)
        with blur_csv.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            if not {"id", "start", "end"}.issubset(reader.fieldnames or []):
                raise ValueError(f"Invalid blur review CSV: {blur_csv}")
            for row in reader:
                start = max(0, math.floor(float(row["start"]) * info["fps"]))
                end = min(info["frames"], math.ceil(float(row["end"]) * info["fps"]))
                add_candidate(candidates, kind="blur", identity=row["id"],
                              start=start, end=end, frames=info["frames"],
                              evidence=blur_csv.resolve(), evidence_sha256=blur_hash)
        for kind, index in indexes.items():
            if source not in index:
                raise ValueError(f"Missing {kind} scan for {source.name}")
            path, report = index[source]
            if (report.get("source_sha256") != digest
                    or abs(float(report.get("fps", 0)) - info["fps"]) > .001):
                raise ValueError(f"Stale {kind} scan for {source.name}")
            evidence_hash = sha256_file(path)
            for row in report["candidates"]:
                add_candidate(candidates, kind=kind, identity=str(row["id"]),
                              start=row["start_frame"], end=row["end_frame"],
                              frames=info["frames"], evidence=path,
                              evidence_sha256=evidence_hash)
        if len({row["id"] for row in candidates}) != len(candidates):
            raise ValueError(f"Duplicate candidate ID for {source.name}")
        sources.append({"source": str(source), "source_sha256": digest,
                        **info, "candidates": sorted(candidates,
                                                     key=lambda row: (row["start_frame"], row["id"]))})
    value = {"schema": SCHEMA, "draft": str(draft), "order_file": str(order_file),
             "order_sha256": sha256_file(order_file),
             "fastpan_dir": str(fastpan_dir.resolve()), "tilt_dir": str(tilt_dir.resolve()),
             "sources": sources}
    return value


def propose(draft: Path, fastpan_dir: Path, tilt_dir: Path, out: Path) -> dict:
    value = proposal_value(draft, fastpan_dir, tilt_dir)
    write_new(out, value)
    return {"proposal": str(out), "sources": len(value["sources"]),
            "candidates": sum(len(row["candidates"]) for row in value["sources"])}


def kept_spans(frames: int, cuts: list[tuple[int, int]]) -> list[tuple[int, int]]:
    # Merge overlapping reasons so each surviving camera frame appears once.
    merged = []
    for start, end in sorted(cuts):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    kept = []
    cursor = 0
    for start, end in merged:
        if cursor < start:
            kept.append((cursor, start))
        cursor = end
    if cursor < frames:
        kept.append((cursor, frames))
    return kept


def build(manifest_path: Path, out: Path) -> dict:
    manifest = read_json(manifest_path)
    if manifest.get("schema") != SCHEMA or not isinstance(manifest.get("sources"), list):
        raise ValueError("Unsupported long-cut review manifest")
    # Reconstruct every detector candidate from its current evidence. Human
    # cut bounds are editable, but the detector's own bounds remain immutable.
    fresh = proposal_value(Path(manifest["draft"]), Path(manifest["fastpan_dir"]),
                           Path(manifest["tilt_dir"]))
    for field in ("draft", "order_file", "order_sha256", "fastpan_dir", "tilt_dir"):
        if manifest.get(field) != fresh[field]:
            raise ValueError(f"Long-cut source evidence changed: {field}")
    if len(manifest["sources"]) != len(fresh["sources"]):
        raise ValueError("Long-cut source list changed since proposal")
    for reviewed, original in zip(manifest["sources"], fresh["sources"]):
        if {key: value for key, value in reviewed.items() if key != "candidates"} != {
                key: value for key, value in original.items() if key != "candidates"}:
            raise ValueError("Long-cut source metadata changed since proposal")
        if len(reviewed.get("candidates", [])) != len(original["candidates"]):
            raise ValueError("Long-cut candidate list changed since proposal")
        for selected, baseline in zip(reviewed["candidates"], original["candidates"]):
            for field in ("id", "kind", "start_frame", "end_frame", "evidence",
                          "evidence_sha256"):
                if selected.get(field) != baseline[field]:
                    raise ValueError(f"Long-cut candidate changed: {baseline['id']}")
    draft = Path(manifest["draft"]).resolve(strict=True)
    order_file, ordered = ordered_sources(draft)
    if (Path(manifest["order_file"]).resolve() != order_file
            or sha256_file(order_file) != manifest.get("order_sha256")
            or len(ordered) != len(manifest["sources"])):
        raise ValueError("Capture order changed since long-cut review")
    picture = []
    removed = 0.0
    for index, ((source, _), reviewed) in enumerate(zip(ordered, manifest["sources"]), 1):
        info = probe(source)
        if (Path(reviewed["source"]).resolve() != source
                or reviewed.get("source_sha256") != sha256_file(source)
                or reviewed.get("frames") != info["frames"]
                or abs(float(reviewed.get("fps", 0)) - info["fps"]) > .001):
            raise ValueError(f"Source changed since long-cut review: {source.name}")
        cuts = []
        seen = set()
        for candidate in reviewed.get("candidates", []):
            identity = candidate.get("id")
            start, end = candidate.get("start_frame"), candidate.get("end_frame")
            if (not isinstance(identity, str) or identity in seen
                    or type(start) is not int or type(end) is not int
                    or not 0 <= start < end <= info["frames"]):
                raise ValueError(f"Invalid candidate in {source.name}: {identity}")
            seen.add(identity)
            evidence = Path(candidate["evidence"]).resolve()
            if not evidence.is_file() or sha256_file(evidence) != candidate.get("evidence_sha256"):
                raise ValueError(f"Candidate evidence changed: {identity}")
            if candidate.get("decision") not in {"cut", "keep"}:
                raise ValueError(f"Candidate still needs review: {identity}")
            if (candidate.get("actor") != "human"
                    or not str(candidate.get("reviewer", "")).strip()
                    or not str(candidate.get("review_note", "")).strip()):
                raise ValueError(f"Candidate lacks a human decision: {identity}")
            if candidate["decision"] == "cut":
                cut_start = candidate.get("cut_start_frame")
                cut_end = candidate.get("cut_end_frame")
                if (type(cut_start) is not int or type(cut_end) is not int
                        or not 0 <= cut_start < cut_end <= info["frames"]
                        or cut_start >= end or cut_end <= start):
                    raise ValueError(f"Reviewed cut bounds are invalid or miss the candidate: {identity}")
                cuts.append((cut_start, cut_end))
        spans = kept_spans(info["frames"], cuts)
        removed += (info["frames"] - sum(end - start for start, end in spans)) / info["fps"]
        for start, end in spans:
            picture.append({"id": f"long-{index:04d}-{len(picture) + 1:05d}",
                            "source": source.name, "sha256": reviewed["source_sha256"],
                            "source_in": round(start / info["fps"], 6),
                            "source_out": round(min(end / info["fps"], info["duration_s"]), 6)})
    if not picture:
        raise ValueError("All footage would be removed")
    if any(clip["source_out"] <= clip["source_in"] for clip in picture):
        raise ValueError("A retained span is too short for the delivery timeline")
    write_new(out, {"picture": picture, "transitions": [], "operations": [], "audio": [],
                    "audio_policy": "mix", "video_policy": "encode", "color_policy": "sdr"})
    return {"changes": str(out), "picture_spans": len(picture),
            "removed_seconds": round(removed, 3)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    proposal = actions.add_parser("propose", help="Gather source-linked cut candidates")
    for name in ("draft", "fastpan-dir", "tilt-dir", "out"):
        proposal.add_argument(f"--{name}", type=Path, required=True)
    approved = actions.add_parser("build", help="Make timeline changes from human-reviewed decisions")
    approved.add_argument("--manifest", type=Path, required=True)
    approved.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = (propose(args.draft, args.fastpan_dir, args.tilt_dir, args.out)
                  if args.action == "propose" else build(args.manifest, args.out))
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Long cut {args.action} failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
