"""Check the Blender-to-videogen handoff against changed media and cue timing."""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "handoff.py"
SPEC = importlib.util.spec_from_file_location("blender_handoff", SCRIPT)
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


class HandoffTests(unittest.TestCase):
    def test_package_pins_hashes_and_places_media_at_narration_cue(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            video, narration, report, out = (root / "shot.mp4", root / "voice.wav",
                                             root / "shot.json", root / "project")
            video.write_bytes(b"reviewed shot")
            narration.write_bytes(b"reviewed narration")
            report.write_text(json.dumps({"video": {"sha256": handoff.digest(video)},
                                          "frames": 96, "fps": 24, "resolution": [1280, 720]}),
                              encoding="utf-8")
            def media_probe(path):
                if path == video:
                    return {"streams": [{"codec_type": "video", "nb_read_frames": "96",
                                         "width": 1280, "height": 720}],
                            "format": {"duration": "4"}}
                return {"streams": [{"codec_type": "audio"}], "format": {"duration": "2"}}
            with patch.object(handoff, "probe", side_effect=media_probe):
                plan = handoff.package(report, video, narration, out, "Screw closes", "cue-screw", 15,
                                       "Original procedural scene", "Owned narration", "recorded")
                self.assertEqual(plan["durationFrames"], 135)
                self.assertEqual(plan["scenes"][0]["visual"],
                                 {"videoId": "shot", "videoStartFrame": 15})
                manifest = json.loads((out / "asset-manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["assets"][0]["sha256"], handoff.digest(video))
                self.assertEqual(manifest["assets"][1]["origin"], "recorded")
                self.assertIn("<Sequence from={15}>", (out / "video.tsx").read_text(encoding="utf-8"))
                with self.assertRaises(FileExistsError):
                    handoff.package(report, video, narration, out, "Screw closes", "cue-screw", 15,
                                    "Original", "Owned")
                video.write_bytes(b"changed shot")
                with self.assertRaisesRegex(ValueError, "differs from its render report"):
                    handoff.package(report, video, narration, root / "changed", "Screw closes",
                                    "cue-screw", 0, "Original", "Owned")


if __name__ == "__main__":
    unittest.main()
