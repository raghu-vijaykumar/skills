import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import upscale

try:
    NCNN_READY = upscale.preferred_backend("realesrgan", None)[0] == "realesrgan"
except upscale.UpscaleError:
    NCNN_READY = False
PYTORCH_READY = (upscale.pytorch_available() and upscale.cuda_available()
                 and upscale.bundled_weights("realesr-general-x4v3") is not None)


class UpscaleTest(unittest.TestCase):
    def make_video(self, path, size="320x180", duration=1):
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=30:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={duration}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(path)], check=True, capture_output=True)

    def test_lanczos_upscale_preserves_audio_and_size(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "input.mp4"
            target = root / "output.mp4"
            self.make_video(source)
            manifest = upscale.upscale(upscale.build_parser().parse_args([
                "--input", str(source), "--output", str(target),
                "--backend", "lanczos", "--scale", "2"]))
            self.assertEqual(manifest["backend"], "lanczos")
            self.assertEqual(manifest["output_size"], [640, 360])
            self.assertEqual(manifest["source_size"], [320, 180])
            data = upscale.probe(target)
            self.assertEqual((data["width"], data["height"]), (640, 360))
            self.assertTrue(data["has_audio"])
            self.assertTrue((target.parent / ".content-studio" / "upscale" /
                             source.stem / "upscale.json").is_file())
            self.assertTrue((target.parent / ".content-studio" / "upscale" /
                             source.stem / "before-after.jpg").is_file())

    def test_draft_dry_run_plans_4k_upscale(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch) / "vlog"
            clip = draft / ".content-studio" / "processed-clips" / "clip"
            clip.mkdir(parents=True)
            source = clip / "final.mp4"
            self.make_video(source)
            args = upscale.build_parser().parse_args([
                "--draft", str(draft), "--target", "4k", "--dry-run"])
            summary = upscale.upscale_draft(args)
            self.assertEqual(summary["clips"][0]["status"], "would_upscale")
            self.assertEqual(summary["clips"][0]["target"], [3840, 2160])
            self.assertTrue((draft / ".content-studio" / "upscale" /
                             "upscale-batch.json").is_file())

    def test_upscale_rejects_same_output_path(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "input.mp4"
            self.make_video(source)
            args = upscale.build_parser().parse_args([
                "--input", str(source), "--output", str(source),
                "--backend", "lanczos", "--scale", "2"])
            with self.assertRaisesRegex(upscale.UpscaleError, "differ"):
                upscale.upscale(args)

    def test_content_forwards_option_flags_to_upscale(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "content.py"
        missing = Path(__file__).parent / "does-not-exist.mp4"
        result = subprocess.run(
            [sys.executable, str(script), "upscale", "--input", str(missing),
             "--output", str(Path(__file__).parent / "unused.mp4"),
             "--backend", "lanczos"],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1)
        self.assertIn("input must be a supported video", result.stderr)
        self.assertNotIn("unrecognized", result.stderr)

    def test_frame_timestamps_and_deltas_cover_the_clip(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            source = Path(scratch) / "input.mp4"
            self.make_video(source)
            stamps = upscale.frame_timestamps(source, 0.0, 1.0)
            deltas = upscale.frame_deltas(stamps, 30.0)
        self.assertGreaterEqual(len(stamps), 25)
        self.assertEqual(len(deltas), len(stamps))
        self.assertAlmostEqual(deltas[0], 1 / 30, delta=0.01)

    def test_lanczos_preserves_variable_frame_timing(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "vfr.mp4"
            target = root / "out.mp4"
            subprocess.run([
                "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=1.0",
                "-vf", "setpts='if(lt(N,15),N/30,0.5+(N-15)/15)/TB'",
                "-fps_mode", "vfr", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(source)], check=True, capture_output=True)
            before = upscale.frame_timestamps(source, 0.0, 2.0)
            upscale.upscale(upscale.build_parser().parse_args([
                "--input", str(source), "--output", str(target),
                "--backend", "lanczos", "--scale", "2"]))
            after = upscale.frame_timestamps(target, 0.0, 2.0)
        self.assertGreaterEqual(len(set(round(b - a, 4) for a, b in zip(before, before[1:]))), 3)
        self.assertLessEqual(abs(len(after) - len(before)), 1)
        self.assertAlmostEqual(after[-1], before[-1], delta=0.08)

    def test_10bit_sdr_keeps_bit_depth_and_color_tags(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "tenbit.mp4"
            target = root / "out.mp4"
            subprocess.run([
                "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=0.6",
                "-c:v", "libx265", "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1",
                "-color_primaries", "bt709", "-color_trc", "bt709",
                "-colorspace", "bt709", "-x265-params", "log-level=error",
                str(source)], check=True, capture_output=True)
            upscale.upscale(upscale.build_parser().parse_args([
                "--input", str(source), "--output", str(target),
                "--backend", "lanczos", "--scale", "2"]))
            info = upscale.probe(target)
        self.assertIn("10", info["pix_fmt"])
        self.assertEqual(info["color_space"], "bt709")

    def test_hdr_needs_an_explicit_decision(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "input.mp4"
            self.make_video(source)
            hdr = upscale.probe(source)
            hdr["color_transfer"] = "arib-std-b67"
            with patch.object(upscale, "probe", return_value=hdr):
                with self.assertRaisesRegex(upscale.UpscaleError, "HDR"):
                    upscale.upscale(upscale.build_parser().parse_args([
                        "--input", str(source), "--output", str(root / "out.mp4"),
                        "--backend", "lanczos", "--scale", "2"]))

    def test_second_render_reuses_the_manifest(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "input.mp4"
            target = root / "output.mp4"
            self.make_video(source)
            args = ["--input", str(source), "--output", str(target),
                    "--backend", "lanczos", "--scale", "2"]
            first = upscale.upscale(upscale.build_parser().parse_args(args))
            second = upscale.upscale(upscale.build_parser().parse_args(args))
        self.assertNotIn("cached", first)
        self.assertTrue(second["cached"])
        self.assertEqual(second["params"], first["params"])

    def test_model_defaults_follow_the_backend(self):
        self.assertEqual(upscale.resolve_model("realesrgan", None, None),
                         "realesrgan-x4plus")
        self.assertEqual(upscale.resolve_model("pytorch", None, None),
                         "realesr-general-x4v3")
        self.assertIsNone(upscale.resolve_model("lanczos", "anything", None))
        with self.assertRaisesRegex(upscale.UpscaleError, "pytorch"):
            upscale.resolve_model("realesrgan", "realesr-general-x4v3", None)

    def test_default_backend_prefers_verified_cuda_weights(self):
        if not PYTORCH_READY:
            self.skipTest("CUDA torch and verified weights are not installed")
        self.assertEqual(upscale.preferred_backend(None, None)[0], "pytorch")

    @unittest.skipUnless(PYTORCH_READY, "CUDA torch and verified weights are not installed")
    def test_pytorch_render_records_device_and_checkpoint(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "input.mp4"
            target = root / "output.mp4"
            self.make_video(source, size="160x90", duration=0.4)
            manifest = upscale.upscale(upscale.build_parser().parse_args([
                "--input", str(source), "--output", str(target),
                "--backend", "pytorch", "--model", "realesr-general-x4v3",
                "--scale", "2"]))
            info = upscale.probe(target)
            self.assertEqual(manifest["backend"], "pytorch")
            self.assertEqual(manifest["timing"]["device"], "cuda")
            self.assertGreater(manifest["timing"]["peak_vram_mb"], 0)
            self.assertTrue(manifest["checkpoint"]["sha256"])
            self.assertEqual(manifest["denoise_strength"], 0.5)
        self.assertEqual((info["width"], info["height"]), (320, 180))
        self.assertTrue(info["has_audio"])

    def test_encode_args_honours_the_encoder_choice(self):
        info = {"pix_fmt": "yuv420p"}
        self.assertIn("hevc_nvenc", upscale.encode_args(info, encoder="nvenc"))
        self.assertIn("libx265", upscale.encode_args(info, encoder="libx265"))
        ten_bit = upscale.encode_args({"pix_fmt": "yuv420p10le"}, encoder="nvenc")
        self.assertIn("p010le", ten_bit)

    def test_frame_deltas_extend_to_the_window_tail(self):
        deltas = upscale.frame_deltas([0.0, 0.5, 1.0], 30.0, tail=0.4)
        self.assertAlmostEqual(sum(deltas), 1.4, places=6)

    def test_chunk_plan_covers_every_frame(self):
        self.assertEqual(upscale.plan_chunks(0, 10), [(0, 0)])
        self.assertEqual(upscale.plan_chunks(25, 0), [(0, 25)])
        self.assertEqual(upscale.plan_chunks(25, 10), [(0, 10), (10, 20), (20, 25)])

    @unittest.skipUnless(NCNN_READY, "ncnn/Vulkan backend not installed")
    def test_ncnn_chunked_render_keeps_frames_and_audio(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "input.mp4"
            target = root / "output.mp4"
            self.make_video(source, size="160x90", duration=0.6)
            manifest = upscale.upscale(upscale.build_parser().parse_args([
                "--input", str(source), "--output", str(target),
                "--backend", "realesrgan", "--model", "realesrgan-x4plus",
                "--scale", "2", "--chunk", "8"]))
            info = upscale.probe(target)
        self.assertEqual(manifest["backend"], "realesrgan")
        self.assertEqual(manifest["model"], "realesrgan-x4plus")
        self.assertEqual((info["width"], info["height"]), (320, 180))
        self.assertTrue(info["has_audio"])
        self.assertGreaterEqual(manifest["timing"]["frames"], 15)
        self.assertGreaterEqual(manifest["timing"]["chunks"], 2)
        self.assertIn(manifest["timing"]["timing"], {"vfr", "uniform_fallback"})


if __name__ == "__main__":
    unittest.main()
