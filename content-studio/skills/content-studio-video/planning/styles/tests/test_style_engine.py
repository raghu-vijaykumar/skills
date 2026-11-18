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

    def test_blender_overrides_require_compatible_editorial_style(self):
        with self.assertRaisesRegex(ValueError, "Blender overrides require"):
            engine.plan({"scenes": [{"id": "bad", "duration_seconds": 4,
                "style": "core-explainer", "blender_style": "cartoon-style"}]})

    def test_explicit_blender_executable_path(self):
        with patch.dict(os.environ, {"CONTENT_STUDIO_BLENDER_EXE": sys.executable}):
            self.assertEqual(engine.renderer_executable("blender"), sys.executable)

if __name__ == "__main__":
    unittest.main()
