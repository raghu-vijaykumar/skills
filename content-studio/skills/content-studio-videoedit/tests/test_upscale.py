import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import upscale


class UpscaleTest(unittest.TestCase):
    def make_video(self, path):
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=1",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
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


if __name__ == "__main__":
    unittest.main()
