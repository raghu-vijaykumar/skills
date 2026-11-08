import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

REFLECTION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REFLECTION / "scripts"))
sys.path.insert(0, str(REFLECTION / "backends"))

import ai  # noqa: E402
from dsrnet.geometry import working_size  # noqa: E402


class FakeBackend:
    """Deterministic stand-in for DSRNet; no torch, no GPU, no checkpoint."""

    weights = Path("fake-dsrnet.ckpt")
    device = "cpu"
    half = False
    peak_memory_mb = 0.0

    def resize(self, rgb, width, height):
        image = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
        return np.asarray(image.resize((width, height), Image.BICUBIC),
                          dtype=np.float32) / 255.0

    def reflect(self, rgb, max_width=640):
        height, width, _ = rgb.shape
        work_width, work_height = working_size(width, height, max_width)
        small = self.resize(rgb, work_width, work_height)
        clean = np.clip(small * 0.93, 0.0, 1.0)
        reflection = np.full_like(small, 0.03)
        return {
            "work_size": [work_width, work_height],
            "small": small,
            "clean": clean,
            "reflection": reflection,
            "residual": small - clean - reflection,
            "clean_low": self.resize(clean, width, height),
            "input_low": self.resize(small, width, height),
        }

    def close(self):
        pass


def metrics(candidate, luma=0.5, saturation=0.25, clip=0.02, sharpness=0.10):
    return {
        "candidate_fraction": candidate,
        "glare_fraction": candidate / 3,
        "veil_fraction": candidate / 2,
        "luma_mean": luma,
        "saturation_mean": saturation,
        "clip_high": clip,
        "sharpness": sharpness,
    }


def sample(before, after):
    return {"frame": 0, "at_seconds": 0.0, "before": before, "after": after,
            "reflection_energy": 0.03}


class GeometryTest(unittest.TestCase):
    def test_working_size_is_multiple_of_32_and_keeps_aspect(self):
        width, height = working_size(1920, 1080, 640)
        self.assertEqual((width, height), (640, 352))
        self.assertEqual(width % 32, 0)
        self.assertEqual(height % 32, 0)
        self.assertAlmostEqual(width / height, 1920 / 1080, places=1)

    def test_working_size_never_goes_below_the_encoder_minimum(self):
        width, height = working_size(100, 40, 20)
        self.assertGreaterEqual(width, 32)
        self.assertGreaterEqual(height, 32)
        self.assertEqual(width % 32, 0)
        self.assertEqual(height % 32, 0)


class FuseTest(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(7)
        self.native = rng.random((48, 64, 3), dtype=np.float32)
        self.input_low = rng.random((48, 64, 3), dtype=np.float32)
        self.clean_low = rng.random((48, 64, 3), dtype=np.float32)

    def test_zero_strength_returns_the_native_frame(self):
        fused = ai.detail_preserving_fuse(self.native, self.clean_low,
                                          self.input_low, 0.0)
        np.testing.assert_array_equal(fused, self.native)

    def test_identity_prediction_preserves_the_native_frame(self):
        fused = ai.detail_preserving_fuse(self.native, self.input_low,
                                          self.input_low, 1.0)
        np.testing.assert_allclose(fused, self.native, atol=1e-6)

    def test_identity_prediction_keeps_high_frequency_detail(self):
        fused = ai.detail_preserving_fuse(self.native, self.native,
                                          self.native, 1.0)
        np.testing.assert_allclose(fused, self.native, atol=1e-6)

    def test_correction_is_bounded_to_unit_range(self):
        fused = ai.detail_preserving_fuse(np.ones((4, 4, 3), np.float32),
                                          np.zeros((4, 4, 3), np.float32),
                                          np.ones((4, 4, 3), np.float32), 3.0)
        self.assertGreaterEqual(float(fused.min()), 0.0)
        self.assertLessEqual(float(fused.max()), 1.0)


class EvaluateTest(unittest.TestCase):
    def test_measurable_reduction_needs_review(self):
        result = ai.evaluate(
            [sample(metrics(0.12), metrics(0.10, luma=0.49))],
            reflection_energy=0.03, flicker_ratio=1.02)
        self.assertEqual(result["decision"], "REVIEW")
        self.assertTrue(result["review"]["required"])
        self.assertEqual(result["review"]["status"], "review_required")
        self.assertEqual(result["failed_checks"], [])

    def test_no_reduction_is_skipped(self):
        result = ai.evaluate(
            [sample(metrics(0.12), metrics(0.12))],
            reflection_energy=0.03, flicker_ratio=1.0)
        self.assertEqual(result["decision"], "SKIP")

    def test_backend_abstention_is_skipped(self):
        result = ai.evaluate(
            [sample(metrics(0.12), metrics(0.10))],
            reflection_energy=0.0005, flicker_ratio=1.0)
        self.assertEqual(result["decision"], "SKIP")
        self.assertIn("backend_detected_reflection", result["failed_checks"])

    def test_exposure_shift_is_rejected(self):
        result = ai.evaluate(
            [sample(metrics(0.12), metrics(0.10, luma=0.30))],
            reflection_energy=0.03, flicker_ratio=1.0)
        self.assertEqual(result["decision"], "REJECTED")
        self.assertIn("luma_change", result["failed_checks"])

    def test_temporal_flicker_is_rejected(self):
        result = ai.evaluate(
            [sample(metrics(0.12), metrics(0.10, luma=0.49))],
            reflection_energy=0.03, flicker_ratio=2.0)
        self.assertEqual(result["decision"], "REJECTED")
        self.assertIn("temporal_flicker", result["failed_checks"])

    def test_sharpness_loss_is_rejected(self):
        result = ai.evaluate(
            [sample(metrics(0.12, sharpness=0.10),
                    metrics(0.10, luma=0.49, sharpness=0.05))],
            reflection_energy=0.03, flicker_ratio=1.0)
        self.assertEqual(result["decision"], "REJECTED")
        self.assertIn("sharpness_ratio", result["failed_checks"])


class EndToEndTest(unittest.TestCase):
    def make_video(self, path):
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=0x606060:s=320x180:r=30:d=1",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
            "-vf", "drawbox=x=100:y=40:w=120:h=90:color=0xF2F2F2:t=fill",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(path)],
            check=True, capture_output=True)

    def test_run_writes_a_gated_review_package(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "shop.mp4"
            self.make_video(source)
            output = root / "shop-ai-review.mp4"
            work = root / "work"
            report = ai.run(source, output, work, backend=FakeBackend())
            self.assertIn(report["decision"]["decision"],
                          {"REVIEW", "SKIP", "REJECTED"})
            self.assertTrue(report["decision"]["review"]["required"])
            self.assertEqual(report["processing"]["frames"], 30)
            self.assertTrue(report["decision"]["checks"])
            self.assertTrue((work / "report.json").is_file())
            self.assertTrue((work / "report.md").is_file())
            self.assertTrue((work / "contact-sheet.jpg").is_file())
            self.assertGreater(output.stat().st_size, 0)
            saved = json.loads((work / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["backend"]["work_size"], [320, 160])
            self.assertTrue(saved["metrics"]["samples"])
            self.assertEqual(saved["source"]["width"], 320)


if __name__ == "__main__":
    unittest.main()
