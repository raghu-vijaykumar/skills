"""Keep appearance and motion deficits visible through revisions."""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from score_objects import assess, retest_checklist, summarize


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

    def test_retest_checklist_prioritizes_gaps_and_keeps_regressions(self):
        light = self.row() | {"id": "light"}
        light["candidate"]["motion"]["timing"] = 3
        large = self.row() | {"id": "rack", "film": "Study", "shot": "load", "actor": "Rack"}
        large["candidate"]["appearance"]["material"] = 1
        large["candidate"]["motion"]["timing"] = 5
        absent = self.row() | {"id": "missing-card", "candidate": None}
        matched = self.row() | {"id": "complete-phone"}
        result = summarize({"objects": [light, large, absent, matched]},
                           summarize({"objects": [self.row() | {"id": "light"}]}))
        checklist = retest_checklist(result)
        self.assertEqual(checklist.count("- [ ]"), 3)
        self.assertLess(checklist.index("missing-card"), checklist.index("Study / load / Rack"))
        self.assertLess(checklist.index("Study / load / Rack"), checklist.index("- [ ] light"))
        self.assertIn("material -3", checklist)
        self.assertIn("Lower than the preceding review on timing", checklist)
        self.assertNotIn("complete-phone", checklist)

    def test_single_photo_scores_appearance_and_keeps_motion_open(self):
        row = self.row()
        row["reference"].update(photos=[{"evidence": "front.jpg", "shows": "Profile and contact"}],
                                motion=None, motion_basis={"kind": "unverified"})
        report = summarize({"objects": [row]})
        rated = report["objects"][0]
        self.assertEqual(rated["category_scores"]["appearance"], {"reference": 4.0, "candidate": 4.0})
        self.assertEqual(rated["category_scores"]["motion"], {"reference": None, "candidate": 4.0})
        self.assertNotIn("mechanics", rated["axis_deltas"])
        self.assertEqual(report["counts"]["review"], 1)
        self.assertIn("motion evidence pending", retest_checklist(report))
        row["reference"]["motion"] = row["candidate"]["motion"].copy()
        with self.assertRaisesRegex(ValueError, "cannot supply reference motion scores"):
            assess(row)

    def test_sourced_motion_closes_pending_baseline(self):
        row = self.row()
        row["reference"].update(photos=[{"evidence": "rest.jpg", "shows": "Unpressed"}],
                                motion=None, motion_basis={"kind": "unverified"})
        prior = summarize({"objects": [row]})
        row["reference"].update(motion=row["candidate"]["motion"].copy(), motion_basis={
            "kind": "photo-sequence", "evidence": "ordered views", "states": ["Rest", "Contact"],
        })
        with self.assertRaisesRegex(ValueError, "two distinct"):
            assess(row)
        row["reference"]["photos"].append({"evidence": "pressed.jpg", "shows": "Contact closed"})
        retest = summarize({"objects": [row]}, prior)
        self.assertEqual(retest["objects"][0]["status"], "matched")
        self.assertNotIn("mechanics", retest["objects"][0]["change_since_review"])
        self.assertNotIn("motion evidence pending", retest_checklist(retest))
