import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import polish


class PolishTest(unittest.TestCase):
    def make_video(self, path, color="red"):
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", f"color=c={color}:s=320x180:r=30:d=1",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(path)], check=True, capture_output=True)

    def test_ordered_restoration_filters(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            reference = root / "reference.mp4"
            source = root / "source.mp4"
            output = root / "output.mp4"
            self.make_video(reference, "gray")
            self.make_video(source, "blue")
            args = polish.build_parser().parse_args([
                "--input", str(source), "--output", str(output),
                "--lens-k1", "0.01", "--denoise", "light",
                "--deflicker", "--match-reference", str(reference),
                "--stabilize", "--sharpen", "light"])
            manifest = polish.polish(args)
            self.assertTrue(output.is_file())
            self.assertEqual(manifest["used"]["denoise"], "light")
            self.assertTrue(manifest["used"]["deflicker"])
            self.assertTrue(manifest["used"]["stabilize"])
            self.assertEqual(manifest["used"]["sharpen"], "light")
            self.assertEqual(manifest["output_size"], [320, 180])
            self.assertTrue((root / "polish.json").is_file())

    def test_no_filters_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "source.mp4"
            self.make_video(source)
            args = polish.build_parser().parse_args([
                "--input", str(source), "--output", str(root / "out.mp4"),
                "--denoise", "off", "--sharpen", "off"])
            with self.assertRaisesRegex(polish.PolishError, "no filters"):
                polish.polish(args)


if __name__ == "__main__":
    unittest.main()
