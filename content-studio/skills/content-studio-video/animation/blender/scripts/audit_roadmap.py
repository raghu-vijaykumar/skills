"""Audit every Blender catalog row and the scored GIFs shown in the README."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess

from catalog import BLENDER, VISUAL_CATEGORIES, catalog, markdown_table, scorebook


def decode_gif(path):
    """Read the complete animation with the same FFmpeg toolchain as video output."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required to decode showcase GIFs")
    result = subprocess.run([ffprobe, "-v", "error", "-count_frames",
                             "-select_streams", "v:0", "-show_entries",
                             "stream=nb_read_frames,width,height", "-of", "json", str(path)],
                            capture_output=True, text=True, check=True)
    stream = json.loads(result.stdout)["streams"][0]
    frames = int(stream["nb_read_frames"])
    if frames < 2 or stream["width"] < 1 or stream["height"] < 1:
        raise ValueError(f"Selected GIF has no motion: {path}")
    return {"frames": frames, "resolution": [stream["width"], stream["height"]]}


def audit():
    entries = catalog()
    winners = scorebook()
    book = json.loads((BLENDER / "scores.json").read_text(encoding="utf-8"))
    # Audit the page that actually presents the scored gallery and catalog.
    readme = (BLENDER / "README.md").read_text(encoding="utf-8")
    start, end = "<!-- blender-catalog:start -->", "<!-- blender-catalog:end -->"
    if readme.count(start) != 1 or readme.count(end) != 1:
        raise ValueError("README catalog markers are missing or duplicated")
    shown = readme.split(start, 1)[1].split(end, 1)[0].strip()
    if shown != markdown_table(entries):
        raise ValueError("README catalog differs from the 94-entry manifest")
    rows = []
    visual_gifs = set()
    decoded = {}
    for entry in entries:
        row = {key: entry.get(key) for key in ("id", "category", "status", "method",
                                               "planning_method", "review", "evidence")}
        if entry["status"] in {"Rendered", "Integrated"}:
            # The scorebook has already checked every candidate's rubric and winner.
            score_route = entry.get("score_route", entry["id"])
            winner = winners[score_route]
            row.update({"score_route": score_route, "selected_candidate": winner["id"],
                        "selected_score": winner["score_total"],
                        "candidate_count": len(book["routes"][score_route]["candidates"]),
                        "gif_sha256": winner["gif_sha256"]})
            gif = BLENDER / entry["evidence"]
            relative = entry["evidence"]
            if f"]({relative})" not in readme.split(start, 1)[0]:
                raise ValueError(f"Selected GIF is not inline above the catalog: {entry['id']}")
            if gif not in decoded:
                decoded[gif] = decode_gif(gif)
            row["gif_decode"] = decoded[gif]
            if entry["category"] in VISUAL_CATEGORIES:
                visual_gifs.add(entry["evidence"])
        elif entry["category"] == "Orchestration":
            row["planning_proof"] = entry["planning_proof"]
        elif entry["status"] == "Prototype":
            row["editor_import"] = "pending"
        rows.append(row)
    style_gifs = {row["evidence"] for row in rows
                  if row["category"] in {"Core styles", "Extended styles", "Horror packs"}}
    if len(style_gifs) != 31 or len(visual_gifs) != 55:
        raise ValueError("Visual route GIFs are missing or shared")
    statuses = {name: sum(row["status"] == name for row in rows)
                for name in ("Catalogued", "Prototype", "Rendered", "Integrated")}
    return {"schema_version": 1, "upstream_commit":
            "904f095d8f36a6e72adaebb08d07f884a074743d",
            "catalog_rows": len(rows), "statuses": statuses,
            "scored_routes": len(book["routes"]),
            "scored_candidate_records": sum(len(group["candidates"])
                                            for group in book["routes"].values()),
            "distinct_selected_gifs_decoded": len(decoded),
            "distinct_style_gifs": len(style_gifs),
            "distinct_visual_route_gifs": len(visual_gifs),
            "engine_editor_imports": "pending",
            "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Blender roadmap: {report['catalog_rows']} rows, "
          f"{report['scored_candidate_records']} scored candidates, "
          f"{report['distinct_selected_gifs_decoded']} decoded winning GIFs")


if __name__ == "__main__":
    main()
