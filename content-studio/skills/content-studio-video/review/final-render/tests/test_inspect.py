import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

# This leaf's inspect.py shares a name with the Python standard library module.
import importlib.util

SPEC = importlib.util.spec_from_file_location(
    "content_studio_master_inspect", Path(__file__).resolve().parents[1] / "scripts" / "inspect.py")
inspector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspector)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class ExactMasterInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, name, picture, sound):
        target = self.root / name
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", picture,
            "-f", "lavfi", "-i", sound,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(target)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr[-500:])
        return target

    def test_real_black_frozen_and_silent_master_are_review_candidates(self):
        target = self.fixture("defect.mp4", "color=c=black:s=64x64:r=10:d=2",
                              "anullsrc=channel_layout=stereo:sample_rate=48000:d=2")
        digest = inspector.sha256_file(target)
        report = inspector.inspect_master(target, digest, self.root / "guides")
        kinds = {finding["kind"] for finding in report["findings"]}
        self.assertTrue({"black", "frozen", "audio_silence"}.issubset(kinds), kinds)
        self.assertEqual(report["output_sha256"], digest)
        self.assertEqual(report["status"], "REVIEW")
        self.assertTrue(all(Path(item["path"]).is_file() for item in report["safe_zone_guides"]))
        self.assertIsNone(report["loudness"]["integrated_lufs"])
        self.assertEqual(json.loads(json.dumps(report))["output_sha256"], digest)

    def test_moving_picture_with_tone_has_no_forced_defect(self):
        target = self.fixture("moving.mp4", "testsrc2=size=64x64:rate=10:duration=2",
                              "sine=frequency=440:duration=2")
        report = inspector.inspect_master(target, inspector.sha256_file(target))
        self.assertEqual(report["status"], "SKIP")
        self.assertEqual(report["findings"], [])
        self.assertIsNotNone(report["loudness"]["integrated_lufs"])

    def test_utf8_media_tags_and_filename_are_inspected(self):
        target = self.root / "dolphin-🐬.mp4"
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=64x64:rate=10:duration=1",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-metadata", "title=Dolphin 🐬", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(target),
        ], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(result.returncode, 0, result.stderr[-500:])
        report = inspector.inspect_master(target, inspector.sha256_file(target))
        self.assertEqual(report["format"]["width"], 64)

    def test_stale_master_hash_fails_before_inspection(self):
        target = self.fixture("stale.mp4", "testsrc2=size=64x64:rate=10:duration=1",
                              "sine=frequency=440:duration=1")
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            inspector.inspect_master(target, "0" * 64)

    def test_one_frame_brightness_excursion_is_candidate_only(self):
        log = "\n".join([
            "frame:0 pts:0 pts_time:0.0 lavfi.signalstats.YAVG=40",
            "frame:1 pts:1 pts_time:0.1 lavfi.signalstats.YAVG=180",
            "frame:2 pts:2 pts_time:0.2 lavfi.signalstats.YAVG=42",
            "lavfi.freezedetect.freeze_start: 0.3",
            "lavfi.freezedetect.freeze_end: 1.3",
        ])
        findings = inspector._video_candidates(log, 2)
        self.assertEqual({item["kind"] for item in findings}, {"flash", "frozen"})
        self.assertTrue(all(item["status"] == "REVIEW" for item in findings))


if __name__ == "__main__":
    unittest.main()
