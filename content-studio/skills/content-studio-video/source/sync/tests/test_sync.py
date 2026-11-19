import importlib.util
import shutil
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync.py"
SPEC = importlib.util.spec_from_file_location("content_studio_sync", SCRIPT)
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def wav(self, name, samples):
        path = self.root / name
        with wave.open(str(path), "wb") as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(8000)
            target.writeframes((np.clip(samples, -1, 1) * 30000).astype("<i2").tobytes())
        return path

    def signal(self, seconds=10):
        random = np.random.default_rng(7)
        samples = random.standard_normal(seconds * 8000)
        amplitudes = random.uniform(.05, .7, seconds * 10)
        return (samples * np.repeat(amplitudes, 800) * .25).astype(np.float32)

    def test_delayed_recorder_offset_and_bounded_audition(self):
        base = self.signal()
        reference = self.wav("camera.wav", np.pad(base, (3200, 0)))
        external = self.wav("recorder.wav", base)
        report = sync.analyze(reference, external, 3)
        self.assertEqual(report["status"], "REVIEW", report)
        self.assertAlmostEqual(report["offset_seconds"], .4, delta=.04)
        self.assertIsNone(report["drift_ppm"])
        audition = self.root / "audition.wav"
        sync.audition(report, audition, 1, 2)
        self.assertTrue(audition.is_file())
        external.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "stale"):
            sync.audition(report, audition, 1, 2)

    def test_drift_is_estimated_from_separate_anchors(self):
        base = self.signal(55)
        reference = self.wav("long-camera.wav", np.pad(base, (3200, 0)))
        positions = np.arange(len(base)) * 1.001
        recorder = np.interp(positions, np.arange(len(base)), base, left=0, right=0)
        external = self.wav("long-recorder.wav", recorder)
        report = sync.analyze(reference, external, 4)
        self.assertEqual(report["status"], "REVIEW", report)
        self.assertAlmostEqual(report["offset_seconds"], .4, delta=.06)
        self.assertAlmostEqual(report["drift_ppm"], 1000, delta=500)
        self.assertEqual(len(report["anchors"]), 2)

    def test_silence_and_repeated_pattern_fail_closed(self):
        silence = self.wav("silent.wav", np.zeros(8000 * 10))
        active = self.wav("active.wav", self.signal())
        report = sync.analyze(silence, active, 3)
        self.assertEqual(report["status"], "UNSUPPORTED")
        self.assertIsNone(report["offset_seconds"])
        pattern = self.signal(1)
        repeated = np.tile(pattern, 12)
        one = self.wav("repeat-one.wav", repeated)
        two = self.wav("repeat-two.wav", repeated)
        report = sync.analyze(one, two, 4)
        self.assertEqual(report["status"], "UNSUPPORTED", report)
        self.assertIn("ambiguous", report["reason"])


if __name__ == "__main__":
    unittest.main()
