"""Report evidence-backed teaching scores without inferring student comprehension."""

import argparse
import json
from pathlib import Path

from score_objects import has_text


FLOORS = {"accuracy": 4, "causality": 3, "motion_readability": 3, "language": 3}
CHECKS = ("identify", "predict", "explain")


def assess_beat(beat):
    beat_id = beat["id"]
    if not all(has_text(beat.get(key)) for key in ("id", "objective", "evidence")):
        raise ValueError("Each beat needs a stable ID, learning objective, and render evidence")
    axes = beat["axes"]
    if set(axes) != set(FLOORS):
        raise ValueError(f"{beat_id}: supply all teaching axes")
    for axis, rating in axes.items():
        score = rating.get("score")
        if type(score) is not int or not 1 <= score <= 5 or not has_text(rating.get("observation")):
            raise ValueError(f"{beat_id}/{axis}: supply a score from 1 to 5 and an observation")
    blockers = beat["blockers"]
    if not isinstance(blockers, list) or not all(map(has_text, blockers)):
        raise ValueError(f"{beat_id}: blockers must list any factual or misleading-motion gaps")
    checks = beat["checks"]
    if set(checks) != set(CHECKS):
        raise ValueError(f"{beat_id}: supply identify, predict, and explain questions")
    answered = 0
    missed = []
    for kind, check in checks.items():
        if not all(has_text(check.get(key)) for key in ("question", "expected")):
            raise ValueError(f"{beat_id}/{kind}: supply a question and expected answer")
        result = check.get("learner_result")
        if result is None:
            continue
        if type(result.get("met")) is not bool or not has_text(result.get("evidence")):
            raise ValueError(f"{beat_id}/{kind}: a learner result needs a decision and observation")
        answered += 1
        if not result["met"]:
            missed.append(kind)
    scores = {axis: rating["score"] for axis, rating in axes.items()}
    below = [axis for axis, minimum in FLOORS.items() if scores[axis] < minimum]
    needs_revision = bool(blockers or below or missed)
    if needs_revision and not has_text(beat.get("retest")):
        raise ValueError(f"{beat_id}: name a concrete revision and visible retest")
    # Keep an expert's editorial judgment separate from observed learner results.
    return {**beat, "average": round(sum(scores.values()) / len(scores), 2),
            "below_floor": below, "editorial": "revise" if needs_revision else "ready_for_review",
            "comprehension": "needs_revision" if missed else "demonstrated" if answered == len(CHECKS)
            else "not_tested" if answered == 0 else "partial",
            "answered_checks": answered}


def summarize(ledger, previous=None):
    if not has_text(ledger.get("audience")) or not has_text(ledger.get("render")):
        raise ValueError("Supply the intended audience and the exact render or render manifest")
    rows = [assess_beat(beat) for beat in ledger["beats"]]
    if not rows or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Supply a nonempty list of unique beat IDs")
    if previous:
        if previous["audience"] != ledger["audience"]:
            raise ValueError("Keep the same audience for a retest")
        earlier = {beat["id"]: beat for beat in previous["beats"]}
        for row in rows:
            old = earlier.get(row["id"])
            if old is None:
                continue
            keys = ("question", "expected")
            if row["objective"] != old["objective"] or any(
                row["checks"][kind][key] != old["checks"][kind][key] for kind in CHECKS for key in keys
            ):
                raise ValueError(f"{row['id']}: changed teaching objective or comprehension checks")
            row["axis_change"] = {axis: row["axes"][axis]["score"] - old["axes"][axis]["score"] for axis in FLOORS}
    return {**ledger, "beats": rows}


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
        parser.exit(1, f"Teaching review failed: {error}\n")
    for row in report["beats"]:
        print(f"{row['id']}: {row['average']}/5, {row['editorial']}, learner checks {row['comprehension']}")


if __name__ == "__main__":
    main()
