"""A real FFmpeg mux checks that narration changes audio without re-encoding picture."""

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mix_into_video.py"
SPEC = importlib.util.spec_from_file_location("mix_into_video", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class NarrationMixTests(unittest.TestCase):
    def test_mixed_master_copies_picture_and_records_source_hash(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            video = root / "manual.mp4"
            voice = root / "voice.wav"
            output = root / "voiced.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=blue:s=320x180:r=30:d=1", "-f", "lavfi", "-i",
                            "sine=frequency=220:duration=1", "-c:v", "libx264", "-c:a", "aac",
                            "-shortest", str(video)], check=True, capture_output=True)
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "sine=frequency=440:duration=0.8", str(voice)],
                           check=True, capture_output=True)
            before = MODULE.digest(video)
            result = MODULE.mix(video, voice, output)
            delivered = MODULE.probe(output)
            self.assertEqual(MODULE.digest(video), before)
            self.assertEqual(result["input_sha256"], before)
            self.assertTrue(result["picture_stream_copied"])
            self.assertTrue(any(item["codec_type"] == "audio" for item in delivered["streams"]))
            self.assertTrue(output.with_suffix(".mp4.mix.json").is_file())
            self.assertTrue(json.loads(output.with_suffix(".mp4.mix.json").read_text())["review_required"])
            with self.assertRaisesRegex(ValueError, "new file"):
                MODULE.mix(video, voice, video)


if __name__ == "__main__":
    unittest.main()
