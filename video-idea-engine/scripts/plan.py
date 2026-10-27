#!/usr/bin/env python3
"""Scaffold a draft with the idea-engine brief, filled from the channel dataset."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATES = SKILL / "templates"
CONTENT_HELPER = SKILL.parent / "content-helper" / "scripts"
sys.path.insert(0, str(CONTENT_HELPER))

from common import (DEFAULT_CONFIG, Log, channel_path, channel_root, channel_settings, load_config,  # noqa: E402
                    select_channels)


def fmt(value, suffix: str = "") -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.1f}{suffix}"
    return f"{value}{suffix}"


def context(root: Path, settings: dict) -> dict:
    path = channel_path(root, "analytics") / "insights.json"
    if not path.exists():
        raise SystemExit(f"missing {path}\nRun: python scripts/content.py insights --channel "
                         f"{settings['slug']} --vtr-count 12")
    data = json.loads(path.read_text(encoding="utf-8"))
    lanes = data.get("topic_lanes") or []
    bands = data.get("duration_bands") or []
    best_band = max(bands, key=lambda b: (b.get("views") or 0), default={})
    strongest = lanes[0] if lanes else {}
    return {
        "slug": settings["slug"],
        "name": settings["name"],
        "generated": data.get("generated", "unknown"),
        "numbers": data.get("numbers", {}),
        "lanes": lanes[:8],
        "bands": bands,
        "best_band": best_band,
        "strongest_lane": strongest,
    }


def render(template: str, values: dict) -> str:
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace(f"<{key}>", str(value))
    return text


def draft_id(root: Path, channel: str, title: str) -> str:
    """Allocate one safe per-video folder; preserve the channel's numeric sequence."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-") or "idea"
    if channel != "revise-labs":
        return slug
    numbers = []
    for folder in (root / "drafts").iterdir() if (root / "drafts").exists() else []:
        match = re.match(r"^(\d{5})-", folder.name)
        if match:
            numbers.append(int(match.group(1)))
    for bucket in ("shorts", "long"):
        for folder in (root / bucket).iterdir() if (root / bucket).exists() else []:
            provenance = folder / "source-provenance.json"
            if not provenance.is_file():
                continue
            source_id = json.loads(provenance.read_text(encoding="utf-8")).get("sourceId", "")
            match = re.match(r"^(\d{5})-", source_id)
            if match:
                numbers.append(int(match.group(1)))
    return f"{max(numbers, default=0) + 1:05d}-{slug}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--id", help="optional explicit safe video ID")
    parser.add_argument("--force", action="store_true", help="refresh an existing brief")
    parser.add_argument("--kind", choices=["short", "long"], default="short")
    parser.add_argument("--promise", default="")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()

    log = Log()
    cfg = load_config(Path(args.config))
    slug, raw = select_channels(cfg, args.channel)[0]
    settings = channel_settings(cfg, slug, raw)
    root = channel_root(cfg, slug)
    ctx = context(root, settings)

    folder_id = args.id or draft_id(root, slug, args.name)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", folder_id):
        raise SystemExit("video ID must contain only letters, digits, and hyphens")
    draft = root / "drafts" / folder_id
    if draft.exists() and (draft / "brief.md").exists() and not args.force:
        raise SystemExit(f"draft brief exists: {draft}; use --force to refresh")
    if not draft.exists():
        subprocess.run([sys.executable, str(CONTENT_HELPER / "content.py"), "draft", "new",
                        "--channel", slug, "--name", args.name, "--id", folder_id,
                        "--config", args.config], check=True)
    if not draft.exists():
        raise SystemExit(f"could not create {draft}")
    # Keep the brief in the same per-video folder that videogen will edit.

    numbers = ctx["numbers"]
    lane = ctx["strongest_lane"]
    band = ctx["best_band"]
    try:
        vtr_median = float(numbers.get("VTR median") or 0)
    except ValueError:
        vtr_median = 0.0
    common = {
        "idea": args.name,
        "channel": slug,
        "slug": slug,
        "kind": args.kind,
        "date": ctx["generated"],
        "band": band.get("band", "unknown"),
    }
    brief = render("brief.md", {
        **common,
        "promise": args.promise or "By the end, the viewer will be able to ...",
        "lane": lane.get("token", "?"),
        "views": fmt(lane.get("views")),
        "avg": fmt(lane.get("avg_pct"), "%"),
        "vtr": fmt(lane.get("vtr"), "%"),
        "n": lane.get("n", "?"),
    })
    research = render("research-sweep.md", {
        **common,
        "views_median": fmt(numbers.get("views median")),
        "pct_median": fmt(numbers.get("average % median")),
        "vtr_median": fmt(numbers.get("VTR median")),
        "subs_rate": fmt(numbers.get("subscribers per 1k views")),
        "band": band.get("band", "unknown"),
        "lane": lane.get("token", "?"),
        "weak_gate": "VTR (entry)" if vtr_median and vtr_median < 50 else "retention",
    })
    packaging = render("packaging.md", common)
    measurement = render("postmortem.md", common)

    (draft / "brief.md").write_text(brief, encoding="utf-8")
    (draft / "research.md").write_text(research, encoding="utf-8")
    (draft / "packaging.md").write_text(packaging, encoding="utf-8")
    (draft / "measurement.md").write_text(measurement, encoding="utf-8")

    if (root / "videogen.config.ts").is_file() and not (draft / "video.tsx").exists():
        binary = root / "node_modules" / ".bin" / ("videogen.cmd" if sys.platform == "win32" else "videogen")
        if not binary.exists():
            raise SystemExit(f"install the pinned videogen package in {root}, then run videogen scaffold {folder_id}")
        subprocess.run([str(binary), "scaffold", folder_id, "--title", args.name],
                       cwd=root, check=True)
    log(f"scaffolded {draft}")
    log(f"prior: median {numbers.get('views median')} views, "
        f"{numbers.get('average % median')}% avg, {numbers.get('VTR median')}% VTR; "
        f"best band {band.get('band', '?')}; strongest lane {lane.get('token', '?')}")
    log("next: fill research.md and packaging.md before writing any code or narration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
