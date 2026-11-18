"""Keep the full roadmap honest about which examples have rendered evidence."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "catalog.py"
SPEC = importlib.util.spec_from_file_location("blender_catalog", SCRIPT)
catalog_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog_module)


class CatalogTests(unittest.TestCase):
    def test_all_named_skills_have_one_category_dependencies_and_immutable_source(self):
        entries = catalog_module.catalog()
        self.assertEqual(len(entries), 94)
        self.assertEqual(len({entry["id"] for entry in entries}), 94)
        self.assertEqual(sum(entry["status"] == "Rendered" for entry in entries), 24)
        for entry in entries:
            self.assertTrue(entry["source"].startswith(catalog_module.UPSTREAM + "/"))
            self.assertEqual(entry["route"], "content-studio-video-animation")
            self.assertTrue(all(name in {item["id"] for item in entries}
                                for name in entry["dependencies"]))

    def test_known_demo_route_is_reviewable_and_generic_object_stays_catalogued(self):
        result = catalog_module.route("Animate a realistic mechanical clamp")
        self.assertEqual((result["subject"], result["style"]),
                         ("hard-surface", "realistic-style"))
        self.assertEqual(result["render_method"], "blender-shot")
        self.assertEqual(result["builder"], "examples/clamp.py")
        self.assertTrue(result["review_required"])
        generic = catalog_module.route("Animate an industrial machine")
        self.assertIsNone(generic["render_method"])
        self.assertEqual(generic["status"], "Catalogued")
        self.assertEqual(catalog_module.route("A cel-shaded courier waves")["builder"],
                         "examples/character.py")
        self.assertEqual(catalog_module.route("An atmospheric corridor push")["builder"],
                         "examples/corridor.py")
        self.assertEqual(catalog_module.route("An adjustable desk lamp lights a notebook")["builder"],
                         "examples/lamp.py")
        self.assertEqual(catalog_module.route("Model a desk lamp", subject="blender-modeler")["builder"],
                         "examples/lamp.py")
        lowpoly = catalog_module.route("Animate a low-poly desk lamp switching on")
        self.assertEqual((lowpoly["subject"], lowpoly["style"]),
                         ("prop-artist", "lowpoly-style"))
        self.assertEqual(lowpoly["builder"], "examples/lowpoly_lamp.py")
        self.assertIsNone(catalog_module.route("Animate a low-poly car")["builder"])
        voxel = catalog_module.route("Animate a voxel desk lamp switching on")
        self.assertEqual((voxel["subject"], voxel["style"]),
                         ("prop-artist", "voxel-style"))
        self.assertEqual(voxel["builder"], "examples/voxel_lamp.py")
        self.assertIsNone(catalog_module.route("Animate a voxel car")["builder"])
        isometric = catalog_module.route("Animate an isometric desk lamp switching on")
        self.assertEqual((isometric["subject"], isometric["style"]),
                         ("prop-artist", "isometric-style"))
        self.assertEqual(isometric["builder"], "examples/isometric_lamp.py")
        self.assertIsNone(catalog_module.route("Animate an isometric city")["builder"])
        realistic = catalog_module.route("Animate a realistic desk lamp")
        self.assertEqual((realistic["subject"], realistic["style"]),
                         ("prop-artist", "realistic-style"))
        self.assertEqual(realistic["builder"], "examples/realistic_lamp.py")
        self.assertIsNone(catalog_module.route("Animate a realistic car")["builder"])
        horror = catalog_module.route("A psychological horror corridor with a door reveal")
        self.assertEqual((horror["subject"], horror["style"]),
                         ("environment-artist", "horror-style"))
        self.assertEqual(horror["builder"], "examples/horror_corridor.py")
        self.assertIsNone(catalog_module.route("A horror desk lamp")["builder"])
        psx = catalog_module.route("A PSX horror hall with one CRT")
        self.assertEqual((psx["subject"], psx["style"]),
                         ("environment-artist", "psx-horror-style"))
        self.assertEqual(psx["builder"], "examples/psx_horror.py")
        self.assertIsNone(catalog_module.route("A PSX horror creature")["builder"])
        anime = catalog_module.route("An anime heroine blinks and raises her arm")
        self.assertEqual((anime["subject"], anime["style"]),
                         ("character-artist", "anime-style"))
        self.assertEqual(anime["builder"], "examples/anime_heroine.py")
        unnamed = catalog_module.route("A heroine blinks and raises her arm")
        self.assertEqual(unnamed["style"], "anime-style")
        self.assertEqual(unnamed["builder"], "examples/anime_heroine.py")
        self.assertIsNone(catalog_module.route("An anime creature waves")["builder"])
        stylized = catalog_module.route("A windmill cottage turns on an island")
        self.assertEqual((stylized["subject"], stylized["style"]),
                         ("environment-artist", "stylized-style"))
        self.assertEqual(stylized["builder"], "examples/stylized_windmill.py")
        self.assertIsNone(catalog_module.route("A stylized cityscape")["builder"])
        cartoon = catalog_module.route("A bouncy ball mascot jumps and squashes")
        self.assertEqual((cartoon["subject"], cartoon["style"]),
                         ("character-artist", "cartoon-style"))
        self.assertEqual(cartoon["builder"], "examples/cartoon_bounce.py")
        self.assertIsNone(catalog_module.route("A cartoon dragon jumps")["builder"])
        comic = catalog_module.route("A rocket whooshes through a panel")
        self.assertEqual((comic["subject"], comic["style"]),
                         ("vehicle-artist", "comic-book-style"))
        self.assertEqual(comic["builder"], "examples/comic_rocket.py")
        self.assertIsNone(catalog_module.route("A comic car accelerates")["builder"])
        manga = catalog_module.route("An eye shifts its gaze across a panel")
        self.assertEqual((manga["subject"], manga["style"]),
                         ("character-artist", "manga-style"))
        self.assertEqual(manga["builder"], "examples/manga_gaze.py")
        self.assertIsNone(catalog_module.route("A manga creature growls")["builder"])
        pixel = catalog_module.route("A treasure chest opens and emits sparks")
        self.assertEqual((pixel["subject"], pixel["style"]),
                         ("prop-artist", "pixel-art-style"))
        self.assertEqual(pixel["builder"], "examples/pixel_chest.py")
        self.assertIsNone(catalog_module.route("A pixel-art bottle spins")["builder"])
        painted = catalog_module.route("A wildflower teacup turns and steams")
        self.assertEqual((painted["subject"], painted["style"]),
                         ("prop-artist", "hand-painted-style"))
        self.assertEqual(painted["builder"], "examples/painted_teacup.py")
        self.assertIsNone(catalog_module.route("A hand-painted car drives")["builder"])
        river = catalog_module.route("A sailboat drifts across a river")
        self.assertEqual((river["subject"], river["style"]),
                         ("vehicle-artist", "painterly-style"))
        self.assertEqual(river["builder"], "examples/watercolor_river.py")
        self.assertIsNone(catalog_module.route("A watercolor airplane flies")["builder"])
        paper = catalog_module.route("A butterfly flaps across a craft table")
        self.assertEqual((paper["subject"], paper["style"]),
                         ("creature-artist", "stop-motion-craft-style"))
        self.assertEqual(paper["builder"], "examples/paper_butterfly.py")
        self.assertIsNone(catalog_module.route("A stop-motion clay dragon walks")["builder"])
        chibi = catalog_module.route("A tiny postal courier hops and offers a letter")
        self.assertEqual((chibi["subject"], chibi["style"]),
                         ("character-artist", "chibi-style"))
        self.assertEqual(chibi["builder"], "examples/chibi_courier.py")
        self.assertIsNone(catalog_module.route("A chibi dragon carries mail")["builder"])
        noir = catalog_module.route("A fedora detective walks through rainy light")
        self.assertEqual((noir["subject"], noir["style"]),
                         ("character-artist", "noir-style"))
        self.assertEqual(noir["builder"], "examples/noir_detective.py")
        self.assertIsNone(catalog_module.route("A noir bicycle turns")["builder"])
        minimal = catalog_module.route("A pendulum sculpture swings through empty space")
        self.assertEqual((minimal["subject"], minimal["style"]),
                         ("blender-modeler", "minimalist-style"))
        self.assertEqual(minimal["builder"], "examples/minimal_pendulum.py")
        self.assertIsNone(catalog_module.route("A minimalist car drives")["builder"])
        vector = catalog_module.route("A sprout grows into a flower")
        self.assertEqual(vector["subject"], "vegetation-artist")
        self.assertEqual(vector["style"], "vector-style")
        self.assertEqual(vector["builder"], "examples/vector_sprout.py")
        self.assertIsNone(catalog_module.route("A vector forest grows")["builder"])

    def test_explicit_style_wins_and_unsupported_combination_has_no_builder(self):
        result = catalog_module.route("A character waves", "stop-motion-craft-style")
        self.assertEqual(result["style"], "stop-motion-craft-style")
        self.assertIsNone(result["render_method"])
        overridden = catalog_module.route("A realistic mechanical clamp", "anime-style")
        self.assertEqual(overridden["style"], "anime-style")
        self.assertIsNone(overridden["render_method"])
        with self.assertRaisesRegex(ValueError, "Unknown Blender style"):
            catalog_module.route("A character waves", "unbuilt-style")

    def test_false_rendered_claim_and_broken_dependency_are_rejected(self):
        original = catalog_module.MANIFEST
        try:
            candidate = copy.deepcopy(original)
            candidate["entries"][0]["status"] = "Rendered"
            catalog_module.MANIFEST = candidate
            with self.assertRaisesRegex(ValueError, "lacks a supported method"):
                catalog_module.catalog()
            candidate["entries"][0]["status"] = "Catalogued"
            candidate["entries"][0]["dependencies"] = ["missing-skill"]
            with self.assertRaisesRegex(ValueError, "Invalid dependencies"):
                catalog_module.catalog()
            candidate["entries"][0]["dependencies"] = ["blender-modeler"]
            candidate["entries"][1]["dependencies"] = ["blender-director"]
            with self.assertRaisesRegex(ValueError, "Dependency cycle"):
                catalog_module.catalog()
        finally:
            catalog_module.MANIFEST = original

    def test_explicit_subject_uses_catalog_id(self):
        result = catalog_module.route("A realistic clamp", subject="hard-surface")
        self.assertEqual(result["subject"], "hard-surface")
        with self.assertRaisesRegex(ValueError, "Unknown Blender subject"):
            catalog_module.route("A clamp", subject="unlisted-subject")

    def test_gallery_requires_scores_for_every_candidate_and_selects_best(self):
        book = json.loads((catalog_module.BLENDER / "scores.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog_module.scorebook(book)), 25)
        handoff = book["routes"]["video-handoff"]
        self.assertEqual(len(handoff["candidates"]), 2)
        self.assertEqual(handoff["selected"], "clamp-handoff-full-resolution")
        pixel = book["routes"]["pixel-art-style"]
        self.assertEqual(len(pixel["candidates"]), 3)
        self.assertEqual(pixel["selected"], "pixel-chest-v2-coarse")
        self.assertEqual([candidate["technical_pass"] for candidate in pixel["candidates"]],
                         [False, False, True])
        painted = book["routes"]["hand-painted-style"]
        self.assertEqual(len(painted["candidates"]), 2)
        self.assertEqual(painted["selected"], "painted-teacup-v2")
        self.assertEqual([candidate["score_total"] for candidate in painted["candidates"]],
                         [78, 82])
        watercolor = book["routes"]["painterly-style"]
        self.assertEqual(len(watercolor["candidates"]), 3)
        self.assertEqual(watercolor["selected"], "watercolor-river-v3")
        self.assertEqual([candidate["score_total"] for candidate in watercolor["candidates"]],
                         [74, 78, 82])
        paper = book["routes"]["stop-motion-craft-style"]
        self.assertEqual(len(paper["candidates"]), 2)
        self.assertEqual(paper["selected"], "paper-butterfly-v2")
        self.assertEqual([candidate["score_total"] for candidate in paper["candidates"]],
                         [74, 82])
        chibi = book["routes"]["chibi-style"]
        self.assertEqual(len(chibi["candidates"]), 2)
        self.assertEqual(chibi["selected"], "chibi-courier-v2")
        self.assertEqual([candidate["score_total"] for candidate in chibi["candidates"]],
                         [70, 78])
        noir = book["routes"]["noir-style"]
        self.assertEqual(len(noir["candidates"]), 2)
        self.assertEqual(noir["selected"], "noir-detective-v2")
        self.assertEqual([candidate["score_total"] for candidate in noir["candidates"]],
                         [69, 77])
        minimal = book["routes"]["minimalist-style"]
        self.assertEqual(len(minimal["candidates"]), 2)
        self.assertEqual(minimal["selected"], "minimal-pendulum-v2")
        self.assertEqual([candidate["score_total"] for candidate in minimal["candidates"]],
                         [74, 82])
        vector = book["routes"]["vector-style"]
        self.assertEqual(vector["selected"], "vector-sprout-v3")
        self.assertEqual([candidate["score_total"] for candidate in vector["candidates"]],
                         [74, 78, 82])
        unscored = copy.deepcopy(book)
        unscored["routes"]["hard-surface"]["candidates"][0]["scores"].pop("finish")
        with self.assertRaisesRegex(ValueError, "five 0–5 scores"):
            catalog_module.scorebook(unscored)
        worse_winner = copy.deepcopy(book)
        competitor = copy.deepcopy(worse_winner["routes"]["hard-surface"]["candidates"][0])
        competitor["id"] = "clamp-better"
        competitor["scores"] = {name: 5 for name in catalog_module.SCORE_FIELDS}
        competitor["score_total"] = 100
        worse_winner["routes"]["hard-surface"]["candidates"].append(competitor)
        with self.assertRaisesRegex(ValueError, "not the best passing result"):
            catalog_module.scorebook(worse_winner)

    def test_readme_catalog_and_rendered_gallery_stay_in_sync(self):
        readme = (catalog_module.REPO / "README.md").read_text(encoding="utf-8")
        generated = readme.split("<!-- blender-catalog:start -->", 1)[1].split(
            "<!-- blender-catalog:end -->", 1)[0].strip()
        self.assertEqual(generated, catalog_module.markdown_table(catalog_module.catalog()))
        for name in ("clamp", "character", "corridor", "lamp", "handoff",
                     "lowpoly-lamp", "voxel-lamp", "isometric-lamp", "realistic-lamp",
                     "horror-corridor", "psx-horror", "anime-heroine", "stylized-windmill",
                     "cartoon-bounce", "comic-rocket", "manga-gaze", "pixel-chest",
                     "painted-teacup", "watercolor-river", "paper-butterfly",
                     "chibi-courier", "noir-detective", "minimal-pendulum",
                     "vector-sprout"):
            path = catalog_module.BLENDER / "previews" / f"{name}.gif"
            self.assertTrue(path.is_file(), path)
            self.assertIn(f"animation/blender/previews/{name}.gif", readme)
        self.assertIn("![Best scored vector sprout animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/vector-sprout.gif)", readme)

    def test_visual_style_gifs_must_be_distinct(self):
        original = catalog_module.MANIFEST
        candidate = copy.deepcopy(original)
        anime = next(entry for entry in candidate["entries"] if entry["id"] == "anime-style")
        anime.update({"status": "Rendered", "method": "blender-shot",
                      "evidence": "previews/lowpoly-lamp.gif", "review": "lowpoly-review.md",
                      "builder": "examples/lowpoly_lamp.py", "spec": "examples/lowpoly_lamp.json",
                      "score_record": "scores.json"})
        winners = catalog_module.scorebook()
        winners["anime-style"] = winners["lowpoly-style"]
        try:
            catalog_module.MANIFEST = candidate
            with patch.object(catalog_module, "scorebook", return_value=winners):
                with self.assertRaisesRegex(ValueError, "distinct GIFs"):
                    catalog_module.catalog()
        finally:
            catalog_module.MANIFEST = original


if __name__ == "__main__":
    unittest.main()
