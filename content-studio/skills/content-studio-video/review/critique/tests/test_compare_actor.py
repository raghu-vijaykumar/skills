"""Check actor bounds and paired evidence on a decoded frame."""

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare import run
from compare_actor import build, parse_box


class ActorComparisonTests(unittest.TestCase):
    def test_rejects_off_canvas_and_subpixel_boxes(self):
        for box in ([0, 0, 1.01, 1], [.1, .4, .1, .6], [.1, .2, .10001, .4]):
            with self.subTest(box=box), self.assertRaises(ValueError):
                parse_box(box, 100, 100)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs FFmpeg and FFprobe")
    def test_preserves_per_clip_actor_fraction_and_produces_sheet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "object.mp4"
            run("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=160x240:rate=30",
                "-frames:v", "6", "-c:v", "libx264", str(video))
            output = root / "review"
            mapping = {"actors": [{"id": "prop",
                                   "reference": {"seconds": 0, "box": [.1, .2, .9, .7]},
                                   "candidate": {"seconds": .1, "box": [.25, .2, .75, .6]}}]}
            self.assertEqual(build(video, video, mapping, output), 1)
            row = json.loads((output / "evidence.json").read_text())["actors"][0]
            self.assertEqual(row["reference"]["frame_fraction"], [.8, .5])
            self.assertEqual(row["candidate"]["frame_fraction"], [.5, .4])
            with Image.open(output / row["sheet"]) as sheet:
                self.assertEqual(sheet.size, (1280, 824))

            photo = root / "portrait.jpg"
            im = Image.new("RGB", (240, 160), "orange")
            exif = im.getexif()
            exif[274] = 6  # A portrait photo stored sideways.
            im.save(photo, exif=exif)
            mapping["actors"][0]["reference"].pop("seconds")
            photo_output = root / "photo-review"
            self.assertEqual(build(photo, video, mapping, photo_output, reference_photo=True), 1)
            evidence = json.loads((photo_output / "evidence.json").read_text())
            ref = evidence["reference"]
            self.assertEqual((ref["kind"], ref["width"], ref["height"]), ("photo", 160, 240))
            self.assertEqual(evidence["actors"][0]["reference"]["box_pixels"], [16, 48, 144, 168])
            self.assertNotIn("requested_seconds", evidence["actors"][0]["reference"])
