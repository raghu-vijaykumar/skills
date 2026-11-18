import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "scripts" / "style_engine.py"
spec = importlib.util.spec_from_file_location("style_engine", path)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

class StyleEngineTests(unittest.TestCase):
    def test_alias(self):
        self.assertEqual(engine.resolve("3blue1brown"), "math-visual")

    def test_branch_education(self):
        self.assertEqual(engine.resolve("branch-education"), "engineering-cutaway")
        self.assertEqual(engine.recommend("processor chip circuit"), "engineering-cutaway")
        result = engine.plan({"scenes": [{"id": "cpu", "duration_seconds": 10, "style": "branch-education"}]})
        self.assertEqual(result["scenes"][0]["renderer"], "blender")
        self.assertIn("cross-section", result["scenes"][0]["techniques"])

    def test_recommend(self):
        self.assertEqual(engine.recommend("gradient vector equation"), "math-visual")
        self.assertEqual(engine.resolve("core-explainer"), "core-explainer")
        self.assertEqual(engine.recommend("why browser cache stays stale after deploy"), "core-explainer")

    def test_hybrid_scene_plan(self):
        result = engine.plan({"topic": "Education", "scenes": [
            {"id": "intro", "duration_seconds": 5, "style": "kurzgesagt"},
            {"id": "proof", "duration_seconds": 12, "style": "3blue1brown"},
        ]})
        self.assertEqual([s["style"] for s in result["scenes"]], ["vector-science", "math-visual"])
        self.assertTrue(result["review_required"])

    def test_duplicate_scene_rejected(self):
        with self.assertRaises(ValueError):
            engine.plan({"scenes": [{"id": "a", "duration_seconds": 2}, {"id": "a", "duration_seconds": 3}]})

    def test_invalid_duration_rejected(self):
        with self.assertRaises(ValueError):
            engine.plan({"scenes": [{"id": "a", "duration_seconds": -1}]})

    def test_blender_scene_selects_only_matching_rendered_demo(self):
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            result = engine.plan({"scenes": [{"id": "clamp", "duration_seconds": 4,
                "visual_intent": "Animate a realistic mechanical clamp"}]})
        scene = result["scenes"][0]
        self.assertEqual(scene["style"], "cinematic-3d")
        self.assertEqual(scene["blender"]["builder"], "examples/clamp.py")
        self.assertEqual(scene["status"], "planned_not_rendered")

    def test_blender_style_override_and_unsupported_combination(self):
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            result = engine.plan({"scenes": [{"id": "unsupported", "duration_seconds": 4,
                "style": "anime-style", "visual_intent": "Realistic clamp"}]})
        scene = result["scenes"][0]
        self.assertEqual(scene["blender"]["style"], "anime-style")
        self.assertIsNone(scene["blender"]["builder"])
        self.assertEqual(scene["status"], "needs_builder")
        self.assertTrue(result["warnings"])
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            forced = engine.plan({"scenes": [{"id": "courier", "duration_seconds": 4,
                "visual_intent": "A courier waves", "blender_style": "cartoon-style"}]})
        self.assertEqual(forced["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(forced["scenes"][0]["blender"]["builder"],
                         "examples/character.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            lowpoly = engine.plan({"scenes": [{"id": "lamp", "duration_seconds": 4,
                "visual_intent": "A desk lamp switches on", "blender_style": "lowpoly-style"}]})
        self.assertEqual(lowpoly["scenes"][0]["blender"]["builder"],
                         "examples/lowpoly_lamp.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            voxel = engine.plan({"scenes": [{"id": "voxel-lamp", "duration_seconds": 3,
                "visual_intent": "A desk lamp switches on", "blender_style": "voxel-style"}]})
        self.assertEqual(voxel["scenes"][0]["blender"]["builder"],
                         "examples/voxel_lamp.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            isometric = engine.plan({"scenes": [{"id": "iso-lamp", "duration_seconds": 3,
                "visual_intent": "A desk lamp switches on", "blender_style": "isometric-style"}]})
        self.assertEqual(isometric["scenes"][0]["blender"]["builder"],
                         "examples/isometric_lamp.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            realistic = engine.plan({"scenes": [{"id": "real-lamp", "duration_seconds": 3,
                "visual_intent": "A desk lamp adjusts", "blender_style": "realistic-style"}]})
        self.assertEqual(realistic["scenes"][0]["blender"]["builder"],
                         "examples/realistic_lamp.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            horror = engine.plan({"scenes": [{"id": "horror-hall", "duration_seconds": 3,
                "visual_intent": "A horror corridor reveals a door"}]})
        self.assertEqual(horror["scenes"][0]["blender"]["builder"],
                         "examples/horror_corridor.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            psx = engine.plan({"scenes": [{"id": "psx-hall", "duration_seconds": 3,
                "visual_intent": "A PSX horror hall reveals a CRT"}]})
        self.assertEqual(psx["scenes"][0]["blender"]["builder"],
                         "examples/psx_horror.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            anime = engine.plan({"scenes": [{"id": "anime-heroine", "duration_seconds": 3,
                "visual_intent": "An anime heroine blinks and raises an arm"}]})
        self.assertEqual(anime["scenes"][0]["blender"]["builder"],
                         "examples/anime_heroine.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            unnamed = engine.plan({"scenes": [{"id": "heroine", "duration_seconds": 3,
                "visual_intent": "A heroine blinks and raises an arm"}]})
        self.assertEqual(unnamed["scenes"][0]["blender"]["builder"],
                         "examples/anime_heroine.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            windmill = engine.plan({"scenes": [{"id": "windmill", "duration_seconds": 3,
                "visual_intent": "A windmill cottage turns on an island"}]})
        self.assertEqual(windmill["scenes"][0]["blender"]["builder"],
                         "examples/stylized_windmill.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            cartoon = engine.plan({"scenes": [{"id": "cartoon-mascot", "duration_seconds": 3,
                "visual_intent": "A bouncy ball mascot jumps and squashes"}]})
        self.assertEqual(cartoon["scenes"][0]["blender"]["builder"],
                         "examples/cartoon_bounce.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            comic = engine.plan({"scenes": [{"id": "comic-rocket", "duration_seconds": 3,
                "visual_intent": "A rocket whooshes through a panel"}]})
        self.assertEqual(comic["scenes"][0]["blender"]["builder"],
                         "examples/comic_rocket.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            manga = engine.plan({"scenes": [{"id": "manga-gaze", "duration_seconds": 3,
                "visual_intent": "An eye shifts its gaze across a panel"}]})
        self.assertEqual(manga["scenes"][0]["blender"]["builder"],
                         "examples/manga_gaze.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            pixel = engine.plan({"scenes": [{"id": "pixel-chest", "duration_seconds": 4,
                "visual_intent": "A treasure chest opens and emits sparks"}]})
        self.assertEqual(pixel["scenes"][0]["blender"]["builder"],
                         "examples/pixel_chest.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            painted = engine.plan({"scenes": [{"id": "painted-teacup", "duration_seconds": 3,
                "visual_intent": "A wildflower teacup turns and steams"}]})
        self.assertEqual(painted["scenes"][0]["blender"]["builder"],
                         "examples/painted_teacup.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            river = engine.plan({"scenes": [{"id": "watercolor-river", "duration_seconds": 3,
                "visual_intent": "A sailboat drifts across a river"}]})
        self.assertEqual(river["scenes"][0]["blender"]["builder"],
                         "examples/watercolor_river.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            paper = engine.plan({"scenes": [{"id": "paper-butterfly", "duration_seconds": 3,
                "visual_intent": "A butterfly flaps across a craft table"}]})
        self.assertEqual(paper["scenes"][0]["blender"]["builder"],
                         "examples/paper_butterfly.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            chibi = engine.plan({"scenes": [{"id": "chibi-postal", "duration_seconds": 3,
                "visual_intent": "A tiny postal courier hops and offers a letter"}]})
        self.assertEqual(chibi["scenes"][0]["blender"]["builder"],
                         "examples/chibi_courier.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            noir = engine.plan({"scenes": [{"id": "noir-walk", "duration_seconds": 3,
                "visual_intent": "A fedora detective walks through rainy light"}]})
        self.assertEqual(noir["scenes"][0]["blender"]["builder"],
                         "examples/noir_detective.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            minimal = engine.plan({"scenes": [{"id": "minimal-swing", "duration_seconds": 3,
                "visual_intent": "A pendulum sculpture swings through empty space"}]})
        self.assertEqual(minimal["scenes"][0]["blender"]["builder"],
                         "examples/minimal_pendulum.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            vector = engine.plan({"scenes": [{"id": "sprout", "duration_seconds": 3,
                "visual_intent": "A sprout grows into a flower"}]})
        self.assertEqual(vector["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(vector["scenes"][0]["blender"]["builder"],
                         "examples/vector_sprout.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            retro = engine.plan({"scenes": [{"id": "arcade", "duration_seconds": 4,
                "visual_intent": "A spaceship fires at an asteroid"}]})
        self.assertEqual(retro["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(retro["scenes"][0]["blender"]["builder"],
                         "examples/retro_8bit_ship.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            retro16 = engine.plan({"scenes": [{"id": "fox", "duration_seconds": 4,
                "visual_intent": "A fox walks beside a waterfall"}]})
        self.assertEqual(retro16["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(retro16["scenes"][0]["blender"]["builder"],
                         "examples/retro_16bit_fox.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            hd2d = engine.plan({"scenes": [{"id": "bridge", "duration_seconds": 3,
                "visual_intent": "A traveler carries a lantern across a bridge"}]})
        self.assertEqual(hd2d["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(hd2d["scenes"][0]["blender"]["builder"],
                         "examples/hd2d_bridge.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            aero = engine.plan({"scenes": [{"id": "aero", "duration_seconds": 3,
                "visual_intent": "A glossy aqua dashboard grows a leaf"}]})
        self.assertEqual(aero["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(aero["scenes"][0]["blender"]["builder"],
                         "examples/aero_dashboard.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            cosmic = engine.plan({"scenes": [{"id": "cosmic", "duration_seconds": 3,
                "visual_intent": "An impossible aperture looms over a tiny witness"}]})
        self.assertEqual(cosmic["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(cosmic["scenes"][0]["blender"]["builder"],
                         "examples/cosmic_aperture.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            hand = engine.plan({"scenes": [{"id": "hand", "duration_seconds": 3,
                "visual_intent": "A hand unfolds a fused metal sixth digit"}]})
        self.assertEqual(hand["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(hand["scenes"][0]["blender"]["builder"],
                         "examples/mutating_hand.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            analog = engine.plan({"scenes": [{"id": "training", "duration_seconds": 3,
                "visual_intent": "A training room security camera records an empty chair"}]})
        self.assertEqual(analog["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(analog["scenes"][0]["blender"]["builder"],
                         "examples/analog_training.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            liminal = engine.plan({"scenes": [{"id": "pool", "duration_seconds": 3,
                "visual_intent": "An empty tiled pool hall repeats endlessly"}]})
        self.assertEqual(liminal["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(liminal["scenes"][0]["blender"]["builder"],
                         "examples/liminal_pool.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            folk = engine.plan({"scenes": [{"id": "rite", "duration_seconds": 3,
                "visual_intent": "A sunlit village field surrounds a wicker effigy"}]})
        self.assertEqual(folk["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(folk["scenes"][0]["blender"]["builder"],
                         "examples/folk_ritual.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            puppet = engine.plan({"scenes": [{"id": "pip", "duration_seconds": 3,
                "visual_intent": "A cheerful felt puppet on a children's show stage turns wrong"}]})
        self.assertEqual(puppet["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(puppet["scenes"][0]["blender"]["builder"],
                         "examples/puppet_stage.py")

    def test_blender_overrides_require_compatible_editorial_style(self):
        with self.assertRaisesRegex(ValueError, "Blender overrides require"):
            engine.plan({"scenes": [{"id": "bad", "duration_seconds": 4,
                "style": "core-explainer", "blender_style": "cartoon-style"}]})

    def test_explicit_blender_executable_path(self):
        with patch.dict(os.environ, {"CONTENT_STUDIO_BLENDER_EXE": sys.executable}):
            self.assertEqual(engine.renderer_executable("blender"), sys.executable)

if __name__ == "__main__":
    unittest.main()
