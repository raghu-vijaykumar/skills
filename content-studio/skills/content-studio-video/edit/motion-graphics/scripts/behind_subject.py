#!/usr/bin/env python3
"""Expand one or more rising text-behind-subject cues into timeline changes."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "timeline" / "scripts"))
import model  # noqa: E402

PRESET = json.loads((Path(__file__).resolve().parents[1] / "presets" /
                     "text-behind-subject.json").read_text(encoding="utf-8"))


def build_changes(timeline: dict, cues: list[dict]) -> dict:
    if not isinstance(cues, list) or not cues:
        raise ValueError("Cues must be a nonempty array")
    root = Path(timeline["source_root"]).resolve()
    resolved = model.validate(timeline, require_review=False)
    operations = copy.deepcopy(timeline.get("operations", []))
    existing = {item["id"] for item in operations}
    for cue in cues:
        if not isinstance(cue, dict):
            raise ValueError("Each cue must be an object")
        cue_id = cue.get("id")
        if not isinstance(cue_id, str) or not cue_id or cue_id in existing:
            raise ValueError(f"Duplicate or missing cue ID: {cue_id}")
        existing.add(cue_id)
        font = model.asset_path(root, cue.get("font_source"))
        matte = model.asset_path(root, cue.get("matte_source"))
        provenance = matte.with_suffix(".json")
        if provenance.is_file():
            record = json.loads(provenance.read_text(encoding="utf-8"))
            shot = next((clip for clip in resolved["clips"]
                         if clip["start"] <= cue.get("start", -1)
                         and cue.get("end", -1) <= clip["end"]), None)
            if shot is None:
                raise ValueError(f"Cue {cue_id} does not fit one source shot")
            source_start = shot["source_in"] + cue["start"] - shot["start"]
            if (record.get("source_sha256") != shot["sha256"]
                    or abs(float(record.get("start", -1)) - source_start) > .04
                    or abs(float(record.get("duration", -1))
                           - (cue["end"] - cue["start"])) > .04
                    or record.get("matte_sha256") != model.sha256_file(matte)):
                raise ValueError(f"Matte provenance does not match cue {cue_id}")
        operation = {
            "id": cue_id, "method": "text-behind-subject",
            "start": cue.get("start"), "end": cue.get("end"),
            "text": cue.get("text"),
            "font_source": cue["font_source"], "font_sha256": model.sha256_file(font),
            "matte_source": cue["matte_source"], "matte_sha256": model.sha256_file(matte),
            "rise_seconds": cue.get("rise_seconds", PRESET["defaults"]["rise_seconds"]),
            "from_y": cue.get("from_y", PRESET["defaults"]["from_y"]),
            "to_y": cue.get("to_y", PRESET["defaults"]["to_y"]),
            "font_height": cue.get("font_height", PRESET["defaults"]["font_height"]),
            "review_status": "pending_review",
        }
        operations.append(operation)
    # Validate the complete proposed timeline before writing a review file.
    proposed = copy.deepcopy(timeline)
    proposed["operations"] = operations
    model.validate(proposed, require_review=False)
    return {"operations": operations}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--cues", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    changes = build_changes(model.load(args.timeline),
                            json.loads(args.cues.read_text(encoding="utf-8"))["cues"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as target:
        json.dump(changes, target, indent=2, ensure_ascii=False)
        target.write("\n")
    print(json.dumps({"changes": str(args.out), "cues": len(changes["operations"])},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
