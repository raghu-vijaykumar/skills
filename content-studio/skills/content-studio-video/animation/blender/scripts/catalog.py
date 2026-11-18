"""Validate Blender routes and select only scene examples with matching evidence."""

import argparse
import hashlib
import json
import re
from pathlib import Path

BLENDER = Path(__file__).resolve().parents[1]
CONTENT_STUDIO = BLENDER.parents[3]
REPO = CONTENT_STUDIO.parent
MANIFEST = json.loads((BLENDER / "capabilities.json").read_text(encoding="utf-8"))
STYLE_CATEGORIES = {"Core styles", "Extended styles", "Horror packs"}
UPSTREAM = ("https://github.com/arjun988/blender-skills/blob/"
            f"{MANIFEST['upstream_commit']}/.claude/skills")
STATUSES = {"Catalogued", "Prototype", "Rendered", "Integrated"}
PINNED_COMMIT = "904f095d8f36a6e72adaebb08d07f884a074743d"
SCORE_FIELDS = {"subject_fidelity", "motion_readability", "composition",
                "finish", "evidence_integrity"}


def scorebook(book=None):
    """Require a scored, technically valid winner before a GIF can prove a route."""
    if book is None:
        book = json.loads((BLENDER / "scores.json").read_text(encoding="utf-8"))
    weights = book.get("weights", {})
    if (book.get("schema_version") != 1 or set(weights) != SCORE_FIELDS
            or any(not isinstance(weight, int) or weight <= 0 for weight in weights.values())
            or sum(weights.values()) != 100 or
            type(book.get("minimum_score")) is not int or
            not 0 <= book["minimum_score"] <= 100):
        raise ValueError("Invalid gallery scoring rubric")
    winners = {}
    for route, group in book.get("routes", {}).items():
        candidates = group.get("candidates", [])
        ids = [candidate.get("id") for candidate in candidates]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError(f"Each gallery candidate needs a unique ID: {route}")
        for candidate in candidates:
            scores = candidate.get("scores", {})
            if (set(scores) != SCORE_FIELDS or
                    any(type(value) is not int or not 0 <= value <= 5
                        for value in scores.values())):
                raise ValueError(f"Every candidate needs five 0–5 scores: {route}")
            total = round(sum(scores[key] * weight for key, weight in weights.items()) / 5)
            if candidate.get("score_total") != total:
                raise ValueError(f"Incorrect total score for {candidate['id']}")
            if (type(candidate.get("technical_pass")) is not bool or
                    not isinstance(candidate.get("video_frames"), int) or
                    candidate["video_frames"] < 1 or
                    not isinstance(candidate.get("video_resolution"), list) or
                    len(candidate["video_resolution"]) != 2 or
                    any(type(value) is not int or value < 1
                        for value in candidate["video_resolution"])):
                raise ValueError(f"Missing technical review for {candidate['id']}")
            for field in ("video_sha256", "gif_sha256"):
                if not re.fullmatch(r"[a-f0-9]{64}", candidate.get(field, "")):
                    raise ValueError(f"Missing {field} for {candidate['id']}")
            for field in ("reviewer", "review_date", "review_note"):
                if not isinstance(candidate.get(field), str) or not candidate[field].strip():
                    raise ValueError(f"Missing {field} for {candidate['id']}")
        eligible = [candidate for candidate in candidates
                    if candidate["technical_pass"] and
                    candidate["score_total"] >= book.get("minimum_score", 70)]
        selected = next((candidate for candidate in eligible
                         if candidate["id"] == group.get("selected")), None)
        if not selected or selected["score_total"] != max(
                candidate["score_total"] for candidate in eligible):
            raise ValueError(f"Selected gallery artifact is not the best passing result: {route}")
        relative = selected.get("gif_path")
        if not isinstance(relative, str) or not relative.startswith("previews/"):
            raise ValueError(f"Selected artifact needs a committed GIF: {route}")
        gif = (BLENDER / relative).resolve()
        gif_bytes = gif.read_bytes() if gif.is_relative_to(BLENDER) and gif.is_file() else b""
        if (not gif_bytes.startswith((b"GIF87a", b"GIF89a")) or
                hashlib.sha256(gif_bytes).hexdigest() != selected["gif_sha256"]):
            raise ValueError(f"Selected GIF is missing or has changed: {route}")
        winners[route] = selected
    return winners


