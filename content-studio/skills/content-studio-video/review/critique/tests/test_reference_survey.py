"""Exercise source-only inventory generation with a real hard cut."""

from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare import run
from survey_reference import build


class ReferenceSurveyTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs FFmpeg and FFprobe")
    def test_windows_cover_both_sides_of_a_cut(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref = root / "source.mp4"
            run("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=144x256:r=24:d=1",
                "-f", "lavfi", "-i", "color=white:s=144x256:r=24:d=1",
                "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0", str(ref))
            out = root / "inventory"
            rows = build(ref, out, {"full": (0, 0, 1, 1)}, 8, 0.22)
            self.assertEqual([row["reference"] for row in rows], [(0, 1), (1, 2)])
            self.assertTrue(all((out / row["sheet"]).is_file() for row in rows))
            self.assertEqual(rows[1]["observations"]["actors"], [])
