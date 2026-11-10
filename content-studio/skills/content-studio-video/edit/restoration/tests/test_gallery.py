"""Check the committed visual evidence for each restoration method."""

import statistics
import unittest
from pathlib import Path

from PIL import Image, ImageStat


SKILL = Path(__file__).resolve().parents[1]


class GalleryTests(unittest.TestCase):
    def test_each_visual_method_has_its_own_before_after(self):
        readme = (SKILL / "README.md").read_text(encoding="utf-8")
        for method in ("denoise-light", "denoise-medium", "denoise-nlmeans",
                       "lens", "sharpen-light", "sharpen-medium"):
            path = SKILL / "previews" / f"{method}.png"
            self.assertIn(f"![", readme)
            self.assertIn(f"(previews/{method}.png)", readme)
            with Image.open(path) as image:
                self.assertEqual(image.size, (640, 205))
                # A visual comparison must include two different rendered panels.
                left = image.crop((0, 0, 320, 180)).tobytes()
                right = image.crop((320, 0, 640, 180)).tobytes()
                self.assertNotEqual(left, right, method)

    def test_deflicker_example_reduces_temporal_luma_variation(self):
        path = SKILL / "previews" / "deflicker.gif"
        before, after = [], []
        with Image.open(path) as gif:
            self.assertEqual(gif.size, (480, 135))
            self.assertGreaterEqual(gif.n_frames, 16)
            for index in range(gif.n_frames):
                gif.seek(index)
                frame = gif.convert("L")
                before.append(ImageStat.Stat(frame.crop((0, 0, 240, 135))).mean[0])
                after.append(ImageStat.Stat(frame.crop((240, 0, 480, 135))).mean[0])
        self.assertLess(statistics.pstdev(after), statistics.pstdev(before))


if __name__ == "__main__":
    unittest.main()
