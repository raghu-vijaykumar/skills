import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import filters


class PresetRangeTest(unittest.TestCase):
    def test_preset_filter_expression(self):
        chain = filters.filter_chain([{"start": 2, "end": 4, "preset": "warm-golden"}])
        self.assertIn("between(t\\,2.000000\\,4.000000)", chain)
        self.assertIn("saturation=1.16", chain)

    def test_reject_overlap(self):
        with self.assertRaises(ValueError):
            filters.validate_ranges([{"start": 0, "end": 5, "preset": "warm-golden"},
                                     {"start": 4, "end": 7, "preset": "mono-noir"}])

    def test_unknown_preset(self):
        with self.assertRaises(ValueError):
            filters.validate_ranges([{"start": 1, "end": 2, "preset": "not-real"}])

    def test_catalog_is_available_for_choice(self):
        self.assertIn("clean-natural", filters.PRESETS)


class LookGraphTest(unittest.TestCase):
    def test_builds_fade_blend_for_preset(self):
        graph = filters.look_graph([{"start": 3, "end": 8, "preset": "warm-golden", "fade": 0.5}])
        self.assertIn("eq=contrast=1.06", graph)
        self.assertIn("blend=all_expr=", graph)
        self.assertTrue(graph.endswith("[vout]"))

    def test_zero_fade_uses_hard_enable(self):
        graph = filters.look_graph([{"start": 0, "end": 5, "preset": "mono-noir", "fade": 0}])
        self.assertIn("between(T,0.0,5.0)", graph)

    def test_fade_uses_two_argument_min(self):
        graph = filters.look_graph([{"start": 1, "end": 4, "preset": "cool-cinematic", "fade": 0.4}])
        self.assertIn("min(min(1,(T-1.0)/0.4),(4.0-T)/0.4)", graph)
        self.assertNotIn("min(1,(T-1.0)/0.4,(4.0-T)/0.4)", graph)

    def test_rejects_fade_longer_than_range(self):
        with self.assertRaises(ValueError):
            filters.look_graph([{"start": 0, "end": 1, "preset": "warm-golden", "fade": 2}])

    def test_requires_exactly_one_of_preset_or_lut(self):
        with self.assertRaises(ValueError):
            filters.validate_looks([{"start": 0, "end": 2, "preset": "warm-golden", "lut": "a.cube"}])
        with self.assertRaises(ValueError):
            filters.validate_looks([{"start": 0, "end": 2}])

    def test_resolves_existing_lut(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "look.cube").write_text("LUT_3D_SIZE 2\n", encoding="utf-8")
            graph = filters.look_graph(
                [{"start": 0, "end": 2, "lut": "look.cube", "fade": 0}], root=root
            )
            self.assertIn("lut3d=file=", graph)

    def test_rejects_missing_lut(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                filters.validate_looks(
                    [{"start": 0, "end": 2, "lut": "missing.cube"}], root=Path(folder)
                )


if __name__ == "__main__":
    unittest.main()
