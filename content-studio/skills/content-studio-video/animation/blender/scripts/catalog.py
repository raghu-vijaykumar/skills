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
WORLD_CATEGORY = "Worlds and moods"
VISUAL_CATEGORIES = STYLE_CATEGORIES | {WORLD_CATEGORY, "Genre direction", "Eras"}
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
            if entry["category"] in VISUAL_CATEGORIES:
                previous = visual_gifs.setdefault(entry["evidence"], name)
                if previous != name:
                    raise ValueError(f"Visual styles need distinct GIFs: {previous}, {name}")
        allowed_subjects = entry.get("compatible_subjects")
        if allowed_subjects is not None and (not isinstance(allowed_subjects, list)
                                             or not allowed_subjects or
                                             any(subject not in subject_ids for subject in allowed_subjects)):
            raise ValueError(f"Invalid compatible subjects for {name}")
        allowed_styles = entry.get("compatible_styles")
        style_ids = {item["id"] for item in entries
                     if item["category"] in STYLE_CATEGORIES}
        if allowed_styles is not None and (not isinstance(allowed_styles, list)
                                           or not allowed_styles or
                                           any(style not in style_ids for style in allowed_styles)):
            raise ValueError(f"Invalid compatible styles for {name}")
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


def route(prompt, style=None, subject=None, world=None):
    """Give an inspectable default; a catalogue route is never a render claim."""
    text = prompt.lower()
    entries = catalog()
    subject_rules = [
        (r"\b(vehicle|car|truck|aircraft|spaceship|rocket|boat|sailboat)\b", "vehicle-artist"),
        (r"\b(creature|monster|dragon|animal|butterfly|fox)\b", "creature-artist"),
        (r"(?=.*\b(?:alley|cyberpunk)\b)(?=.*\bdrone\b)", "environment-artist"),
        # A first-person camera cue does not make its environment a character shot.
        (r"\b(character|human|mascot|puppet|courier|heroine|detective|fedora|face|eye|hand|finger|digit|traveler|wanderer)\b|(?<!first[- ])\bperson\b", "character-artist"),
        (r"\b(cabin|trail|woodland|castle|keep|gate|drawbridge|moat)\b", "environment-artist"),
        (r"\b(alley|cyberpunk)\b", "environment-artist"),
        (r"\b(tree|plant|vegetation|forest|sprout|flower)\b", "vegetation-artist"),
        (r"\b(room|corridor|hallway|hall|environment|landscape|building|island|cottage|windmill|river|lake|aperture|portal|void|pool|poolrooms|mall|school|hotel|field|village|playground|nursery|playroom)\b", "environment-artist"),
        (r"\b(machine|mechanism|clamp|robot|industrial)\b", "hard-surface"),
        (r"\b(prop|object|product|furniture|lamp|chair|bottle|chest|teacup|dashboard|widget)\b", "prop-artist"),
    ]
    subjects = {entry["id"] for entry in entries if entry["category"] == "Modeling"}
    if subject is not None and subject not in subjects:
        raise ValueError(f"Unknown Blender subject: {subject}")
    subject = subject or next((name for pattern, name in subject_rules if re.search(pattern, text)),
                              "blender-modeler")
    worlds = {entry["id"] for entry in entries if entry["category"] == WORLD_CATEGORY}
    if world is not None and world not in worlds:
        raise ValueError(f"Unknown Blender world: {world}")
    # World direction is independent of visual style; infer only the demonstrated lane.
    selected_world = world or ("fantasy-worlds" if
                               re.search(r"\b(castle|keep|drawbridge|moat)\b", text)
                               else "sci-fi-punk-worlds" if
                               re.search(r"\bcyberpunk\b|\bneon alley\b", text)
                               else None)
    styles = {e["id"] for e in entries if e["category"] in STYLE_CATEGORIES}
    if style is not None:
        if style not in styles:
            raise ValueError(f"Unknown Blender style: {style}")
        chosen = style
        reason = "explicit style"
    else:
        style_rules = [
            (r"\b(cosmic.horror|eldritch|lovecraftian|void.horror)\b", "cosmic-eldritch-horror"),
            (r"\b(body.horror|mutation|mutating|flesh.fusion)\b", "body-horror-style"),
            (r"\b(analog.horror|found.footage|vhs|security.tape|training.tape)\b", "analog-found-footage-horror"),
            (r"\b(liminal|backrooms|poolrooms|empty.mall|empty.school)\b", "liminal-space-style"),
            (r"\b(folk.horror|rural.ritual|pastoral.dread|wicker.effigy)\b", "folk-horror-style"),
            (r"\b(mascot.horror|puppet.horror|felt.horror|costume.horror)\b", "mascot-puppet-horror"),
            (r"\b(dreamcore|weirdcore|traumacore|dream.horror|surreal.childhood)\b", "dream-weirdcore-style"),
            (r"\b(indie.horror|cabin.horror|forest.horror|corporate.horror|silent.hill|fear.to.fathom|puppet.combo)\b", "indie-horror-aesthetics"),
            (r"\b(psx|ps1|playstation 1|retro horror)\b", "psx-horror-style"),
            (r"\b(horror|creepy|haunted|scary)\b", "horror-style"),
            (r"\b(comic.book|comic|graphic.novel)\b", "comic-book-style"),
            (r"\bmanga\b", "manga-style"),
            (r"\b(hand.painted|painted texture|brushwork)\b", "hand-painted-style"),
            (r"\b(painterly|watercolor|oil.painting|impressionist|gouache)\b", "painterly-style"),
            (r"\b(stop.motion|claymation|paper.craft|papercraft|handmade)\b", "stop-motion-craft-style"),
            (r"\b(chibi|super.deformed)\b", "chibi-style"),
            (r"\b(noir|neo.noir|hardboiled)\b", "noir-style"),
            (r"\b(minimalist|minimal|negative.space)\b", "minimalist-style"),
            (r"\b(vector|flat.design|svg.like)\b", "vector-style"),
            (r"\b(8.bit|8bit|nes|four.color)\b", "retro-8bit-style"),
            (r"\b(16.bit|16bit|snes|genesis|mega.drive)\b", "retro-16bit-style"),
            (r"\b(hd.2d|hd2d|octopath|pixel.3d.hybrid)\b", "hd-2d-style"),
            (r"\b(frutiger.aero|aqua.ui|glossy.2000s)\b", "frutiger-aero-style"),
            (r"\banime\b", "anime-style"),
            (r"\b(cel.shaded|cartoon|toon)\b", "cartoon-style"),
            (r"\b(atmospheric|stylized)\b", "stylized-style"),
            (r"\b(pixel|sprite)\b", "pixel-art-style"),
            (r"\b(realistic|photoreal|photorealistic|pbr)\b", "realistic-style"),
            (r"\b(isometric|iso camera|diorama|city.builder)\b", "isometric-style"),
            (r"\b(voxel|minecraft|blocky)\b", "voxel-style"),
            (r"\b(low.poly|lowpoly)\b", "lowpoly-style"),
        ]
        # Demonstrated subjects can choose a reviewed treatment when no style is named.
        default_style = ("comic-book-style" if subject == "vehicle-artist" and
                         re.search(r"\brocket\b", text) else
                         "stop-motion-craft-style" if subject == "creature-artist" and
                         re.search(r"\bbutterfly\b", text) else
                         "chibi-style" if subject == "character-artist" and
                         re.search(r"\b(tiny|little|miniature|big.head)\b", text) and
                         re.search(r"\b(postal|mail|letter|envelope|courier)\b", text) else
                         "noir-style" if subject == "character-artist" and
                         re.search(r"\b(detective|fedora)\b", text) else
                         "minimalist-style" if subject == "blender-modeler" and
                         re.search(r"\bpendulum\b", text) else
                         "vector-style" if subject == "vegetation-artist" and
                         re.search(r"\b(sprout|flower)\b", text) else
                         "retro-8bit-style" if subject == "vehicle-artist" and
                         re.search(r"\bspaceship\b", text) and
                         re.search(r"\basteroid\b", text) else
                         "retro-16bit-style" if subject == "creature-artist" and
                         re.search(r"\bfox\b", text) and
                         re.search(r"\bwaterfall\b", text) else
                         "hd-2d-style" if subject == "character-artist" and
                         re.search(r"\b(traveler|wanderer)\b", text) and
                         re.search(r"\blantern\b", text) else
                         "frutiger-aero-style" if subject == "prop-artist" and
                         re.search(r"\bdashboard\b", text) and
                         re.search(r"\b(aqua|bubble|leaf|glossy)\b", text) else
                         "cosmic-eldritch-horror" if subject == "environment-artist" and
                         re.search(r"\baperture\b", text) and
                         re.search(r"\b(giant|impossible|void|unknowable)\b", text) else
                         "body-horror-style" if subject == "character-artist" and
                         re.search(r"\bhand\b", text) and
                         re.search(r"\b(extra|sixth|fused|metal|unfolds)\b", text) else
                         "analog-found-footage-horror" if subject == "environment-artist" and
                         re.search(r"\btraining\b", text) and
                         re.search(r"\b(camera|recording|tape|footage)\b", text) else
                         "liminal-space-style" if subject == "environment-artist" and
                         re.search(r"\bpool\b", text) and
                         re.search(r"\b(empty|endless|repeating|repeats|vacant)\b", text) else
                         "folk-horror-style" if subject == "environment-artist" and
                         re.search(r"\b(wicker|ritual|effigy)\b", text) and
                         re.search(r"\b(village|field|rural)\b", text) else
                         "mascot-puppet-horror" if subject == "character-artist" and
                         re.search(r"\b(puppet|mascot)\b", text) and
                         re.search(r"\b(felt|stage|show|plastic.eyes)\b", text) else
                         "dream-weirdcore-style" if subject == "environment-artist" and
                         re.search(r"\b(playground|nursery|playroom)\b", text) and
                         re.search(r"\b(block|alphabet|toy|chair|door)\b", text) else
                         "indie-horror-aesthetics" if subject == "environment-artist" and
                         re.search(r"\b(cabin)\b", text) and
                         re.search(r"\b(forest|trail|flashlight|window)\b", text) else
                         "stylized-style" if subject == "environment-artist" and
                         re.search(r"\b(castle|keep|drawbridge|moat)\b", text) else
                         "stylized-style" if subject == "environment-artist" and
                         re.search(r"\bcyberpunk\b|\bneon alley\b", text) else
                         "painterly-style" if subject in {"vehicle-artist", "environment-artist"}
                         and re.search(r"\briver\b", text) else
                         "pixel-art-style" if subject == "prop-artist" and
                         re.search(r"\bchest\b", text) else
                         "hand-painted-style" if subject == "prop-artist" and
                         re.search(r"\bteacup\b", text) else
                         "manga-style" if subject == "character-artist" and
                         re.search(r"\beye\b", text) and
                         re.search(r"\bgaze\b", text) else
                         "anime-style" if subject == "character-artist" and
                         re.search(r"\bheroine\b", text) else
                         "cartoon-style" if subject == "character-artist" and
                         re.search(r"\bbouncy\b", text) and
                         re.search(r"\bball\b", text) else
                         "stylized-style" if subject == "environment-artist" and
                         re.search(r"\bwindmill\b", text) else
                         "stylized-style" if subject in {"character-artist", "prop-artist"}
                         or (subject == "blender-modeler" and "lamp" in text) else
                         "realistic-style")
        chosen = next((name for pattern, name in style_rules if re.search(pattern, text)),
                      default_style)
        reason = "selected from subject and visual intent"
    # A rendered demo is reusable only for its declared subject, intent, and treatment.
    entry = next((item for item in entries if item["id"] == subject), None)
    style_entry = next((item for item in entries if item["id"] == chosen), None)
    world_entry = next((item for item in entries if item["id"] == selected_world), None)
    cue_matches = lambda item: any(re.search(rf"\b{re.escape(cue)}\b", text)
                                   for cue in item.get("intent_cues", []))
    # A matching world can select its own scene without pretending to be a style.
    if (world_entry and world_entry["status"] in {"Rendered", "Integrated"}
            and subject in world_entry.get("compatible_subjects", [])
            and chosen in world_entry.get("compatible_styles", [])
            and cue_matches(world_entry)):
        entry = world_entry
        matched = True
    elif (style_entry and style_entry["status"] in {"Rendered", "Integrated"}
            and subject in style_entry.get("compatible_subjects", []) and cue_matches(style_entry)):
        entry = style_entry
        matched = True
    else:
        matched = (entry and entry["status"] in {"Rendered", "Integrated"}
                   and chosen in entry.get("compatible_styles", []) and cue_matches(entry))
    return {"subject": subject, "style": chosen, "world": selected_world,
            "reason": reason,
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
