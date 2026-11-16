"""Check that the word audit catches omitted and simultaneous cues."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_word_cues import read_plan


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
