import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts" / "style_engine.py"
spec = importlib.util.spec_from_file_location("style_engine", path)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

class StyleEngineTests(unittest.TestCase):
    def test_alias(self):
        self.assertEqual(engine.resolve("3blue1brown"), "math-visual")

    def test_recommend(self):
        self.assertEqual(engine.recommend("gradient vector equation"), "math-visual")

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

if __name__ == "__main__":
    unittest.main()
