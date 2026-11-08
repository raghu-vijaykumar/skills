import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tune


def metrics(**overrides):
    base = {"noise_floor_dbfs": -50.0, "speech_level_dbfs": -18.0, "snr_db": 32.0,
            "noise_modulation_db": 2.0, "peak_dbfs": -1.2, "clip_ratio": 0.0,
            "speech_band_ratio": 0.55, "duration_seconds": 20.0,
            "content_loss_db": 0.0, "level_match_db": 0.0}
    base.update(overrides)
    return base


class TuneTest(unittest.TestCase):
    def test_default_candidate_is_first_and_matches_preprocess_chain(self):
        deepfilter = tune.candidate_grid("deep-filter.exe")
        self.assertEqual(deepfilter[0]["name"], "default")
        self.assertFalse(deepfilter[0]["post_filter"])
        self.assertEqual(deepfilter[0]["highpass"], 0)
        self.assertIsNone(deepfilter[0]["attenuation"])
        ffmpeg = tune.candidate_grid(None)
        self.assertEqual(ffmpeg[0]["name"], "default")
        self.assertEqual(ffmpeg[0]["nr"], 12)

    def test_every_grid_can_leave_the_clip_alone(self):
        for executable in ("deep-filter.exe", None):
            names = [candidate["name"] for candidate in tune.candidate_grid(executable)]
            self.assertIn("none", names)

    def test_deepfilter_grid_spans_attenuation_limits(self):
        grid = tune.candidate_grid("deep-filter.exe")
        limits = {candidate["name"]: candidate.get("attenuation") for candidate in grid}
        self.assertEqual(limits["pf-safe"], 10)
        self.assertEqual(limits["pf-20"], 20)
        self.assertEqual(limits["pf-30"], 30)
        self.assertIsNone(limits["pf-strong"])

    def test_extreme_suppression_is_penalised(self):
        source = metrics()
        moderate = metrics(noise_floor_dbfs=source["noise_floor_dbfs"] - 24.0,
                           snr_db=source["snr_db"] + 20.0)
        extreme = metrics(noise_floor_dbfs=source["noise_floor_dbfs"] - 90.0,
                          snr_db=source["snr_db"] + 90.0)
        moderate_score, moderate_issues = tune.score_candidate(moderate, source)
        extreme_score, extreme_issues = tune.score_candidate(extreme, source)
        self.assertNotIn("over-suppressed", moderate_issues)
        self.assertIn("over-suppressed", extreme_issues)
        self.assertGreater(moderate_score - extreme_score, 20.0)

    def test_content_loss_blocks_a_candidate(self):
        source = metrics()
        destroyed = metrics(noise_floor_dbfs=-72.0, snr_db=54.0,
                            content_loss_db=18.0, level_match_db=13.0)
        score, issues = tune.score_candidate(destroyed, source)
        self.assertIn("content loss", issues)
        self.assertGreater(score, 50)
        scored = [{"name": "default", "score": score, "issues": issues},
                  {"name": "none", "score": 30.0, "issues": []}]
        self.assertEqual(tune.choose(scored, 1.5)["chosen"], "none")

    def test_disqualified_default_is_named_in_the_reason(self):
        scored = [{"name": "default", "score": 90.0, "issues": ["content loss"]},
                  {"name": "pf-safe", "score": 30.0, "issues": []},
                  {"name": "none", "score": 24.0, "issues": []}]
        decision = tune.choose(scored, 1.5)
        self.assertEqual(decision["chosen"], "pf-safe")
        self.assertIn("content loss", decision["reason"])
        self.assertIn("disqualified", decision["reason"])

    def test_denoise_must_measurably_reduce_noise_to_be_applied(self):
        source = metrics(noise_floor_dbfs=-32.5, snr_db=5.6)
        scored = [
            {"name": "default", "score": 80.0, "issues": ["content loss"]},
            {"name": "pf-safe", "score": 29.29, "issues": [],
             "metrics": metrics(noise_floor_dbfs=-32.7, snr_db=5.8)},
            {"name": "none", "score": 29.21, "issues": [],
             "metrics": metrics(noise_floor_dbfs=-32.5, snr_db=5.6)},
        ]
        decision = tune.choose(scored, 1.5, source)
        self.assertEqual(decision["chosen"], "none")
        self.assertIn("did not measurably reduce noise", decision["reason"])

    def test_measurable_win_over_no_denoise_is_applied(self):
        source = metrics(noise_floor_dbfs=-32.5, snr_db=5.6)
        scored = [
            {"name": "default", "score": 80.0, "issues": ["content loss"]},
            {"name": "pf-safe", "score": 40.0, "issues": [],
             "metrics": metrics(noise_floor_dbfs=-40.5, snr_db=13.6)},
            {"name": "none", "score": 24.0, "issues": [],
             "metrics": metrics(noise_floor_dbfs=-32.5, snr_db=5.6)},
        ]
        self.assertEqual(tune.choose(scored, 1.5, source)["chosen"], "pf-safe")

    def test_over_suppressed_default_is_not_protected_by_margin(self):
        scored = [
            {"name": "default", "score": 81.96,
             "issues": ["over-suppressed", "level drift"]},
            {"name": "pf-30", "score": 82.35, "issues": ["level drift"]},
            {"name": "none", "score": 26.31, "issues": []},
        ]
        decision = tune.choose(scored, 1.5)
        self.assertEqual(decision["chosen"], "pf-30")
        self.assertIn("disqualified", decision["reason"])

    def test_windows_spread_and_cover_short_clips(self):
        self.assertEqual(tune.windows_for(12.0, 40.0), [(0.0, 12.0)])
        windows = tune.windows_for(100.0, 40.0)
        self.assertEqual(len(windows), 2)
        self.assertTrue(all(0.0 <= start < end <= 100.0 for start, end in windows))
        self.assertLess(windows[0][0], windows[1][0])

    def test_more_noise_reduction_scores_higher(self):
        source = metrics()
        light = metrics(noise_floor_dbfs=-56.0, snr_db=38.0)
        heavy = metrics(noise_floor_dbfs=-66.0, snr_db=48.0)
        light_score, _ = tune.score_candidate(light, source)
        heavy_score, _ = tune.score_candidate(heavy, source)
        self.assertGreater(heavy_score, light_score)

    def test_clipping_and_band_loss_are_flagged(self):
        source = metrics()
        clipped = metrics(peak_dbfs=-0.1, clip_ratio=0.001)
        _, issues = tune.score_candidate(clipped, source)
        self.assertIn("clipping", issues)
        hollow = metrics(speech_band_ratio=0.2)
        _, issues = tune.score_candidate(hollow, source)
        self.assertIn("speech-band loss", issues)

    def test_margin_keeps_the_current_default(self):
        scored = [
            {"name": "default", "score": 60.0, "issues": []},
            {"name": "pf", "score": 61.0, "issues": []},
        ]
        self.assertEqual(tune.choose(scored, 1.5)["chosen"], "default")

    def test_clear_win_replaces_the_default(self):
        scored = [
            {"name": "default", "score": 60.0, "issues": []},
            {"name": "pf", "score": 75.0, "issues": []},
        ]
        self.assertEqual(tune.choose(scored, 1.5)["chosen"], "pf")

    def test_no_valid_candidate_returns_none(self):
        scored = [{"name": "default", "score": 10.0, "issues": ["clipping"]},
                  {"name": "pf", "score": 9.0, "issues": ["speech-band loss"]}]
        self.assertIsNone(tune.choose(scored, 1.5)["chosen"])

    def test_select_clips_spans_durations(self):
        files = [Path(f"clip{index}.MP4") for index in range(10)]
        durations = {f"clip{index}.MP4": float(index + 6) for index in range(10)}
        with patch.object(tune, "probe",
                          side_effect=lambda path: {"format": {"duration": str(durations[path.name])}}):
            picked = tune.select_clips(files, 3)
        self.assertEqual([path.name for path in picked], ["clip0.MP4", "clip4.MP4", "clip9.MP4"])

    def test_aggregate_averages_numeric_fields(self):
        summary = tune.aggregate([metrics(noise_floor_dbfs=-40.0),
                                  metrics(noise_floor_dbfs=-60.0)])
        self.assertAlmostEqual(summary["noise_floor_dbfs"], -50.0)

    def test_summary_players_link_into_the_clip_folder(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            folder = root / "001 - clip" / "candidates"
            folder.mkdir(parents=True)
            (folder / "window-1-default.wav").write_bytes(b"")
            (folder / "window-1-pf.wav").write_bytes(b"")
            profile = {
                "clip": "001 - clip.mp4", "chosen": "pf", "reason": "pf won",
                "runner_up": "none", "runner_up_score": 20.0,
                "source_metrics": metrics(), "candidates": [
                    {"name": "default", "score": 70.0, "issues": [],
                     "metrics": metrics()},
                    {"name": "pf", "score": 80.0, "issues": [], "metrics": metrics()},
                ],
            }
            tune.write_summary([profile], root)
            html = (root / "tuning.html").read_text(encoding="utf-8")
            self.assertIn("001%20-%20clip/candidates/window-1-default.wav", html)
            self.assertIn("001%20-%20clip/candidates/window-1-pf.wav", html)


if __name__ == "__main__":
    unittest.main()
