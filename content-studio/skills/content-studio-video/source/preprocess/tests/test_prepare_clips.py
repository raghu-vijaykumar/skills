"""Verify the raw-folder default stops at an individual-clip handoff."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_clips.py"


class PrepareClipsTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg unavailable")
    def test_raw_folder_handoff_does_not_join_or_autocut(self):
        with tempfile.TemporaryDirectory() as scratch:
            folder = Path(scratch)
            for index, color in enumerate(("red", "blue"), start=1):
                source = folder / f"camera-{index}.mp4"
                made = subprocess.run([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                    "-i", f"color=c={color}:s=320x180:r=10", "-f", "lavfi",
                    "-i", "anullsrc=channel_layout=stereo:sample_rate=48000", "-t", "1",
                    "-c:v", "mpeg4", "-c:a", "aac", "-shortest", str(source)],
                    capture_output=True, text=True)
                self.assertEqual(made.returncode, 0, made.stderr[-400:])
            # Synthetic media is safe to process without a production approval.
            result = subprocess.run([sys.executable, str(SCRIPT), "--folder", str(folder),
                                     "--utc-offset", "+00:00", "--denoise", "off",
                                     "--speech-gain", "off", "--no-auto-tune"],
                                    capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-1400:])
            self.assertEqual(len(list((folder / "original").glob("*.mp4"))), 2)
            self.assertTrue((folder / ".content-studio" / "_timeline.csv").is_file())
            processed = list((folder / ".content-studio" / "processed-clips").rglob("processed.*"))
            self.assertEqual(len([item for item in processed if item.suffix in {".mp4", ".mov"}]), 2)
            self.assertFalse(list(folder.glob("*-preprocessed.mp4")))
            self.assertFalse(list(folder.glob("*-rough-cut.mp4")))
            self.assertFalse(list(folder.glob("*-final.mp4")))


if __name__ == "__main__":
    unittest.main()
