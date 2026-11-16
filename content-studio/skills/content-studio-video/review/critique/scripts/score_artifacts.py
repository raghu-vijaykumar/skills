"""Report editorial scores and review coverage for a video package."""

import argparse
import json
from pathlib import Path

from score_objects import has_text


ARTIFACT_AXES = {
    "script": ("factual_accuracy", "hook", "rehooks", "clarity", "variety", "payoff"),
    "storyboard": ("cue_design", "visible_causality", "framing", "visual_variety"),
    "hero": ("form", "material", "staging"),
    "animation": ("mechanics", "timing", "continuity", "motion_readability"),
    "narration": ("intelligibility", "pacing", "emphasis", "variety", "sync"),
    "audio": ("voice_balance", "noise", "dynamics", "continuity"),
    "captions": ("text_accuracy", "timing", "legibility"),
    "music": ("fit", "edit_timing", "balance"),
    "sfx": ("fit", "sync", "balance"),
    "thumbnail": ("legibility", "focal_subject", "promise"),
    "source_project": ("rebuildability", "traceability"),
    "master": ("hook", "rehooks", "variety", "payoff", "continuity"),
}


def assess_item(item):
    item_id = item["id"]
    if not has_text(item_id) or item["kind"] not in ARTIFACT_AXES:
        raise ValueError("Each artifact needs a stable ID and a recognized kind")
    state = item["state"]
    if state in ("pending", "not_generated", "not_applicable"):
        if "ratings" in item or not has_text(item.get("reason")):
            raise ValueError(f"{item_id}: an unscored artifact needs a reason and no ratings")
        return {**item, "status": state}
    if state != "scored" or not has_text(item.get("evidence")):
        raise ValueError(f"{item_id}: score against a specific artifact or record why it is unscored")
    ratings = item["ratings"]
    if set(ratings) != set(ARTIFACT_AXES[item["kind"]]):
        raise ValueError(f"{item_id}: supply each axis for {item['kind']}")
    for axis, rating in ratings.items():
        score = rating.get("score")
        if type(score) is not int or not 1 <= score <= 5 or not has_text(rating.get("observation")):
            raise ValueError(f"{item_id}/{axis}: supply a score from 1 to 5 and a located observation")
    blockers = item.get("blockers", [])
    if not isinstance(blockers, list) or not all(map(has_text, blockers)):
        raise ValueError(f"{item_id}: blockers must list concrete issues")
    # A strong hook or attractive shot cannot compensate for wrong facts or captions.
    below = [axis for axis, rating in ratings.items()
             if rating["score"] < (4 if axis in ("factual_accuracy", "text_accuracy") else 3)]
    status = "revise" if below or blockers else "ready_for_review"
    if status == "revise" and not has_text(item.get("retest")):
        raise ValueError(f"{item_id}: specify a correction and a retest")
    return {**item, "status": status, "below_floor": below,
            "average": round(sum(rating["score"] for rating in ratings.values()) / len(ratings), 2)}


def summarize(ledger, previous=None):
    if not all(has_text(ledger.get(key)) for key in ("audience", "scope")):
        raise ValueError("State the audience and selected review scope")
    rows = [assess_item(item) for item in ledger["artifacts"]]
    if not rows or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Supply a nonempty inventory of unique artifact IDs")
    if previous:
        if any(ledger[key] != previous[key] for key in ("scope", "audience")):
            raise ValueError("Keep the audience and scope stable when comparing scores")
        earlier = {row["id"]: row for row in previous["artifacts"]}
        for row in rows:
            old = earlier.get(row["id"])
            if old is None:
                continue
            if old["kind"] != row["kind"]:
                raise ValueError(f"{row['id']}: keep the artifact kind stable")
            if row["state"] == old["state"] == "scored":
                row["axis_change"] = {
                    axis: rating["score"] - old["ratings"][axis]["score"] for axis, rating in row["ratings"].items()
                }
    counts = {state: sum(row["status"] == state for row in rows)
              for state in ("ready_for_review", "revise", "pending", "not_generated", "not_applicable")}
    return {**ledger, "artifacts": rows, "counts": counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8-sig"))
        previous = json.loads(args.previous.read_text(encoding="utf-8-sig")) if args.previous else None
        report = summarize(ledger, previous)
        with args.out.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except (KeyError, TypeError, ValueError, AttributeError, OSError) as error:
        parser.exit(1, f"Artifact review failed: {error}\n")
    print(", ".join(f"{count} {state}" for state, count in report["counts"].items()))


if __name__ == "__main__":
    main()
