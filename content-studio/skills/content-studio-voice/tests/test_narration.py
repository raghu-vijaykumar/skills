"""Unit tests for narration validation, reuse, and timeline fitting."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import narration


class ValidateScriptTest(unittest.TestCase):
    def test_normalizes_valid_segments(self):
        segments = narration.validate_script(
            {
                "segments": [
                    {"id": "v01", "start": 0, "end": 14, "text": " hello "},
                    {"id": "v02", "start": 14.5, "end": 30, "text": "world"},
                ]
            }
        )
        self.assertEqual(segments[0], {"id": "v01", "start": 0.0, "end": 14.0, "text": "hello"})
        self.assertEqual(segments[1]["start"], 14.5)

    def test_rejects_missing_segments(self):
        with self.assertRaises(ValueError):
            narration.validate_script({})

    def test_rejects_duplicate_ids(self):
        with self.assertRaises(ValueError):
            narration.validate_script(
                {
                    "segments": [
                        {"id": "a", "start": 0, "end": 1, "text": "x"},
                        {"id": "a", "start": 2, "end": 3, "text": "y"},
                    ]
                }
            )

    def test_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            narration.validate_script(
                {"segments": [{"id": "a", "start": 0, "end": 1, "text": "  "}]}
            )

    def test_rejects_reversed_time(self):
        with self.assertRaises(ValueError):
            narration.validate_script(
                {"segments": [{"id": "a", "start": 5, "end": 5, "text": "x"}]}
            )

    def test_rejects_unordered_segments(self):
        with self.assertRaises(ValueError):
            narration.validate_script(
                {
                    "segments": [
                        {"id": "a", "start": 10, "end": 12, "text": "x"},
                        {"id": "b", "start": 1, "end": 2, "text": "y"},
                    ]
                }
            )


class ReuseTest(unittest.TestCase):
    def test_reuses_only_matching_text_and_params(self):
        with tempfile.TemporaryDirectory() as folder:
            audio = Path(folder) / "a.wav"
            audio.write_bytes(b"audio")
            text = "hello"
            params = {"nfe_step": 32}
            entry = {"text_hash": narration.sha256_text(text), "params": params}
            self.assertTrue(narration.is_reusable(entry, text, params, audio))
            self.assertFalse(narration.is_reusable(entry, "changed", params, audio))
            self.assertFalse(narration.is_reusable(entry, text, {"nfe_step": 16}, audio))
            audio.unlink()
            self.assertFalse(narration.is_reusable(entry, text, params, audio))

    def test_hashes_are_stable_and_distinct(self):
        self.assertEqual(narration.sha256_text("hello"), narration.sha256_text("hello"))
        self.assertNotEqual(narration.sha256_text("hello"), narration.sha256_text("world"))


class FitTimelineTest(unittest.TestCase):
    def segments(self):
        return [
            {"id": "a", "start": 0.0, "end": 20.0},
            {"id": "b", "start": 20.0, "end": 40.0},
        ]

    def test_keeps_natural_pace_when_it_fits(self):
        placed = narration.fit_timeline(
            self.segments(), {"a": 10.0, "b": 10.0}, 40.0
        )
        self.assertEqual(placed[0]["tempo"], 1.0)
        self.assertEqual(placed[0]["start"], 0.0)
        self.assertEqual(placed[0]["end"], 10.0)
        self.assertEqual(placed[1]["start"], 20.0)
        self.assertEqual(placed[1]["end"], 30.0)
        self.assertFalse(placed[0]["needs_review"])

    def test_caps_tempo_and_reports_overrun(self):
        placed = narration.fit_timeline(
            self.segments(), {"a": 30.0, "b": 10.0}, 40.0, max_tempo=1.12
        )
        self.assertEqual(placed[0]["tempo"], 1.12)
        self.assertGreater(placed[0]["overrun_seconds"], 0)
        self.assertTrue(placed[0]["needs_review"])
        self.assertGreater(placed[1]["start"], 20.0)

    def test_spills_into_following_slack(self):
        placed = narration.fit_timeline(
            self.segments(), {"a": 25.0, "b": 5.0}, 40.0
        )
        self.assertEqual(placed[0]["tempo"], 1.12)
        self.assertGreater(placed[0]["end"], 20.0)
        self.assertEqual(placed[1]["start"], round(placed[0]["end"] + 0.3, 3))

    def test_rejects_invalid_tempo(self):
        with self.assertRaises(ValueError):
            narration.fit_timeline(self.segments(), {"a": 1.0, "b": 1.0}, 40.0, max_tempo=0.9)

    def test_summary_counts_review_sections(self):
        placed = narration.fit_timeline(
            self.segments(), {"a": 30.0, "b": 10.0}, 40.0
        )
        summary = narration.timeline_summary(placed, 40.0)
        self.assertEqual(len(summary["review"]), 1)
        self.assertGreater(summary["overrun_total"], 0)
        self.assertEqual(summary["video_seconds"], 40.0)


if __name__ == "__main__":
    unittest.main()