def catalog():
    """Reject unsupported status claims and broken references before publishing them."""
    entries = MANIFEST.get("entries", [])
    names = [entry["id"] for entry in entries]
    if (MANIFEST.get("schema_version") != 2 or MANIFEST.get("upstream_commit") != PINNED_COMMIT
            or len(names) != 94 or len(set(names)) != 94):
        raise ValueError("The capability manifest must contain 94 unique skill IDs")
    known = set(names)
    subject_ids = {entry["id"] for entry in entries if entry["category"] == "Modeling"}
    winners = scorebook()
    visual_gifs = {}
    for entry in entries:
        name = entry["id"]
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
            raise ValueError(f"Invalid Blender skill ID: {name}")
        if entry.get("route") != "content-studio-video-animation":
            raise ValueError(f"Unknown Content Studio route for {name}")
        if entry.get("status") not in STATUSES or not isinstance(entry.get("wave"), int):
            raise ValueError(f"Invalid status or wave for {name}")
        dependencies = entry.get("dependencies")
        if (not isinstance(dependencies, list) or len(dependencies) != len(set(dependencies))
                or name in dependencies or any(dependency not in known for dependency in dependencies)):
            raise ValueError(f"Invalid dependencies for {name}")
        method = entry.get("method")
        if entry["status"] == "Catalogued" and (method or entry.get("evidence")
                                                or entry.get("builder")):
            raise ValueError(f"Catalogued guidance cannot claim a renderer: {name}")
        if entry["status"] in {"Prototype", "Rendered", "Integrated"}:
            if method != "blender-shot":
                raise ValueError(f"Executable entry lacks a supported method: {name}")
            for field in (("builder", "spec") if entry["status"] == "Prototype" else
                          ("evidence", "review", "builder", "spec")):
                relative = entry.get(field)
                if not relative or not (BLENDER / relative).is_file():
                    raise ValueError(f"Executable entry lacks {field}: {name}")
        if entry["status"] in {"Rendered", "Integrated"}:
            winner = winners.get(name)
            if (entry.get("score_record") != "scores.json" or not winner or
                    winner["gif_path"] != entry["evidence"]):
                raise ValueError(f"Rendered route lacks a scored winning GIF: {name}")
            if entry["category"] in STYLE_CATEGORIES:
                previous = visual_gifs.setdefault(entry["evidence"], name)
                if previous != name:
                    raise ValueError(f"Visual styles need distinct GIFs: {previous}, {name}")
        allowed_subjects = entry.get("compatible_subjects")
        if allowed_subjects is not None and (not isinstance(allowed_subjects, list)
                                             or not allowed_subjects or
                                             any(subject not in subject_ids for subject in allowed_subjects)):
            raise ValueError(f"Invalid compatible subjects for {name}")
        if entry["status"] == "Integrated":
            proof = entry.get("integration_proof")
            if not proof or not (BLENDER / proof).is_file():
                raise ValueError(f"Integrated entry lacks production proof: {name}")
        entry["source"] = f"{UPSTREAM}/{name}/SKILL.md"
    # Prerequisites must be acyclic so future wave runners can schedule routes safely.
    graph = {entry["id"]: entry["dependencies"] for entry in entries}
    visited, visiting = set(), set()
    def visit(name):
        if name in visiting:
            raise ValueError(f"Dependency cycle at {name}")
        if name in visited:
            return
        visiting.add(name)
        for dependency in graph[name]:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
    for name in graph:
        visit(name)
    return entries


