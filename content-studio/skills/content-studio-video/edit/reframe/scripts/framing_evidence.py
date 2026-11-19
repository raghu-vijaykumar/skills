"""Measure portrait crop loss and subject clearance, then draw destination guides."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _overlap(a: dict, b: dict) -> float:
    width = max(0.0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    height = max(0.0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    return width * height


def _subject_samples(boxes: list[dict], source_name: str, start: float,
                     end: float, crop: dict) -> list[dict]:
    matching = [item for item in boxes if Path(str(item.get("source", ""))).name == source_name]
    times = {start + (end - start) * portion for portion in
             (0.01, .1, .25, .5, .75, .9, .99)}
    for item in matching:
        left, right = float(item["start"]), float(item["end"])
        if right > start and left < end:
            times.add(max(start, left) + min(.02, (min(end, right) - max(start, left)) / 2))
            times.add(min(end, right) - min(.02, (min(end, right) - max(start, left)) / 2))
    samples = []
    safe = {"x": crop["x"] + crop["w"] * .1,
            "y": crop["y"] + crop["h"] * .1,
            "w": crop["w"] * .8, "h": crop["h"] * .8}
    for at in sorted(times):
        active = [item for item in matching if float(item["start"]) <= at < float(item["end"])]
        if not active:
            samples.append({"at_seconds": round(at, 3), "status": "REVIEW",
                            "reason": "No supplied hero box at this time"})
            continue
        for item in active:
            box = {key: float(item["box"][key]) for key in ("x", "y", "w", "h")}
            if (not all(math.isfinite(value) for value in box.values())
                    or box["w"] <= 0 or box["h"] <= 0):
                raise ValueError("Subject box geometry is invalid")
            coverage = _overlap(box, crop) / (box["w"] * box["h"])
            clearance = _overlap(box, safe) / (box["w"] * box["h"])
            center_x = box["x"] + box["w"] / 2
            screen_x = (center_x - crop["x"]) / crop["w"]
            samples.append({"at_seconds": round(at, 3),
                            "label": str(item.get("label", "hero")),
                            "coverage_fraction": round(coverage, 4),
                            "safe_zone_fraction": round(clearance, 4),
                            "screen_center_x": round(screen_x, 4),
                            "status": "REVIEW" if coverage < .98 or clearance < .8 else "SKIP"})
    return samples


def _guides(proposal_dir: Path) -> list[dict]:
    guides = []
    for index, cropped in enumerate(sorted((proposal_dir / "preview").glob("cropped-*.jpg"))):
        with Image.open(cropped) as raw:
            frame = raw.convert("RGB")
        width, height = frame.size
        draw = ImageDraw.Draw(frame)
        for fraction, color in ((.05, "yellow"), (.1, "cyan")):
            draw.rectangle((round(width * fraction), round(height * fraction),
                            round(width * (1 - fraction)), round(height * (1 - fraction))),
                           outline=color, width=max(2, round(width * .006)))
        path = proposal_dir / "preview" / f"safe-zone-{index:02d}.png"
        frame.save(path)
        guides.append({"path": str(path.resolve()), "sha256": sha256_file(path),
                       "source_preview": str(cropped.resolve())})
    return guides


def analyze(source: Path, proposal_path: Path, output: Path,
            subjects: Path | None = None) -> dict:
    source, proposal_path, output = source.resolve(), proposal_path.resolve(), output.resolve()
    if not source.is_file() or not proposal_path.is_file() or output.exists():
        raise ValueError("Source/proposal missing or framing report already exists")
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    if proposal.get("source") != source.name:
        raise ValueError("Framing proposal belongs to another source")
    crop = proposal["crop"]
    if any(not 0 <= float(crop[key]) <= 1 for key in ("x", "y", "w", "h")):
        raise ValueError("Crop geometry is invalid")
    start, end = (float(value) for value in proposal["range"])
    boxes = None
    if subjects:
        subjects = subjects.resolve()
        payload = json.loads(subjects.read_text(encoding="utf-8-sig"))
        boxes = payload.get("subjects", payload.get("segments", [])) if isinstance(payload, dict) else payload
        if not isinstance(boxes, list):
            raise ValueError("Subject boxes must be a list")
    samples = _subject_samples(boxes, source.name, start, end, crop) if boxes is not None else []
    centers = [item["screen_center_x"] for item in samples if "screen_center_x" in item]
    guides = _guides(proposal_path.parent)
    report = {"schema": "content-studio.framing-evidence.v1",
              "source_sha256": sha256_file(source),
              "proposal_sha256": sha256_file(proposal_path),
              "subjects_sha256": sha256_file(subjects) if subjects else None,
              "range": [start, end], "crop": crop,
              "context_lost_fraction": round(1 - float(crop["w"]) * float(crop["h"]), 4),
              "subject_samples": samples,
              "minimum_hero_coverage": min((item["coverage_fraction"] for item in samples
                                             if "coverage_fraction" in item), default=None),
              "screen_center_motion": round(max(centers) - min(centers), 4) if centers else None,
              "guide_frames": guides,
              "hero_coverage_status": ("UNSUPPORTED" if boxes is None else
                                        "REVIEW" if not samples or any(
                                            item["status"] == "REVIEW" for item in samples)
                                        else "SKIP"),
              "human_review_required": True}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--subjects", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.source, args.proposal, args.output, args.subjects), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
