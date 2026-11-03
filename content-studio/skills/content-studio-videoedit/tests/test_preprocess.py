import csv
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
                 patch.object(preprocess, "command"), \
                 patch.object(preprocess, "pcm16",
                              return_value=(preprocess.SAMPLE_RATE, samples)), \
                 patch.object(preprocess, "speech_intervals",
                              side_effect=AssertionError("VAD must not run")):
                preprocess.enhance_audio(Path("in.mp4"), {"index": 1}, work, report,
                                         "ffmpeg", "off")
            self.assertEqual(report["audio"], {"speech_gain": "off", "peak_ceiling_dbfs": -1})
            self.assertEqual(report["speech_gain"], "off")
            self.assertNotIn("speech_intervals", report["audio"])

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
