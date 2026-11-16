"""Report paired, evidence-backed art and animation ratings for authored objects."""

import argparse
import json
from pathlib import Path


APPEARANCE = ("form", "material", "staging")
MOTION = ("mechanics", "timing", "continuity")


def group(values, axes):
    if not isinstance(values, dict) or set(values) != set(axes):
        raise ValueError(f"Expected scores for {', '.join(axes)}")
    if any(type(value) is not int or not 1 <= value <= 5 for value in values.values()):
        raise ValueError("Score each axis with an integer from 1 to 5")
    return values


def assess(entry):
    name = entry["id"]
    a = entry["reference"]
    b = entry["candidate"]
    for side in (a, b):
        if side is not None and any(not isinstance(side.get(key), str) or not side[key].strip()
                                    for key in ("evidence", "observation")):
            raise ValueError(f"{name}: supply evidence and an observation for each side")
    fix = entry.get("revision")
    change = {}
    category_scores = {}
    for category, axes in (("appearance", APPEARANCE), ("motion", MOTION)):
        reference = a[category]
        candidate = b[category] if b is not None else None
        if category == "motion" and reference is None and candidate is None:
            continue
        if reference is None:
            raise ValueError(f"{name}: rate motion on both sides when testing motion")
        reference = group(reference, axes)
        candidate = group(candidate, axes) if candidate is not None else {}
        category_scores[category] = {
            "reference": round(sum(reference.values()) / len(axes), 2),
            "candidate": round(sum(candidate.values()) / len(axes), 2),
        }
        change.update({axis: candidate.get(axis, 0) - reference[axis] for axis in axes})
    deficits = sorted((axis for axis, delta in change.items() if delta < 0), key=change.get)
    status = "missing" if b is None else "improve" if deficits else (
        "better" if any(value > 0 for value in change.values()) else "matched"
    )
    if deficits and (not isinstance(fix, str) or not fix.strip()):
        raise ValueError(f"{name}: give each below-reference object a concrete revision and retest")
    return {**entry, "status": status, "deficits": deficits, "axis_deltas": change,
            "category_scores": category_scores}


def summarize(ledger, prior=None):
    rows = ledger["objects"]
    if not rows:
        raise ValueError("Supply a nonempty objects list")
    ids = [entry["id"] for entry in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Object IDs must be unique")
    assessed = [assess(entry) for entry in rows]
    if prior is not None:
        old = {entry["id"]: entry for entry in prior["objects"]}
        for row in assessed:
            previous = old.get(row["id"])
            if previous is not None:
                if any(row["reference"][category] != previous["reference"][category]
                       for category in ("appearance", "motion")):
                    raise ValueError(f"{row['id']}: keep the same reference ratings for a retest")
                row["change_since_review"] = {
                    axis: delta - previous["axis_deltas"][axis]
                    for axis, delta in row["axis_deltas"].items()
                    if axis in previous["axis_deltas"]
                }
    return {
        "objects": assessed,
        "counts": {status: sum(row["status"] == status for row in assessed)
                   for status in ("missing", "improve", "matched", "better")},
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--ledger", required=True, type=Path)
    cli.add_argument("--previous", type=Path)
    cli.add_argument("--out", required=True, type=Path)
    args = cli.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8-sig"))
        prior = json.loads(args.previous.read_text(encoding="utf-8-sig")) if args.previous else None
        report = summarize(ledger, prior)
        with args.out.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except (KeyError, TypeError, ValueError, OSError) as error:
        cli.exit(1, f"Object score failed: {error}\n")
    print(", ".join(f"{count} {status}" for status, count in report["counts"].items()))


if __name__ == "__main__":
    main()
