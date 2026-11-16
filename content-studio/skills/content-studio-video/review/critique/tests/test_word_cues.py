"""Check that the word audit catches omitted and simultaneous cues."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_word_cues import inspect_frames, read_plan


class WordCueTests(unittest.TestCase):
    def plan(self):
        return {
            "fps": 30, "durationFrames": 10,
            "shots": [{
                "startFrame": 0, "endFrame": 10, "asset": "button", "emotion": "focused",
                "inventory": "Press to close the contact", "script": "Press it.",
                "words": [
                    {"startFrame": 2, "endFrame": 4, "text": "Press", "actor": "cap", "action": "descend"},
                    {"startFrame": 5, "endFrame": 9, "text": "it.", "actor": "contact", "action": "settle"},
                ],
            }],
        }

    def test_full_coverage(self):
        fps, count, cues = read_plan(self.plan())
        self.assertEqual((fps, count, len(cues)), (30, 10, 2))

    def test_reject_missing_word(self):
        plan = self.plan()
        plan["shots"][0]["words"].pop()
        with self.assertRaisesRegex(ValueError, "spoken words differ"):
            read_plan(plan)

    def test_reject_simultaneous_onsets(self):
        plan = self.plan()
        plan["shots"][0]["words"][1]["startFrame"] = 2
        with self.assertRaisesRegex(ValueError, "simultaneous"):
            read_plan(plan)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs FFmpeg and FFprobe")
    def test_a_single_frame_accent_is_kept(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            video = folder / "pulse.mp4"
            subprocess.run([
                "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=144x256:r=30",
                "-vf", "drawbox=c=white:t=fill:enable='eq(n,2)'", "-frames:v", "10", str(video),
            ], check=True)
            fps, duration, rows = read_plan(self.plan())
            inspect_frames(video, rows, fps, duration, (0, 0, 1, 1), folder)
            self.assertEqual(rows[0]["after"], 2)
            self.assertEqual(rows[0]["region_change_percent"], 100)
