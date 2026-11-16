"""Report paired, evidence-backed art and animation ratings for authored objects."""

import argparse
import json
from pathlib import Path


APPEARANCE = ("form", "material", "staging")
MOTION = ("mechanics", "timing", "continuity")
DOCUMENTED_MOTION = ("photo-sequence", "documented-mechanism", "measured-capture")


def group(values, axes):
    if not isinstance(values, dict) or set(values) != set(axes):
        raise ValueError(f"Expected scores for {', '.join(axes)}")
    if any(type(value) is not int or not 1 <= value <= 5 for value in values.values()):
        raise ValueError("Score each axis with an integer from 1 to 5")
    return values


def has_text(value):
    return isinstance(value, str) and bool(value.strip())


def photo_basis(reference):
    if "photos" not in reference and "motion_basis" not in reference:
        return None
    photos = reference.get("photos")
    if not isinstance(photos, list) or not photos or any(
        not isinstance(photo, dict) or not all(has_text(photo.get(key)) for key in ("evidence", "shows"))
        for photo in photos
    ):
        raise ValueError("Supply real-world photo evidence and say what each view shows")
    basis = reference.get("motion_basis")
    kind = basis.get("kind") if isinstance(basis, dict) else None
    if kind in ("static", "unverified"):
        if reference["motion"] is not None:
            raise ValueError(f"A {kind} motion basis cannot supply reference motion scores")
    elif kind in DOCUMENTED_MOTION:
        states = basis.get("states")
        if not has_text(basis.get("evidence")) or not isinstance(states, list) or len(states) < 2 or any(
            not has_text(state) for state in states
        ):
            raise ValueError("Supply motion evidence and at least two ordered, inspectable states")
        if kind == "photo-sequence" and len({photo["evidence"] for photo in photos}) < 2:
            raise ValueError("A photo sequence must identify at least two distinct views of the operation")
        group(reference["motion"], MOTION)
    else:
        raise ValueError("Declare a static, unverified, photo-sequence, documented-mechanism or measured-capture motion basis")
    return kind


def assess(entry):
    name = entry["id"]
    a = entry["reference"]
    b = entry["candidate"]
    for side in (a, b):
        if side is not None and not all(has_text(side.get(key)) for key in ("evidence", "observation")):
            raise ValueError(f"{name}: supply evidence and an observation for each side")
    basis = photo_basis(a)
    if basis == "static" and b is not None and b["motion"] is not None:
        raise ValueError(f"{name}: use an animation basis for an actor whose motion is scored")
    fix = entry.get("revision")
    change = {}
    category_scores = {}
    for category, axes in (("appearance", APPEARANCE), ("motion", MOTION)):
        reference = a[category]
        candidate = b[category] if b is not None else None
        if category == "motion" and basis == "unverified":
            # A candidate can be rated on its own craft while the motion benchmark is open.
            category_scores["motion"] = {"reference": None, "candidate": (
                round(sum(group(candidate, axes).values()) / len(axes), 2) if candidate is not None else None
            )}
            continue
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
    if b is None:
        status = "missing"
    elif deficits:
        status = "improve"
    elif basis == "unverified":
        status = "review"
    else:
        status = "better" if any(value > 0 for value in change.values()) else "matched"
    if status in ("missing", "improve", "review") and not has_text(fix):
        raise ValueError(f"{name}: give each open object a concrete revision and retest")
    result = {**entry, "status": status, "deficits": deficits, "axis_deltas": change,
              "category_scores": category_scores}
    if basis is not None:
        result["motion_review"] = basis
    return result


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
                added_motion_basis = previous.get("motion_review") == "unverified" and row.get("motion_review") in DOCUMENTED_MOTION
                if row["reference"]["appearance"] != previous["reference"]["appearance"] or (
                    not added_motion_basis and row["reference"]["motion"] != previous["reference"]["motion"]
                ):
                    raise ValueError(f"{row['id']}: keep the same reference ratings for a retest")
                row["change_since_review"] = {
                    axis: delta - previous["axis_deltas"][axis]
                    for axis, delta in row["axis_deltas"].items()
                    if axis in previous["axis_deltas"]
                }
    statuses = ("missing", "improve", "matched", "better")
    if any("motion_review" in row for row in assessed):
        statuses += ("review",)
    return {"objects": assessed, "counts": {status: sum(row["status"] == status for row in assessed)
                                           for status in statuses}}


def retest_checklist(report):
    def priority(row):
        # An absent object is a structural gap. Among existing objects,
        # an above-reference axis cannot erase a deficit on another axis.
        shortfall = sum(-value for value in row["axis_deltas"].values() if value < 0)
        return row["status"] != "missing", -shortfall, row["id"]

    open_rows = sorted((row for row in report["objects"] if row["status"] in ("missing", "improve", "review")), key=priority)
    total = len(open_rows)
    status_line = "1 object needs a retest." if total == 1 else f"{total} objects need a retest."
    lines = ["# Object retests", "", status_line, ""]
    for row in open_rows:
        title = " / ".join(str(row[key]) for key in ("film", "shot", "actor") if row.get(key))
        issues = [f"{axis} {row['axis_deltas'][axis]:+d}" for axis in row["deficits"]]
        if row.get("motion_review") == "unverified":
            issues.append("motion evidence pending")
        deltas = ", ".join(issues)
        revision = " ".join(row["revision"].split())
        lines.append(f"- [ ] {title or row['id']} ({row['status']}, {deltas}). {revision}")
        regressed = [axis for axis, change in row.get("change_since_review", {}).items() if change < 0]
        if regressed:
            lines.append(f"  Lower than the preceding review on {', '.join(regressed)}.")
    return "\n".join(lines).rstrip() + "\n"


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--ledger", required=True, type=Path)
    cli.add_argument("--previous", type=Path)
    cli.add_argument("--out", required=True, type=Path)
    cli.add_argument("--retests", type=Path, help="Also write a ranked Markdown checklist for open objects.")
    args = cli.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8-sig"))
        prior = json.loads(args.previous.read_text(encoding="utf-8-sig")) if args.previous else None
        report = summarize(ledger, prior)
        if args.retests and (args.retests.exists() or args.retests.resolve() == args.out.resolve()):
            raise ValueError("Use a separate new file for the retest checklist")
        with args.out.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        if args.retests:
            with args.retests.open("x", encoding="utf-8") as stream:
                stream.write(retest_checklist(report))
    except (KeyError, TypeError, ValueError, OSError) as error:
        cli.exit(1, f"Object score failed: {error}\n")
    print(", ".join(f"{count} {status}" for status, count in report["counts"].items()))


if __name__ == "__main__":
    main()
