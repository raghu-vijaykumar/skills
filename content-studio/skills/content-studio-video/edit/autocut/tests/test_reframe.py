import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import reframe


class ReframeTests(unittest.TestCase):
    def make_video(self, path):
        subprocess.run(
            ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", "color=c=black:s=640x360:r=30:d=2",
             "-vf", "drawbox=x=470:y=90:w=120:h=180:color=white:t=fill",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)],
            check=True, capture_output=True)

    def test_crop_shape_for_portrait_and_landscape_targets(self):
        width, height = reframe.crop_shape(1920, 1080, 1080, 1920)
        self.assertAlmostEqual(width, 0.316406, places=5)
        self.assertEqual(height, 1.0)
        width, height = reframe.crop_shape(1080, 1920, 1920, 1080)
        self.assertEqual(width, 1.0)
        self.assertAlmostEqual(height, 0.316406, places=5)

    def test_saliency_finds_right_side_subject_and_writes_preview(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "right.mp4"
            self.make_video(source)
            record = reframe.analyze_segment(source, 0, 2, (1080, 1920),
                                             mode="saliency")
            self.assertEqual(record["mode"], "saliency")
            self.assertGreater(record["crop"]["x"], 0.5)
            self.assertGreater(record["confidence"], 0.2)
            preview = reframe.write_preview(source, record, root / "preview")
            self.assertTrue(preview.is_file())
            self.assertTrue((root / "preview" / "preview" / "cropped-00.jpg").is_file())

    def test_subject_box_overrides_saliency_and_accepts_bom(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "right.mp4"
            self.make_video(source)
            subjects = root / "subjects.json"
            subjects.write_text(json.dumps({"subjects": [{
                "source": "right.mp4", "start": 0, "end": 2,
                "box": {"x": 0.1, "y": 0.3, "w": 0.2, "h": 0.4},
                "confidence": 0.95, "label": "person"}]}), encoding="utf-8-sig")
            record = reframe.analyze_segment(source, 0, 2, (1080, 1920),
                                             mode="auto", subjects_path=subjects)
            self.assertEqual(record["mode"], "subjects")
            self.assertLess(record["crop"]["x"], 0.2)
            self.assertAlmostEqual(record["confidence"], 0.95)

    def test_center_mode_is_predictable(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "right.mp4"
            self.make_video(source)
            record = reframe.analyze_segment(source, 0, 2, (1080, 1920),
                                             mode="center")
            self.assertEqual(record["mode"], "center")
            self.assertAlmostEqual(record["crop"]["x"], (1 - record["crop"]["w"]) / 2, places=5)


if __name__ == "__main__":
    unittest.main()
