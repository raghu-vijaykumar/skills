#!/usr/bin/env python3
"""Build the one-example UI theme comparison and character gallery README files."""
from __future__ import annotations

import json
from pathlib import Path

import cairosvg
from PIL import Image

from render import style_for, svg_card

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "examples/request-flow.json").read_text(encoding="utf-8"))


def table(tiles):
    rows = []
    for offset in range(0, len(tiles), 3):
        cells = tiles[offset:offset + 3]
        rows.append("| " + " | ".join(cells + [""] * (3 - len(cells))) + " |")
    return "\n".join(rows)


def build():
    themes = json.loads((ROOT / "catalog/styles.json").read_text(encoding="utf-8"))["styles"]
    characters = json.loads((ROOT / "catalog/character-styles.json").read_text(encoding="utf-8"))["styles"]
    theme_tiles = []
    thumbnails = []
    for theme in themes:
        folder = ROOT / "styles" / theme["id"]
        folder.mkdir(parents=True, exist_ok=True)
        svg = svg_card(CARD, style_for(theme["id"]), 1080, 1350, 81)
        (folder / "sample.svg").write_text(svg, encoding="utf-8")
        cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(folder / "sample.png"),
                         output_width=432, output_height=540)
        (folder / "README.md").write_text(
            f'# {theme["name"]}\n\n![{theme["name"]} request-flow sample](sample.png)\n\n'
            f'[Editable SVG](sample.svg) · Theme ID: `{theme["id"]}`\n\n'
            f'{theme["detail"]}\n\n'
            'The content, labels, diagram positions and framing match every other UI theme sample. '
            'The diagram is conceptual and is not evidence of a real system.\n', encoding="utf-8")
        theme_tiles.append(f'[![{theme["name"]}](styles/{theme["id"]}/sample.png)]'
                           f'(styles/{theme["id"]}/README.md)<br>**{theme["name"]}**')
        thumbnails.append(folder / "sample.png")
    # A single comparison image makes the visual differences inspectable at a glance.
    sheet = Image.new("RGB", (432*5, 540*2), "#ffffff")
    for index, path in enumerate(thumbnails):
        with Image.open(path) as thumbnail:
            sheet.paste(thumbnail.convert("RGB"), ((index % 5)*432, (index // 5)*540))
    sheet.save(ROOT / "themes-comparison.png", optimize=True)
    character_tiles = []
    for character in characters:
        folder = ROOT / "character-styles" / character["id"]
        sample = folder / "sample.png"
        if not sample.is_file():
            raise FileNotFoundError(f"Character sample missing: {sample}")
        (folder / "README.md").write_text(
            f'# {character["name"]}\n\n![{character["name"]} character sample](sample.png)\n\n'
            f'Character style ID: `{character["id"]}`\n\n{character["prompt"]}\n\n'
            'This is an AI-generated sample of an original character. The same character brief '
            'and framing were used for every character style. For production, review the generated '
            'character, intended identity, rights and final crop.\n', encoding="utf-8")
        character_tiles.append(f'[![{character["name"]}](character-styles/{character["id"]}/sample.png)]'
                               f'(character-styles/{character["id"]}/README.md)<br>**{character["name"]}**')
    (ROOT / "README.md").write_text(
        '# Image themes and character styles\n\n'
        'Choose a UI theme for diagrams, information cards or other structured content. '
        'Choose a character style when generating an illustrated person. '
        'These are separate decisions from content layout, topic and platform size.\n\n'
        '## UI themes: one diagram, ten treatments\n\n'
        'Every sample below renders the exact same [request-flow content](examples/request-flow.json). '
        'Only its UI theme changes. Click an image to open its individual README and editable SVG.\n\n'
        '![Ten UI themes on the same diagram](themes-comparison.png)\n\n'
        '| Theme | Theme | Theme |\n| --- | --- | --- |\n' + table(theme_tiles) + '\n\n'
        '## Character image styles: one person, six treatments\n\n'
        'Each sample uses the same [character brief](examples/character-brief.txt). '
        'Click an image for the individual style README.\n\n'
        '| Style | Style | Style |\n| --- | --- | --- |\n' + table(character_tiles) + '\n\n'
        'Render the common diagram with `python content-studio/skills/content-studio-image/scripts/render.py '
        'render --input content-studio/skills/content-studio-image/examples/request-flow.json '
        '--style bento-box --output tmp/image-bento`. '
        'Rebuild the gallery with `python content-studio/skills/content-studio-image/scripts/build_gallery.py`.\n',
        encoding="utf-8")
    return {"themes": len(themes), "characterStyles": len(characters)}


if __name__ == "__main__":
    print(json.dumps(build()))
