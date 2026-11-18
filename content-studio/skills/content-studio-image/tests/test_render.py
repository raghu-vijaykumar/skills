"""Behavioral checks for independently usable UI themes and character prompts."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


render = module("social_image_render", ROOT / "scripts/render.py")
characters = module("social_character_prompt", ROOT / "scripts/character_prompt.py")
CARD = {"title": "A simple note", "body": "One clear idea"}


class RenderTests(unittest.TestCase):
    def test_distinct_post_examples_cover_every_theme(self):
        themes = json.loads(render.STYLES.read_text(encoding="utf-8"))["styles"]
        self.assertEqual(len(themes), 10)
        titles = set()
        structures = set()
        for theme in themes:
            self.assertIn("treatment", theme)
            self.assertNotIn("layout", theme)
            example = ROOT / "examples" / "post-themes" / f"{theme['id']}.json"
            card = json.loads(example.read_text(encoding="utf-8"))
            self.assertNotIn("nodes", card)
            self.assertNotIn("edges", card)
            self.assertNotIn(card["title"], titles)
            titles.add(card["title"])
            structures.add(next(key for key in ("body", "points", "steps", "comparison", "data") if key in card))
            svg = render.svg_card(card, render.style_for(theme["id"]), 1080, 1350, 81)
            parsed = ElementTree.fromstring(svg)
            self.assertEqual(parsed.attrib["width"], "1080")
            self.assertIn(card["title"], svg)
            folder = ROOT / "styles" / theme["id"]
            self.assertTrue((folder / "README.md").is_file())
            with Image.open(folder / "sample.png") as image:
                self.assertEqual(image.size, (432, 540))
            self.assertEqual((folder / "sample.svg").read_text(encoding="utf-8"), svg)
        self.assertTrue((ROOT / "post-theme-gallery.png").is_file())
        self.assertGreaterEqual(len(structures), 3)
        self.assertFalse((ROOT / "examples/request-flow.json").exists())

    def test_diagram_and_chart_validate_meaning(self):
        broken = {"title": "Abstract relationship",
                  "nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
                  "edges": [{"from": "a", "to": "missing", "label": "links"}]}
        with self.assertRaisesRegex(ValueError, "unknown"):
            render.validate_content(broken)
        with self.assertRaisesRegex(ValueError, "unit and sourceNote"):
            render.validate_content({"title": "Values", "data": [{"label": "A", "value": 2}]})

    def test_direct_render_has_exact_source_and_file_hashes(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            source = root / "card.json"
            source.write_text(json.dumps(CARD), encoding="utf-8")
            result = render.render(source, root / "out", "bento-box")
            self.assertEqual(result["inputSha256"], render.digest(source))
            for entry in result["files"]:
                self.assertEqual(entry["sha256"], render.digest(root / "out" / entry["path"]))
            self.assertTrue((root / "out/review.html").is_file())

    def test_unresolved_sources_and_rights_stop_render(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            source = root / "card.json"
            source.write_text(json.dumps({**CARD, "claims": [{"type": "fact", "text": "A number"}]}))
            with self.assertRaisesRegex(ValueError, "factual sources"):
                render.render(source, root / "out", "minimalism")
            source.write_text(json.dumps({**CARD, "assets": [{"path": "picture.png"}]}))
            with self.assertRaisesRegex(ValueError, "asset rights"):
                render.render(source, root / "out", "minimalism")

    def test_character_styles_share_identity_brief(self):
        catalog = json.loads(characters.CATALOG.read_text(encoding="utf-8"))["styles"]
        brief = (ROOT / "examples/character-brief.txt").read_text(encoding="utf-8").strip()
        self.assertEqual(len(catalog), 30)
        self.assertEqual(len({style["id"] for style in catalog}), len(catalog))
        for style in catalog:
            prompt = characters.prompt_for(style["id"], brief)
            self.assertIn(brief, prompt)
            self.assertIn(style["prompt"], prompt)
            self.assertTrue(style["family"])
            sample = ROOT / "character-styles" / style["id"] / "sample.png"
            self.assertTrue(sample.is_file())
            with Image.open(sample) as image:
                self.assertEqual(image.size, (512, 512))
            self.assertTrue((ROOT / "character-styles" / style["id"] / "README.md").is_file())
        self.assertTrue((ROOT / "character-style-gallery.jpg").is_file())
        with self.assertRaisesRegex(ValueError, "Unknown"):
            characters.prompt_for("no-such-style", brief)


if __name__ == "__main__":
    unittest.main()
