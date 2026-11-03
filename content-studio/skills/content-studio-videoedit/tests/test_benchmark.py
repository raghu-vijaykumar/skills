import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import benchmark


class BenchmarkTest(unittest.TestCase):
    def make_video(self, path, color):
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", f"color=c={color}:s=320x180:r=30:d=1",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(path)], check=True, capture_output=True)

    def test_five_panel_native_stacked_grid(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            colors = ["red", "green", "blue", "yellow", "white"]
            panels = [root / f"p{index}.mp4" for index in range(1, 6)]
            for panel, color in zip(panels, colors):
                self.make_video(panel, color)
            output = root / "grid.mp4"
            args = benchmark.build_parser().parse_args([
                "--original", str(panels[0]), "--preprocessed", str(panels[1]),
                "--upscaled", str(panels[2]), "--color", str(panels[3]),
                "--color-warm", str(panels[4]), "--output", str(output),
                "--width", "640"])
            manifest = benchmark.build(args)
            self.assertEqual(manifest["output_size"], [640, 1260])
            self.assertEqual(len(manifest["panels"]), 5)
            self.assertEqual(manifest["panels"][0]["size"], [320, 180])
            self.assertEqual(manifest["panels"][2]["size"], [640, 360])
            self.assertTrue(output.is_file())
            self.assertTrue((root / "benchmark.json").is_file())

    def test_duration_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            panels = [root / f"p{index}.mp4" for index in range(1, 5)]
            for panel in panels:
                self.make_video(panel, "red")
            subprocess.run([
                "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "color=c=red:s=320x180:r=30:d=2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(panels[3])],
                check=True, capture_output=True)
            args = benchmark.build_parser().parse_args([
                "--original", str(panels[0]), "--preprocessed", str(panels[1]),
                "--upscaled", str(panels[2]), "--color", str(panels[3]),
                "--output", str(root / "grid.mp4"), "--width", "640"])
            with self.assertRaisesRegex(benchmark.BenchmarkError, "durations differ"):
                benchmark.build(args)


if __name__ == "__main__":
    unittest.main()
