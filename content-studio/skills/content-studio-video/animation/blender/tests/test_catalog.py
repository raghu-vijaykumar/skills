"""Check the upstream pin and ensure guidance never masquerades as a renderer."""

import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "catalog.py"
SPEC = importlib.util.spec_from_file_location("blender_catalog", SCRIPT)
catalog_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog_module)


class CatalogTests(unittest.TestCase):
    def test_all_named_skills_have_one_category_and_immutable_source(self):
        entries = catalog_module.catalog()
        self.assertEqual(len(entries), 94)
        self.assertEqual(len({entry["id"] for entry in entries}), 94)
        for entry in entries:
            self.assertTrue(entry["source"].startswith(catalog_module.UPSTREAM + "/"))
            self.assertEqual(entry["status"], "Catalogued")

    def test_default_route_is_reviewable_and_does_not_claim_a_renderer(self):
        result = catalog_module.route("Animate a realistic mechanical clamp")
        self.assertEqual((result["subject"], result["style"]),
                         ("hard-surface", "realistic-style"))
        self.assertIsNone(result["render_method"])
        self.assertTrue(result["review_required"])

    def test_explicit_style_wins_and_unknown_style_fails(self):
        result = catalog_module.route("A character waves", "stop-motion-craft-style")
        self.assertEqual(result["style"], "stop-motion-craft-style")
        with self.assertRaisesRegex(ValueError, "Unknown Blender style"):
            catalog_module.route("A character waves", "unbuilt-style")

    def test_readme_catalog_and_rendered_gallery_stay_in_sync(self):
        readme = (catalog_module.REPO / "README.md").read_text(encoding="utf-8")
        generated = readme.split("<!-- blender-catalog:start -->", 1)[1].split(
            "<!-- blender-catalog:end -->", 1)[0].strip()
        self.assertEqual(generated, catalog_module.markdown_table(catalog_module.catalog()))
        for name in ("clamp", "character", "corridor"):
            path = catalog_module.BLENDER / "previews" / f"{name}.gif"
            self.assertTrue(path.is_file(), path)
            self.assertIn(f"animation/blender/previews/{name}.gif", readme)


if __name__ == "__main__":
    unittest.main()
