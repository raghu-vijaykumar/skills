import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import preprocess


class PreprocessTest(unittest.TestCase):
    def test_voice_gain_caps_boost_and_keeps_quiet_floor(self):
        samples = np.zeros((preprocess.SAMPLE_RATE * 3, 2), dtype=np.float32)
        samples[preprocess.SAMPLE_RATE:2 * preprocess.SAMPLE_RATE] = 0.01
        envelope, gains = preprocess.gain_envelope(samples, [(1.0, 2.0)])
        self.assertEqual(gains, [13.0])
        self.assertAlmostEqual(float(envelope[0]), 10 ** (-13 / 20), places=5)
        self.assertAlmostEqual(float(envelope[int(1.5 * preprocess.SAMPLE_RATE)]),
                               10 ** (13 / 20), places=4)
        self.assertLess(float(envelope[int(0.9 * preprocess.SAMPLE_RATE)]),
                        float(envelope[int(1.5 * preprocess.SAMPLE_RATE)]))

    def test_speech_gain_off_skips_vad_and_keeps_levels(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            work = Path(scratch)
            report = {}
            samples = np.zeros((preprocess.SAMPLE_RATE, 2), dtype=np.float32)
            with patch.object(preprocess, "extract_audio"), \
                 patch.object(preprocess, "command", return_value=""), \
                 patch.object(preprocess, "pcm16",
                              return_value=(preprocess.SAMPLE_RATE, samples)), \
                 patch.object(preprocess, "speech_intervals",
                              side_effect=AssertionError("VAD must not run")):
                preprocess.enhance_audio(Path("in.mp4"), {"index": 1}, work, report,
                                         "ffmpeg", "off")
            self.assertEqual(report["audio"], {"speech_gain": "off", "level_match_db": 0.0,
                                               "level_match_bounded": False,
                                               "peak_ceiling_dbfs": -1})
            self.assertEqual(report["speech_gain"], "off")
            self.assertNotIn("speech_intervals", report["audio"])
            self.assertNotIn("fallback", report["denoise"])

    def test_denoise_that_removes_the_program_falls_back_to_source(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            work = Path(scratch)
            report = {}
            samples = np.zeros((preprocess.SAMPLE_RATE, 2), dtype=np.float32)
            # source, denoised, re-measured source, match reference
            loudness = [-19.4, -40.0, -19.4, -19.4]
            with patch.object(preprocess, "extract_audio"), \
                 patch.object(preprocess, "command", return_value=""), \
                 patch.object(preprocess, "pcm16",
                              return_value=(preprocess.SAMPLE_RATE, samples)), \
                 patch.object(preprocess, "measure_loudness", side_effect=loudness):
                preprocess.enhance_audio(Path("in.mp4"), {"index": 1}, work, report,
                                         "ffmpeg", "off")
            self.assertEqual(report["denoise"]["fallback"], "content-loss")
            self.assertEqual(report["denoise_engine"], "skipped")
            self.assertEqual(report["denoise"]["denoised_lufs"], -40.0)
            self.assertEqual(report["audio"]["level_match_db"], 0.0)

    def test_level_match_is_bounded_to_the_reference(self):
        self.assertEqual(preprocess.level_match_db(-40.0, -19.0),
                         preprocess.MAX_LEVEL_MATCH_DB)
        self.assertEqual(preprocess.level_match_db(-5.0, -19.0),
                         -preprocess.MAX_LEVEL_MATCH_DB)
        self.assertAlmostEqual(preprocess.level_match_db(-22.0, -19.0), 3.0)
        self.assertEqual(preprocess.level_match_db(None, -19.0), 0.0)

    def test_final_rerenders_when_the_audio_chain_changed(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            target = Path(scratch) / "final.mp4"
            target.write_bytes(b"")
            args = SimpleNamespace(force=False)
            self.assertFalse(preprocess.final_is_current(
                args, True, target, False, {"final_cuts": []}, []))
            self.assertTrue(preprocess.final_is_current(
                args, True, target, True, {"final_cuts": []}, []))
            self.assertFalse(preprocess.final_is_current(
                SimpleNamespace(force=True), True, target, True, {"final_cuts": []}, []))

    def test_tuning_profile_reads_the_chosen_candidate(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch) / "analysis" / "tuning"
            folder = root / "001 - clip"
            folder.mkdir(parents=True)
            params = {"name": "pf-30", "engine": "deepfilter", "post_filter": True,
                      "beta": 0.02, "highpass": 0, "attenuation": 30}
            (folder / "profile.json").write_text(json.dumps(
                {"chosen": "pf-30", "candidates": [
                    {"name": "default", "params": {"name": "default"}},
                    {"name": "pf-30", "params": params}]}), encoding="utf-8")
            args = SimpleNamespace(profiles=True, tuning_root=root)
            applied = preprocess.tuning_profile(args, Path("001 - clip.mp4"))
            self.assertEqual(applied["chosen"], "pf-30")
            self.assertEqual(applied["params"]["attenuation"], 30)
            disabled = SimpleNamespace(profiles=False, tuning_root=root)
            self.assertIsNone(preprocess.tuning_profile(disabled, Path("001 - clip.mp4")))
            missing = SimpleNamespace(profiles=True, tuning_root=root)
            self.assertIsNone(preprocess.tuning_profile(missing, Path("002 - other.mp4")))

    def test_none_profile_skips_denoise_but_keeps_highpass(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            work = Path(scratch)
            report = {}
            samples = np.zeros((preprocess.SAMPLE_RATE, 2), dtype=np.float32)
            profile = {"chosen": "none",
                       "params": {"name": "none", "engine": "none", "highpass": 80}}
            with patch.object(preprocess, "extract_audio"), \
                 patch.object(preprocess, "command", return_value="") as run, \
                 patch.object(preprocess, "deepfilter",
                              side_effect=AssertionError("denoise must not run")), \
                 patch.object(preprocess, "pcm16",
                              return_value=(preprocess.SAMPLE_RATE, samples)), \
                 patch.object(preprocess, "measure_loudness", return_value=-20.0):
                preprocess.enhance_audio(Path("in.mp4"), {"index": 1}, work, report,
                                         "deepfilter", "off", profile)
            self.assertEqual(report["denoise_engine"], "skipped")
            self.assertEqual(report["tuning"]["chosen"], "none")
            commands = [" ".join(call.args[0]) for call in run.call_args_list]
            self.assertTrue(any("highpass=f=80" in command for command in commands))

    def test_profile_passes_attenuation_to_deepfilter(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            work = Path(scratch)
            report = {}
            samples = np.zeros((preprocess.SAMPLE_RATE, 2), dtype=np.float32)
            profile = {"chosen": "pf-30",
                       "params": {"name": "pf-30", "engine": "deepfilter",
                                  "post_filter": True, "beta": 0.02,
                                  "highpass": 0, "attenuation": 30}}
            with patch.object(preprocess, "extract_audio"), \
                 patch.object(preprocess, "command", return_value=""), \
                 patch.object(preprocess, "deepfilter",
                              return_value=Path("enhanced.wav")) as denoise, \
                 patch.object(preprocess, "pcm16",
                              return_value=(preprocess.SAMPLE_RATE, samples)), \
                 patch.object(preprocess, "measure_loudness", return_value=-20.0):
                preprocess.enhance_audio(Path("in.mp4"), {"index": 1}, work, report,
                                         "auto", "off", profile)
            self.assertEqual(denoise.call_args.args[2:], (30, True, 0.02))
            self.assertEqual(report["denoise_engine"], "deepfilter")

    def test_blur_candidates_are_review_only_and_use_source_times(self):
        times = [i / 10 for i in range(10)]
        scores = [100, 95, 90, 4, 3, 95, 100, 90, 95, 100]
        rows = preprocess.blur_candidates(times, scores, 1.0)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["start"], rows[0]["end"]), (0.25, 0.45))
        self.assertEqual(rows[0]["remove"], "")

    def test_review_requires_explicit_yes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            path = Path(scratch) / "review.csv"
            with path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, ["id", "start", "end", "score", "remove", "notes"])
                writer.writeheader()
                writer.writerow({"id": 1, "start": 1, "end": 2, "remove": ""})
                writer.writerow({"id": 2, "start": 4, "end": 5, "remove": "yes"})
            self.assertEqual(preprocess.approved_cuts(path), [(4, 5)])
            self.assertEqual(preprocess.keep_ranges(6, [(4, 5)]), [(0, 4), (5, 6)])

    def test_single_approved_range_trims_video_and_audio(self):
        graph, video, audio = preprocess.video_filter([(0, 2.5)], {"width": 1920, "height": 1080})
        self.assertIn("trim=start=0.000000:end=2.500000", graph)
        self.assertIn("atrim=start=0.000000:end=2.500000", graph)
        self.assertEqual((video, audio), ("[v]", "[a]"))

    def test_dolby_vision_rejects_hlg_only_export(self):
        source = {"width": 1920, "height": 1080, "color_primaries": "bt2020",
                  "color_transfer": "arib-std-b67", "color_space": "bt2020nc"}
        exported = dict(source, codec_type="video", duration="2", side_data_list=[])
        with patch.object(preprocess, "probe", return_value={"streams": [exported, {
                "codec_type": "audio", "channels": 2, "duration": "2"}],
                "format": {"duration": "2"}}), \
             patch.object(preprocess, "frame_times", return_value=[0, 1]), \
             patch.object(preprocess, "frame_count", return_value=2):
            with self.assertRaisesRegex(preprocess.ProcessingError, "lost Dolby Vision"):
                preprocess.validate_render(Path("in.mov"), Path("out.mov"), source, None, True)

    def test_draft_discovery_ignores_finished_video(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            draft = root / "out-of-office" / "drafts" / "trip"
            draft.mkdir(parents=True)
            for name in ("IMG_1.MOV", "video.mp4", "notes.txt"):
                (draft / name).touch()
            args = SimpleNamespace(cfg={"workspace": str(root),
                                        "channels": {"out-of-office": {"name": "Out of Office"}}},
                                   channel="out-of-office", path=None, draft="trip",
                                   clip=None, out=None)
            sources, output = preprocess.source_files(args)
            self.assertEqual([p.name for p in sources], ["IMG_1.MOV"])
            self.assertEqual(output, draft / ".content-studio" / "processed-clips")

    def test_render_tolerates_source_audio_tail(self):
        source_video = {"codec_type": "video", "width": 1920, "height": 1080,
                        "duration": "15.755", "color_primaries": "bt709",
                        "color_transfer": "bt709", "color_space": "bt709"}
        source_audio = {"codec_type": "audio", "duration": "15.808"}
        output_video = dict(source_video, duration="15.755")
        output_audio = {"codec_type": "audio", "channels": 2, "duration": "15.82"}
        probes = {
            Path("in.mp4"): {"streams": [source_video, source_audio],
                             "format": {"duration": "15.822"}},
            Path("out.mp4"): {"streams": [output_video, output_audio],
                              "format": {"duration": "15.822"}},
        }
        with patch.object(preprocess, "probe", side_effect=lambda path: probes[path]), \
             patch.object(preprocess, "frame_times", return_value=[0, 1]), \
             patch.object(preprocess, "frame_count", return_value=2), \
             patch.object(preprocess, "command"):
            preprocess.validate_render(Path("in.mp4"), Path("out.mp4"),
                                       source_video, None, False)

    def test_render_rejects_audio_drift_beyond_source_tail(self):
        source_video = {"codec_type": "video", "width": 1920, "height": 1080,
                        "duration": "15.755", "color_primaries": "bt709",
                        "color_transfer": "bt709", "color_space": "bt709"}
        source_audio = {"codec_type": "audio", "duration": "15.808"}
        output_video = dict(source_video)
        output_audio = {"codec_type": "audio", "channels": 2, "duration": "16.05"}
        probes = {
            Path("in.mp4"): {"streams": [source_video, source_audio],
                             "format": {"duration": "15.822"}},
            Path("out.mp4"): {"streams": [output_video, output_audio],
                              "format": {"duration": "15.822"}},
        }
        with patch.object(preprocess, "probe", side_effect=lambda path: probes[path]), \
             patch.object(preprocess, "frame_times", return_value=[0, 1]), \
             patch.object(preprocess, "frame_count", return_value=2), \
             patch.object(preprocess, "command"):
            with self.assertRaisesRegex(preprocess.ProcessingError, "audio sync"):
                preprocess.validate_render(Path("in.mp4"), Path("out.mp4"),
                                           source_video, None, False)

    def test_failed_dolby_proof_is_removed(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            output = Path(scratch) / "dv-proof.mov"
            output.write_bytes(b"unverified")
            with patch.object(preprocess, "stabilized_render",
                              side_effect=preprocess.ProcessingError("RPU missing")):
                with self.assertRaisesRegex(preprocess.ProcessingError, "RPU missing"):
                    preprocess.safe_render(Path("in.mov"), Path("audio.wav"), {},
                                           Path(scratch), output, [])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
