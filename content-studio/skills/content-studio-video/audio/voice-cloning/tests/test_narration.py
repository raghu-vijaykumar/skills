"""Unit tests for narration validation, reuse, and timeline fitting."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import narration


class ValidateScriptTest(unittest.TestCase):
    def test_detects_mixed_kannada_latin_tts_without_flagging_single_script(self):
        segments = [
            {"id": "raw", "text": "ಪಾಮ್ Jumeirah ಕಡೆ"},
            {"id": "phonetic", "text": "ಪಾಮ್ ಜುಮೇರಾ ಕಡೆ"},
            {"id": "english", "text": "Palm Jumeirah"},
        ]
        self.assertEqual(narration.mixed_kannada_latin_ids(segments), ["raw"])

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

    def test_strict_scene_preserves_one_times_speed_and_exact_start(self):
        segments = [
            {"id": "a", "start": 2.0, "end": 10.0, "text": "one two"},
            {"id": "b", "start": 11.0, "end": 20.0, "text": "three four"},
        ]
        placed = narration.fit_timeline(
            segments, {"a": 7.25, "b": 8.0}, 21.0, strict_scene_slots=True
        )
        self.assertEqual([item["tempo"] for item in placed], [1.0, 1.0])
        self.assertEqual(placed[0]["start"], 2.0)
        self.assertEqual(placed[0]["end"], 9.25)
        self.assertEqual(placed[1]["end"], 19.0)

    def test_strict_scene_rejects_audio_even_when_next_cue_has_slack(self):
        segments = [
            {"id": "a", "start": 0.0, "end": 10.0, "text": "one two"},
            {"id": "b", "start": 20.0, "end": 30.0, "text": "three four"},
        ]
        with self.assertRaisesRegex(ValueError, "after visual end.*shorten the script"):
            narration.fit_timeline(
                segments, {"a": 11.0, "b": 5.0}, 31.0, strict_scene_slots=True
            )

    def test_strict_scene_allows_final_cue_to_end_with_picture(self):
        placed = narration.fit_timeline(
            [{"id": "a", "start": 0.0, "end": 10.0, "text": "end"}],
            {"a": 10.0}, 10.0, strict_scene_slots=True,
        )
        self.assertEqual(placed[0]["end"], 10.0)

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

    def test_fit_slot_corrects_small_fast_and_slow_voice_variations(self):
        segments = [
            {"id": "a", "start": 0.0, "end": 17.0, "text": "one two three"},
            {"id": "b", "start": 21.0, "end": 37.0, "text": "one two three"},
        ]
        placed = narration.fit_timeline(
            segments, {"a": 17.536, "b": 15.488}, 42.0, fit_slot=True
        )
        self.assertAlmostEqual(placed[0]["tempo"], 17.536 / 17.0, places=4)
        self.assertAlmostEqual(placed[1]["tempo"], 15.488 / 16.0, places=4)
        self.assertAlmostEqual(placed[0]["end"], 17.0, places=2)
        self.assertAlmostEqual(placed[1]["end"], 37.0, places=2)
        self.assertFalse(any(item["needs_review"] for item in placed))
        self.assertEqual(narration.timeline_summary(placed, 42.0)["max_narration_gap_seconds"], 5.0)

    def test_fit_slot_reports_unacceptable_stretch(self):
        placed = narration.fit_timeline(
            self.segments(), {"a": 10.0, "b": 30.0}, 40.0,
            fit_slot=True, min_tempo=0.88, max_tempo=1.12,
        )
        self.assertEqual(placed[0]["tempo"], 0.88)
        self.assertLess(placed[0]["pace_delta_seconds"], -0.05)
        self.assertEqual(placed[1]["tempo"], 1.12)
        self.assertGreater(placed[1]["pace_delta_seconds"], 0.05)
        self.assertTrue(all(item["needs_review"] for item in placed))

    def test_fit_slot_rejects_invalid_min_tempo(self):
        with self.assertRaises(ValueError):
            narration.fit_timeline(self.segments(), {"a": 10.0, "b": 10.0}, 40.0,
                                   fit_slot=True, min_tempo=0)

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
