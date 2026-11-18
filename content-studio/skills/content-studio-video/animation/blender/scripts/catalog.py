"""Validate the pinned Blender guidance and route requests without claiming render support."""

import argparse
import json
import re
from pathlib import Path

BLENDER = Path(__file__).resolve().parents[1]
CONTENT_STUDIO = BLENDER.parents[3]
REPO = CONTENT_STUDIO.parent
CATEGORIES = json.loads((BLENDER / "categories.json").read_text(encoding="utf-8"))
STYLE_CATEGORIES = {"Core styles", "Extended styles", "Horror packs"}
UPSTREAM = "https://github.com/arjun988/blender-skills/blob/904f095d8f36a6e72adaebb08d07f884a074743d/.claude/skills"


def catalog():
    """Validate the maintained names and link to immutable upstream guidance."""
    mapped = [name for names in CATEGORIES.values() for name in names]
    if len(mapped) != 94 or len(set(mapped)) != 94:
        raise ValueError("The category map must contain 94 unique skill IDs")
    entries = []
    for category, names in CATEGORIES.items():
        for name in names:
            entries.append({"id": name, "category": category,
                            "source": f"{UPSTREAM}/{name}/SKILL.md",
                            "status": "Catalogued"})
    return entries


def route(prompt, style=None):
    """Give an inspectable default; a catalogue route is never a render claim."""
    text = prompt.lower()
    subject_rules = [
        (r"\b(vehicle|car|truck|aircraft|spaceship)\b", "vehicle-artist"),
        (r"\b(creature|monster|dragon|animal)\b", "creature-artist"),
        (r"\b(character|person|human|mascot)\b", "character-artist"),
        (r"\b(tree|plant|vegetation|forest)\b", "vegetation-artist"),
        (r"\b(room|corridor|environment|landscape|building)\b", "environment-artist"),
        (r"\b(machine|mechanism|clamp|robot|industrial)\b", "hard-surface"),
        (r"\b(prop|object|product|furniture)\b", "prop-artist"),
    ]
    subject = next((name for pattern, name in subject_rules if re.search(pattern, text)), "blender-modeler")
    styles = {e["id"] for e in catalog() if e["category"] in STYLE_CATEGORIES}
    if style is not None:
        if style not in styles:
            raise ValueError(f"Unknown Blender style: {style}")
        chosen = style
        reason = "explicit style"
    else:
        style_rules = [
            (r"\b(horror|creepy|haunted|scary)\b", "horror-style"),
            (r"\b(anime|cel.shaded)\b", "anime-style"),
            (r"\b(cartoon|toon)\b", "cartoon-style"),
            (r"\b(pixel|sprite)\b", "pixel-art-style"),
            (r"\b(low.poly|lowpoly)\b", "lowpoly-style"),
        ]
        chosen = next((name for pattern, name in style_rules if re.search(pattern, text)),
                      "stylized-style" if subject == "character-artist" else "realistic-style")
        reason = "selected from subject and visual intent"
    return {"subject": subject, "style": chosen, "reason": reason,
            "status": "Catalogued", "render_method": None, "review_required": True}


def markdown_table(entries):
    lines = ["| Category | Skill | Status | Render evidence |",
             "| --- | --- | --- | --- |"]
    for entry in entries:
        lines.append(f"| {entry['category']} | [`{entry['id']}`]({entry['source']}) | Catalogued | Pending |")
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
    print(f"Updated {path} with {len(entries)} catalogued skills")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list")
    plan = sub.add_parser("plan")
    plan.add_argument("prompt")
    plan.add_argument("--style")
    sub.add_parser("readme-table")
    sub.add_parser("sync-readme")
    args = parser.parse_args()
    entries = catalog()
    if args.action == "list":
        print(json.dumps(entries, indent=2))
    elif args.action == "plan":
        print(json.dumps(route(args.prompt, args.style), indent=2))
    elif args.action == "readme-table":
        print(markdown_table(entries))
    else:
        sync_readme(entries)


if __name__ == "__main__":
    main()
