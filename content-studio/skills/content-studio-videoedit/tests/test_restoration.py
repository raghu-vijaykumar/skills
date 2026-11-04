import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import restoration
import upscale


def make_video(path, size="320x180", duration=1):
    subprocess.run([
        "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=30:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={duration}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-shortest", str(path)], check=True, capture_output=True)


def summary(sharp=0.05, noise=0.01, luma=0.5, clip=0.0):
    return {"edge_sharpness": sharp, "noise_flat": noise,
            "luma_mean": luma, "clip_high": clip}


def preview(lanczos=None, ai=None, motion=1.0, jitter=0.05):
    return {"lanczos": {"summary": lanczos or summary()},
            "ai": {"summary": ai or summary()},
            "temporal": {"motion_ratio": motion, "sharpness_jitter": jitter}}


class RestorationTest(unittest.TestCase):
    def test_decision_fix_when_detail_improves_cleanly(self):
        result = restoration.decide(preview(ai=summary(sharp=0.07)))
        self.assertEqual(result["decision"], "FIX")
        self.assertGreater(result["metrics"]["sharpness_gain"], 0.03)

    def test_decision_skip_when_gain_is_not_measurable(self):
        result = restoration.decide(preview(ai=summary(sharp=0.051)))
        self.assertEqual(result["decision"], "SKIP")
        self.assertIn("no_measurable_detail_gain", result["reasons"])

    def test_decision_unsupported_on_temporal_flicker(self):
        result = restoration.decide(preview(ai=summary(sharp=0.09), motion=2.6))
        self.assertEqual(result["decision"], "UNSUPPORTED")
        self.assertIn("temporal_flicker", result["reasons"])

    def test_decision_review_on_borderline_noise(self):
        result = restoration.decide(preview(ai=summary(sharp=0.08, noise=0.013)))
        self.assertEqual(result["decision"], "REVIEW")
        self.assertIn("noise_increase", result["reasons"])

    def test_unmeasurable_metrics_never_report_success(self):
        result = restoration.decide(preview(
            ai=summary(sharp=0.09, noise=float("nan"))))
        self.assertEqual(result["decision"], "REVIEW")
        self.assertIn("unmeasurable_metrics", result["reasons"])

    def test_decision_unsupported_on_clipping(self):
        result = restoration.decide(preview(ai=summary(sharp=0.08, clip=0.03)))
        self.assertEqual(result["decision"], "UNSUPPORTED")
        self.assertIn("clipping", result["reasons"])

    def test_analyze_skips_a_clip_already_at_target(self):
        info = {"width": 640, "height": 360, "duration": 1.0, "pix_fmt": "yuv420p",
                "color_transfer": "bt709", "dolby_vision": False}
        with patch.object(upscale, "probe", return_value=info), \
             patch.object(upscale, "source_hash", return_value="hash"):
            result = restoration.analyze_clip(Path("in.mp4"), (640, 360))
        self.assertEqual(result["decision"], "SKIP")
        self.assertEqual(result["reasons"], ["already_at_target"])

    def test_analyze_never_approves_hdr_for_the_frame_pipeline(self):
        info = {"width": 1920, "height": 1080, "duration": 5.0,
                "pix_fmt": "yuv420p10le", "color_transfer": "arib-std-b67",
                "dolby_vision": False}
        with patch.object(upscale, "probe", return_value=info), \
             patch.object(upscale, "source_hash", return_value="hash"):
            result = restoration.analyze_clip(Path("in.mp4"), (3840, 2160))
        self.assertEqual(result["decision"], "UNSUPPORTED")
        self.assertIn("hdr_step_not_approved", result["reasons"])

    def test_analyze_marks_a_resolution_gap_as_candidate(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            source = Path(scratch) / "clip.mp4"
            make_video(source)
            result = restoration.analyze_clip(source, (640, 360))
        self.assertEqual(result["decision"], "REVIEW")
        self.assertTrue(result["needs_preview"])
        self.assertIn("candidate_needs_preview", result["reasons"])
        self.assertIn("edge_sharpness", result["source_metrics"])

    def test_preview_window_stays_inside_the_clip(self):
        self.assertEqual(restoration.preview_window(4.0, 8.0), (0.0, 4.0))
        start, seconds = restoration.preview_window(30.0, 8.0)
        self.assertAlmostEqual(seconds, 8.0)
        self.assertGreaterEqual(start, 0.0)
        self.assertLessEqual(start + seconds, 30.0)

    def test_temporal_profile_of_identical_outputs_is_stable(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            left = root / "left.mp4"
            right = root / "right.mp4"
            make_video(left)
            make_video(right)
            result = restoration.temporal_profile(left, right, 0.1, root / "tmp")
        self.assertEqual(result["frames"], 8)
        self.assertAlmostEqual(result["motion_ratio"], 1.0, delta=0.12)
        self.assertLess(result["sharpness_jitter"], 0.05)

    def test_preview_refuses_hdr_sources(self):
        info = {"width": 1920, "height": 1080, "duration": 5.0,
                "pix_fmt": "yuv420p10le", "color_transfer": "arib-std-b67",
                "dolby_vision": False}
        with patch.object(upscale, "probe", return_value=info):
            with self.assertRaisesRegex(upscale.UpscaleError, "HDR"):
                restoration.preview_clip(Path("in.mp4"), (3840, 2160))

    def test_timeline_sources_keep_referenced_clips_only(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            processed = root / "processed-clips"
            used = processed / "IMG_0001.MOV" / "final.mp4"
            other = processed / "IMG_0002.MOV" / "final.mp4"
            for path in (used, other):
                path.parent.mkdir(parents=True)
                path.write_bytes(b"video")
            timeline = root / "timeline.json"
            timeline.write_text(json.dumps({"tracks": [
                {"kind": "video", "clips": [{"source": "IMG_0001.MOV"}]}]}),
                encoding="utf-8")
            picked = restoration.timeline_sources(timeline, [used, other])
        self.assertEqual(picked, [used])

    def test_delivery_verification_rejects_a_no_op_render(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "source.mp4"
            output = root / "output.mp4"
            make_video(source, size="320x180", duration=1)
            upscale.run_lanczos(source, output, (640, 360), 0.0, 1.0, False,
                                "30/1", None, encoder="libx265")
            result = restoration.verify_delivery(
                source, output, (640, 360), 0.0, 1.0, "lanczos", None, None,
                2, 256, None, None, None, root / "work", encoder="libx265")
            self.assertTrue(Path(result["reference"]).is_file())
        self.assertEqual(result["status"], "review")
        self.assertIn(result["decision"]["decision"],
                      {"SKIP", "REVIEW", "UNSUPPORTED"})
        self.assertIn("min_detail_gain", result["criteria"])

    def test_timeline_ranges_merge_adjacent_usage(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            processed = root / "processed-clips"
            used = processed / "IMG_0001.MOV" / "final.mp4"
            other = processed / "IMG_0002.MOV" / "final.mp4"
            for path in (used, other):
                path.parent.mkdir(parents=True)
                path.write_bytes(b"video")
            timeline = root / "timeline.json"
            timeline.write_text(json.dumps({"source_root": str(processed), "tracks": [
                {"kind": "video", "clips": [
                    {"id": "v0", "source": "IMG_0001.MOV", "source_in": 0.0, "source_out": 2.0},
                    {"id": "v1", "source": "IMG_0001.MOV", "source_in": 2.02, "source_out": 4.0},
                    {"id": "v2", "source": "IMG_0002.MOV", "source_in": 1.0, "source_out": 3.0},
                ]}]}), encoding="utf-8")
            entries = restoration.timeline_ranges(timeline, [used, other])
        self.assertEqual(len(entries), 2)
        first = next(item for item in entries if item["source"] == used)
        self.assertEqual(first["ranges"], [(0.0, 4.0)])
        self.assertEqual(first["clip_ids"], ["v0", "v1"])

    def test_write_timeline_map_points_at_assets(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            processed = root / "processed-clips"
            source = processed / "IMG_0001.MOV" / "final.mp4"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"video")
            asset = source.parent / "upscaled" / "range-0.mp4"
            asset.parent.mkdir()
            asset.write_bytes(b"upscaled")
            timeline = root / "timeline.json"
            timeline.write_text(json.dumps({"source_root": str(processed), "tracks": [
                {"kind": "video", "clips": [
                    {"id": "v0", "source": "IMG_0001.MOV",
                     "source_in": 1.0, "source_out": 3.0}]}]}), encoding="utf-8")
            out = root / "timeline-upscaled.json"
            updated = restoration.write_timeline_map(timeline, [{
                "source": str(source), "start": 1.0, "end": 3.0,
                "asset": str(asset), "model": "realesr-general-x4v3",
                "backend": "pytorch", "denoise_strength": 0.5}], out)
            data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(updated, 1)
        clip = data["tracks"][0]["clips"][0]
        self.assertEqual(clip["source"], "IMG_0001.MOV/upscaled/range-0.mp4")
        self.assertEqual(clip["enhancements"][0]["stage"], "upscale")
        self.assertEqual(clip["enhancements"][0]["review_status"], "approved")

    def test_batch_report_links_the_preview(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            preview_path = root / "clip" / "preview.html"
            preview_path.parent.mkdir()
            preview_path.write_text("preview", encoding="utf-8")
            summary = {"upscaled": 1, "review_pending": 0, "unsupported": 0, "clips": [
                {"source": "clip.mp4", "status": "upscaled", "decision": "FIX",
                 "reasons": ["detail_gain_without_artifacts"],
                 "preview": str(preview_path)}]}
            report = root / "upscale-review.html"
            restoration.write_batch_report(summary, report)
            html = report.read_text(encoding="utf-8")
        self.assertIn("clip/preview.html", html)
        self.assertIn("detail_gain_without_artifacts", html)


if __name__ == "__main__":
    unittest.main()
