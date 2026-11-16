"""Keep appearance and motion deficits visible through revisions."""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from score_objects import assess, summarize


class ObjectScoreTests(unittest.TestCase):
    def row(self):
        grade = {"evidence": "paired/coin.jpg#09.2s", "observation": "Readable rim and support",
                 "appearance": {"form": 4, "material": 4, "staging": 4},
                 "motion": {"mechanics": 4, "timing": 4, "continuity": 4}}
        return {"id": "coin", "reference": grade, "candidate": copy.deepcopy(grade),
                "revision": "Render a textured raised rim and inspect the turn."}

    def test_high_motion_does_not_cancel_a_surface_deficit(self):
        row = self.row()
        row["candidate"]["appearance"]["material"] = 2
        row["candidate"]["motion"]["timing"] = 5
        verdict = assess(row)
        self.assertEqual(verdict["status"], "improve")
        self.assertEqual(verdict["deficits"], ["material"])
        self.assertEqual(verdict["category_scores"]["motion"]["candidate"], 4.33)

    def test_retest_reports_improvement_against_fixed_reference(self):
        row = self.row()
        row["candidate"]["appearance"]["material"] = 3
        prior = summarize({"objects": [row]})
        result = summarize({"objects": [self.row()]}, prior)
        self.assertEqual(result["objects"][0]["change_since_review"]["material"], 1)
        self.assertEqual(result["counts"]["matched"], 1)

    def test_missing_object_needs_revision(self):
        row = self.row()
        row["candidate"] = None
        self.assertEqual(assess(row)["status"], "missing")
        del row["revision"]
        with self.assertRaisesRegex(ValueError, "concrete revision"):
            assess(row)
