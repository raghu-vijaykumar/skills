"""Check that the word audit catches omitted and simultaneous cues."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_word_cues import changed, cue_signature, inspect_frames, read_plan, read_targets


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

    def test_rapid_take_requires_visible_cue_kinds_and_allows_visual_reskins(self):
        plan = {**self.plan(), "style": "rapid-take"}
        words = plan["shots"][0]["words"]
        words[0]["cueKind"] = "object"
        for invalid in (None, "caption", ["object"]):
            words[1]["cueKind"] = invalid
            with self.assertRaisesRegex(ValueError, "Rapid Take word 'it.' needs a cueKind"):
                read_plan(plan)
        words[1]["cueKind"] = "continuation"
        self.assertEqual(read_plan({**plan, "artPreset": "anime"}),
                         read_plan({**plan, "artPreset": "pixel-art"}))
        words[0]["text"] = "Press it."
        words.pop()
        with self.assertRaisesRegex(ValueError, "one spoken word per Rapid Take cue"):
            read_plan(plan)

    def test_color_accent_can_move_without_changing_luma(self):
        red = Image.new("RGB", (8, 8), (255, 0, 0))
        green = Image.new("RGB", (8, 8), (0, 130, 0))
        self.assertEqual(changed(red, green, (0, 0, 1, 1)), 0)
        self.assertEqual(changed(red, green, (0, 0, 1, 1), color=True), 100)

    def test_preset_signature_preserves_clock_and_actions(self):
        plan = self.plan()
        anime = cue_signature(*read_plan({**plan, "artPreset": "anime"}))
        self.assertEqual(anime, cue_signature(*read_plan({**plan, "artPreset": "pixel-art"})))
        word = plan["shots"][0]["words"][1]
        word["startFrame"] += 1
        self.assertNotEqual(anime, cue_signature(*read_plan(plan)))
        word["startFrame"] -= 1
        word["action"] = "blink"
        self.assertNotEqual(anime, cue_signature(*read_plan(plan)))

    def test_target_regions_are_keyed_to_unique_cue_frames(self):
        _, _, cues = read_plan(self.plan())
        row = {"frame": 2, "region": [.1, .2, .5, .75]}
        self.assertEqual(read_targets({"targets": [row]}, cues), {2: row["region"]})
        for entries in ([row, row], [{**row, "frame": 3}], [{**row, "frame": True}]):
            with self.assertRaisesRegex(ValueError, "unique word onset"):
                read_targets({"targets": entries}, cues)
        with self.assertRaisesRegex(ValueError, "Invalid target region"):
            read_targets({"targets": [{**row, "region": [0, 0, .001, 1]}]}, cues)

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

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs FFmpeg and FFprobe")
    def test_target_evidence_ignores_changes_outside_the_annotated_actor(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            video = folder / "targets.mp4"
            subprocess.run([
                "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=144x256:r=30",
                "-vf", ("drawbox=x=72:w=72:h=256:c=white:t=fill:enable='eq(n,2)+eq(n,5)',"
                        "drawbox=x=0:w=36:h=256:c=white:t=fill:enable='eq(n,3)'"),
                "-frames:v", "10", str(video),
            ], check=True)
            fps, duration, rows = read_plan(self.plan())
            inspect_frames(video, rows, fps, duration, (0, 0, 1, 1), folder,
                           targets={2: [0, 0, .22, 1], 5: [0, 0, .22, 1]})
            self.assertEqual((rows[0]["after"], rows[0]["target_after"]), (2, 3))
            self.assertEqual(rows[0]["target_change_percent"], 100)
            self.assertGreater(rows[1]["region_change_percent"], 40)
            self.assertEqual(rows[1]["target_change_percent"], 0)
            self.assertTrue((folder / "targets-001.jpg").is_file())
