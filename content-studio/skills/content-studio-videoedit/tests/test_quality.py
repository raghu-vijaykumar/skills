import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import quality


class QualityTest(unittest.TestCase):
    def make_video(self, path):
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)],
            check=True, capture_output=True)

    def test_identical_video_scores_high(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "source.mp4"
            self.make_video(source)
            result = quality.measure(source, source)
            self.assertGreater(result["ssim"], 0.99)
            self.assertGreater(result["psnr_db"], 30)
            self.assertTrue(result["vmaf"] is None or result["vmaf"] > 90)


if __name__ == "__main__":
    unittest.main()