def route(prompt, style=None, subject=None):
    """Give an inspectable default; a catalogue route is never a render claim."""
    text = prompt.lower()
    entries = catalog()
    subject_rules = [
        (r"\b(vehicle|car|truck|aircraft|spaceship)\b", "vehicle-artist"),
        (r"\b(creature|monster|dragon|animal)\b", "creature-artist"),
        (r"\b(character|person|human|mascot|courier)\b", "character-artist"),
        (r"\b(tree|plant|vegetation|forest)\b", "vegetation-artist"),
        (r"\b(room|corridor|environment|landscape|building)\b", "environment-artist"),
        (r"\b(machine|mechanism|clamp|robot|industrial)\b", "hard-surface"),
        (r"\b(prop|object|product|furniture|lamp|chair|bottle)\b", "prop-artist"),
    ]
    subjects = {entry["id"] for entry in entries if entry["category"] == "Modeling"}
    if subject is not None and subject not in subjects:
        raise ValueError(f"Unknown Blender subject: {subject}")
    subject = subject or next((name for pattern, name in subject_rules if re.search(pattern, text)),
                              "blender-modeler")
    styles = {e["id"] for e in entries if e["category"] in STYLE_CATEGORIES}
    if style is not None:
        if style not in styles:
            raise ValueError(f"Unknown Blender style: {style}")
        chosen = style
        reason = "explicit style"
    else:
        style_rules = [
            (r"\b(horror|creepy|haunted|scary)\b", "horror-style"),
            (r"\banime\b", "anime-style"),
            (r"\b(cel.shaded|cartoon|toon)\b", "cartoon-style"),
            (r"\b(atmospheric|stylized)\b", "stylized-style"),
            (r"\b(pixel|sprite)\b", "pixel-art-style"),
            (r"\b(isometric|iso camera|diorama|city.builder)\b", "isometric-style"),
            (r"\b(voxel|minecraft|blocky)\b", "voxel-style"),
            (r"\b(low.poly|lowpoly)\b", "lowpoly-style"),
        ]
        chosen = next((name for pattern, name in style_rules if re.search(pattern, text)),
                      "stylized-style" if subject in {"character-artist", "prop-artist"}
                      or (subject == "blender-modeler" and "lamp" in text) else "realistic-style")
        reason = "selected from subject and visual intent"
    # A rendered demo is reusable only for its declared subject, intent, and treatment.
    entry = next((item for item in entries if item["id"] == subject), None)
    style_entry = next((item for item in entries if item["id"] == chosen), None)
    cue_matches = lambda item: any(re.search(rf"\b{re.escape(cue)}\b", text)
                                   for cue in item.get("intent_cues", []))
    # A demonstrated style-specific builder takes priority over a generic subject demo.
    if (style_entry and style_entry["status"] in {"Rendered", "Integrated"}
            and subject in style_entry.get("compatible_subjects", []) and cue_matches(style_entry)):
        entry = style_entry
        matched = True
    else:
        matched = (entry and entry["status"] in {"Rendered", "Integrated"}
                   and chosen in entry.get("compatible_styles", []) and cue_matches(entry))
    return {"subject": subject, "style": chosen, "reason": reason,
            "status": entry["status"] if matched else "Catalogued",
            "render_method": entry["method"] if matched else None,
            "builder": entry["builder"] if matched else None,
            "spec": entry["spec"] if matched else None,
            "evidence": entry["evidence"] if matched else None,
            "review_required": True}


def markdown_table(entries):
    lines = ["| Category | Skill | Content Studio route | Status | Render evidence |",
             "| --- | --- | --- | --- | --- |"]
    for entry in entries:
        route = entry["method"] or f"Planned wave {entry['wave']}"
        evidence = (f"[GIF](content-studio/skills/content-studio-video/animation/blender/"
                    f"{entry['evidence']})" if entry.get("evidence") else "Pending")
        lines.append(f"| {entry['category']} | [`{entry['id']}`]({entry['source']}) | "
                     f"{route} | {entry['status']} | {evidence} |")
    return "\n".join(lines)


def sync_readme(entries):
    """Update only the generated catalog region of the main README."""
    path = REPO / "README.md"
    body = path.read_text(encoding="utf-8")
    start = "<!-- blender-catalog:start -->"
    end = "<!-- blender-catalog:end -->"
    if body.count(start) != 1 or body.count(end) != 1:
        raise ValueError("README must contain exactly one Blender catalog marker pair")
    before, rest = body.split(start, 1)
    _, after = rest.split(end, 1)
    updated = before + start + "\n" + markdown_table(entries) + "\n" + end + after
    path.write_text(updated, encoding="utf-8")
    print(f"Updated {path} with {len(entries)} capability rows")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list")
    plan = sub.add_parser("plan")
    plan.add_argument("prompt")
    plan.add_argument("--style")
    plan.add_argument("--subject")
    sub.add_parser("readme-table")
    sub.add_parser("sync-readme")
    sub.add_parser("scores")
    args = parser.parse_args()
    entries = catalog()
    if args.action == "list":
        print(json.dumps(entries, indent=2))
    elif args.action == "plan":
        print(json.dumps(route(args.prompt, args.style, args.subject), indent=2))
    elif args.action == "readme-table":
        print(markdown_table(entries))
    elif args.action == "scores":
        book = json.loads((BLENDER / "scores.json").read_text(encoding="utf-8"))
        print(json.dumps({route: {"selected": winner["id"],
                                  "score": winner["score_total"],
                                  "candidates": len(book["routes"][route]["candidates"])}
                          for route, winner in scorebook(book).items()}, indent=2))
    else:
        sync_readme(entries)


if __name__ == "__main__":
    main()
