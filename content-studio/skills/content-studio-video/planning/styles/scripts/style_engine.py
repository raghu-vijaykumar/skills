#!/usr/bin/env python3
"""Deterministic scene-aware style planner; no third-party dependencies."""
import argparse
import json
import shutil
from pathlib import Path

STYLES = {
    "math-visual": {"label": "Mathematical visualization", "keywords": ["math", "gradient", "equation", "vector", "algorithm", "neural", "geometry"], "techniques": ["animated-equations", "geometric-transform", "graph-animation"], "renderer": "manim"},
    "vector-science": {"label": "Illustrated science storytelling", "keywords": ["space", "biology", "planet", "science", "physics", "animal"], "techniques": ["layered-vector", "parallax", "shape-morph"], "renderer": "remotion"},
    "rapid-tech": {"label": "Rapid technical explainer", "keywords": ["code", "software", "api", "programming", "developer", "cloud"], "techniques": ["code-highlight", "kinetic-type", "rapid-cut"], "renderer": "remotion"},
    "editorial-map": {"label": "Editorial geography explainer", "keywords": ["map", "country", "geography", "history", "route", "border"], "techniques": ["route-trace", "map-camera", "data-overlay"], "renderer": "remotion"},
    "cinematic-3d": {"label": "Cinematic 3D reconstruction", "keywords": ["machine", "hardware", "engineering", "mechanism", "3d"], "techniques": ["cutaway", "orbit-camera", "dramatic-light"], "renderer": "blender"},
    "engineering-cutaway": {"label": "3D engineering cutaway explainer", "keywords": ["processor", "chip", "engine", "circuit", "electronics", "inside", "assembly", "architecture", "mechanical"], "techniques": ["layered-exploded-view", "transparent-shell", "component-isolation", "cross-section", "assembly-sequence", "camera-dolly"], "renderer": "blender"},
    "documentary": {"label": "Evidence-led documentary", "keywords": ["investigation", "documentary", "evidence", "archive", "interview"], "techniques": ["archival-composite", "timeline", "source-callout"], "renderer": "remotion"},
    "travel-scrapbook": {"label": "Travel scrapbook", "keywords": ["travel", "vlog", "trip", "beach", "hotel", "journey"], "techniques": ["postcard", "photo-parallax", "travel-route"], "renderer": "remotion"},
}
ALIASES = {"3blue1brown": "math-visual", "kurzgesagt": "vector-science", "fireship": "rapid-tech", "vox": "editorial-map", "lemmino": "cinematic-3d", "johnny-harris": "documentary", "branch-education": "engineering-cutaway", "brancheducation": "engineering-cutaway"}
EXECUTABLES = {"manim": "manim", "remotion": "node", "blender": "blender"}
# Node presence is only a prerequisite; Remotion package/project availability is not validated.

def resolve(name):
    name = ALIASES.get(name, name)
    if name not in STYLES:
        raise ValueError(f"Unknown style: {name}. Choose from {', '.join(STYLES)}")
    return name

def recommend(text, fallback="documentary"):
    words = set(__import__("re").findall(r"[a-z0-9]+", text.lower()))
    scores = {key: len(words.intersection(data["keywords"])) for key, data in STYLES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else fallback

def plan(data, selected="auto"):
    if not isinstance(data.get("scenes"), list) or not data["scenes"]:
        raise ValueError("scenes must be a nonempty array")
    output = {"schema_version": 1, "topic": data.get("topic", ""), "format": data.get("format", "video"), "scenes": [], "warnings": []}
    seen = set()
    for scene in data["scenes"]:
        if not isinstance(scene, dict) or not scene.get("id") or scene["id"] in seen:
            raise ValueError("Each scene needs a unique nonempty id")
        seen.add(scene["id"])
        duration = scene.get("duration_seconds")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
            raise ValueError(f"Invalid duration for scene {scene['id']}")
        text = " ".join(str(scene.get(k, "")) for k in ("narration", "visual_intent"))
        requested = scene.get("style", selected)
        style = recommend(text + " " + data.get("topic", "")) if requested == "auto" else resolve(requested)
        definition = STYLES[style]
        renderer = definition["renderer"]
        available = shutil.which(EXECUTABLES[renderer]) is not None
        output["scenes"].append({
            "id": scene["id"], "duration_seconds": duration, "style": style,
            "label": definition["label"], "techniques": definition["techniques"],
            "renderer": renderer, "renderer_detected": available,
            "status": "planned_not_rendered" if available else "needs_renderer",
            "evidence": scene.get("evidence", []), "visual_intent": scene.get("visual_intent", ""),
        })
        if not available:
            warning = f"{renderer} executable not detected; scene {scene['id']} cannot be rendered by this planner"
            output["warnings"].append(warning)
    output["review_required"] = True
    return output

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    p = sub.add_parser("plan")
    p.add_argument("input")
    p.add_argument("--style", default="auto")
    p.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "list":
        print(json.dumps({"styles": STYLES, "aliases": ALIASES}, indent=2))
    else:
        source = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = plan(source, args.style)
        dest = Path(args.output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {dest} ({len(result['scenes'])} scenes, {len(result['warnings'])} warnings)")

if __name__ == "__main__":
    main()
