"""Behavioral checks for independently usable UI themes and character prompts."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


render = module("social_image_render", ROOT / "scripts/render.py")
characters = module("social_character_prompt", ROOT / "scripts/character_prompt.py")
CARD = json.loads((ROOT / "examples/request-flow.json").read_text(encoding="utf-8"))


class RenderTests(unittest.TestCase):
    def test_same_diagram_uses_every_theme(self):
        themes = json.loads(render.STYLES.read_text(encoding="utf-8"))["styles"]
        self.assertGreaterEqual(len(themes), 8)
        outputs = []
        for theme in themes:
            self.assertIn("treatment", theme)
            self.assertNotIn("layout", theme)
            svg = render.svg_card(CARD, render.style_for(theme["id"]), 1080, 1350, 81)
            parsed = ElementTree.fromstring(svg)
            self.assertEqual(parsed.attrib["width"], "1080")
            for label in ("Client", "API", "Store", "send", "write"):
                self.assertIn(label, svg)
            outputs.append(svg)
            folder = ROOT / "styles" / theme["id"]
            self.assertTrue((folder / "README.md").is_file())
            self.assertTrue((folder / "sample.png").is_file())
            self.assertTrue((folder / "sample.svg").is_file())
        self.assertEqual(len(outputs), len(set(outputs)))

    def test_diagram_and_chart_validate_meaning(self):
        broken = {**CARD, "edges": [{"from": "client", "to": "missing", "label": "calls"}]}
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
        self.assertGreaterEqual(len(catalog), 6)
        for style in catalog:
            prompt = characters.prompt_for(style["id"], brief)
            self.assertIn(brief, prompt)
            self.assertIn(style["prompt"], prompt)
            self.assertTrue((ROOT / "character-styles" / style["id"] / "sample.png").is_file())
            self.assertTrue((ROOT / "character-styles" / style["id"] / "README.md").is_file())
        with self.assertRaisesRegex(ValueError, "Unknown"):
            characters.prompt_for("no-such-style", brief)


if __name__ == "__main__":
    unittest.main()
