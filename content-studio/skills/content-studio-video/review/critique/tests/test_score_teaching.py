"""Verify that editorial quality and learner evidence have separate outcomes."""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from score_teaching import CHECKS, FLOORS, summarize


class TeachingScoreTests(unittest.TestCase):
    def setUp(self):
        self.ledger = {
            "audience": "High school",
            "render": "study.mp4 with recorded SHA-256",
            "beats": [{
                "id": "vertex",
                "objective": "Translate one point into world space",
                "evidence": "00:02–00:05, fixed-camera sequence",
                "axes": {axis: {"score": 4, "observation": "Matched to visible action"} for axis in FLOORS},
                "blockers": [],
                "checks": {check: {"question": check, "expected": "Describe the visible change"} for check in CHECKS},
                "retest": "Hold the world-space coordinates for two seconds.",
            }],
        }
        self.row = self.ledger["beats"][0]

    def test_high_scores_do_not_claim_student_comprehension(self):
        row = summarize(self.ledger)["beats"][0]
        self.assertEqual(row["editorial"], "ready_for_review")
        self.assertEqual(row["comprehension"], "not_tested")

    def test_factual_deficit_requires_revision_with_high_average(self):
        self.row["axes"]["accuracy"]["score"] = 3
        row = summarize(self.ledger)["beats"][0]
        self.assertEqual(row["editorial"], "revise")
        self.assertEqual(row["below_floor"], ["accuracy"])

    def test_blocker_cannot_be_averaged_away(self):
        self.row["blockers"] = ["Direction marker is reversed"]
        self.assertEqual(summarize(self.ledger)["beats"][0]["editorial"], "revise")

    def test_learner_result_requires_observation_and_complete_checks(self):
        self.row["checks"]["identify"]["learner_result"] = {"met": True}
        with self.assertRaisesRegex(ValueError, "observation"):
            summarize(self.ledger)
        self.row["checks"]["identify"]["learner_result"]["evidence"] = "Student identified the origin."
        self.assertEqual(summarize(self.ledger)["beats"][0]["comprehension"], "partial")
        for check in CHECKS:
            self.row["checks"][check]["learner_result"] = {"met": True, "evidence": "Observed response"}
        self.assertEqual(summarize(self.ledger)["beats"][0]["comprehension"], "demonstrated")
        self.row["checks"]["predict"]["learner_result"]["met"] = False
        self.assertEqual(summarize(self.ledger)["beats"][0]["editorial"], "revise")

    def test_retest_preserves_questions_and_reports_per_axis_change(self):
        before = summarize(copy.deepcopy(self.ledger))
        self.row["axes"]["motion_readability"]["score"] = 5
        self.assertEqual(summarize(self.ledger, before)["beats"][0]["axis_change"]["motion_readability"], 1)
        self.row["checks"]["explain"]["question"] = "A different question"
        with self.assertRaisesRegex(ValueError, "changed teaching objective"):
            summarize(self.ledger, before)
