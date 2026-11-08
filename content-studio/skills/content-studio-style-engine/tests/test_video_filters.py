import importlib.util
import unittest
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "video_filters.py"
spec = importlib.util.spec_from_file_location("video_filters", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class VideoFilterTests(unittest.TestCase):
    def test_preset_filter_expression(self):
        chain = mod.filters([{"start": 2, "end": 4, "preset": "warm-golden"}])
        self.assertIn("between(t\\\\,2.000000\\\\,4.000000)", chain)
        self.assertIn("saturation=1.16", chain)

    def test_reject_overlap(self):
        with self.assertRaises(ValueError):
            mod.validate_ranges([{"start": 0, "end": 5, "preset": "warm-golden"},
                                 {"start": 4, "end": 7, "preset": "mono-noir"}])

    def test_unknown_preset(self):
        with self.assertRaises(ValueError):
            mod.validate_ranges([{"start": 1, "end": 2, "preset": "not-real"}])

if __name__ == "__main__":
    unittest.main()
