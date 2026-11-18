#!/usr/bin/env python3
"""Regenerate post-theme examples and the image skill's visual catalog."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from render import style_for, svg_card

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def tile_table(items):
    rows = []
    for offset in range(0, len(items), 3):
        cells = items[offset:offset+3]
        rows.append("| " + " | ".join(cells + [""] * (3-len(cells))) + " |")
    return "| Style | Style | Style |\n| --- | --- | --- |\n" + "\n".join(rows)


def contact_sheet(paths, output, columns, labels):
    if not paths:
        raise ValueError("Contact sheet needs images")
    if len(paths) != len(labels):
        raise ValueError("Every contact sheet image needs a label")
    with Image.open(paths[0]) as first:
        size = first.size
    rows = (len(paths) + columns - 1) // columns
    label_h = 42
    sheet = Image.new("RGB", (size[0]*columns, (size[1]+label_h)*rows), "#ffffff")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 23)
    except OSError:
        font = ImageFont.load_default()
    for index, path in enumerate(paths):
        with Image.open(path) as source:
            if source.size != size:
                raise ValueError(f"Sample size mismatch: {path}")
            x, y = (index % columns)*size[0], (index // columns)*(size[1]+label_h)
            sheet.paste(source.convert("RGB"), (x, y))
            box = draw.textbbox((0, 0), labels[index], font=font)
            draw.text((x+(size[0]-(box[2]-box[0]))/2, y+size[1]+7), labels[index],
                      fill="#17212b", font=font)
    # A photo-heavy contact sheet compresses well as JPEG; keep the editable post previews as PNG.
    if output.suffix == ".jpg":
        sheet.save(output, quality=88, subsampling=0, optimize=True)
    else:
        sheet.save(output, optimize=True)


def build():
    themes = read(ROOT / "catalog/styles.json")["styles"]
    characters = read(ROOT / "catalog/character-styles.json")["styles"]
    theme_tiles, theme_images = [], []
    for theme in themes:
        card_path = ROOT / "examples/post-themes" / f"{theme['id']}.json"
        card = read(card_path)
        if card.get("nodes") or card.get("edges"):
            raise ValueError(f"Theme example must be a post, not a diagram: {theme['id']}")
        folder = ROOT / "styles" / theme["id"]
        folder.mkdir(parents=True, exist_ok=True)
        svg = svg_card(card, style_for(theme["id"]), 1080, 1350, 81)
        (folder / "sample.svg").write_text(svg, encoding="utf-8")
        cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(folder / "sample.png"),
                         output_width=432, output_height=540)
        (folder / "README.md").write_text(
            f'# {theme["name"]}\n\n![{theme["name"]} post example](sample.png)\n\n'
            f'[Editable SVG](sample.svg) · [Example content](../../examples/post-themes/{theme["id"]}.json)\n\n'
            f'{theme["detail"]}\n\n'
            f'**Example post:** {card["title"]}. This is an illustrative concept, not evidence or an approved publication. '
            'Use this theme with other content and layouts as well.\n', encoding="utf-8")
        theme_tiles.append(f'[![{theme["name"]}](styles/{theme["id"]}/sample.png)]'
                           f'(styles/{theme["id"]}/README.md)<br>**{theme["name"]}** — {card["title"]}')
        theme_images.append(folder / "sample.png")
    contact_sheet(theme_images, ROOT / "post-theme-gallery.png", 5,
                  [theme["name"] for theme in themes])
    families = defaultdict(list)
    character_images = []
    for style in characters:
        folder = ROOT / "character-styles" / style["id"]
        sample = folder / "sample.png"
        if not sample.is_file():
            raise FileNotFoundError(f"Missing character example: {sample}")
        (folder / "README.md").write_text(
            f'# {style["name"]}\n\n![{style["name"]} character example](sample.png)\n\n'
            f'Family: **{style["family"]}**\n\n{style["prompt"]}\n\n'
            'The same [original character brief](../../examples/character-brief.txt) is used across this catalog. '
            'This generated image demonstrates a treatment; review identity, rights and final crop for any real post.\n',
            encoding="utf-8")
        families[style["family"]].append(f'[![{style["name"]}](character-styles/{style["id"]}/sample.png)]'
                                         f'(character-styles/{style["id"]}/README.md)<br>**{style["name"]}**')
        character_images.append(sample)
    # Existing legacy samples are square too; the sheet lets readers scan every style at once.
    contact_sheet(character_images, ROOT / "character-style-gallery.jpg", 5,
                  [style["name"] for style in characters])
    sections = []
    for family, tiles in families.items():
        sections.append(f'### {family}\n\n{tile_table(tiles)}')
    (ROOT / "README.md").write_text(
        '# Image themes and character styles\n\n'
        'A UI theme defines a post\'s visual language. Content decides the topic and layout. '
        'The ten examples below are deliberately different posts; none is a technical architecture diagram. '
        'Character art styles are a separate choice, and a genre or mood can be layered onto any of them.\n\n'
        '## UI post themes\n\n'
        'Each preview uses the maintained [SVG renderer](scripts/render.py) and links to its own README, '
        'editable source and example card. These are illustrative concepts that need content review before use.\n\n'
        '![Ten different posts in the ten UI themes](post-theme-gallery.png)\n\n'
        f'{tile_table(theme_tiles)}\n\n'
        '## Character styles\n\n'
        f'This is a broad maintained catalog of {len(characters)} rendering treatments, grouped by medium. '
        'It does not attempt to name every art style. All portraits use the same '
        '[original character brief](examples/character-brief.txt); each image links to an individual README.\n\n'
        '![Character style catalog](character-style-gallery.jpg)\n\n'
        + "\n\n".join(sections) + '\n\n'
        'Rebuild the README galleries with `python content-studio/skills/content-studio-image/scripts/build_gallery.py`. '
        'Create a new character prompt with [character_prompt.py](scripts/character_prompt.py). '
        'Use [render.py](scripts/render.py) to render your own reviewed post card with a chosen UI theme.\n',
        encoding="utf-8")
    return {"uiThemes": len(themes), "characterStyles": len(characters)}


if __name__ == "__main__":
    print(json.dumps(build()))
