"""Exercise rubric coverage, scope changes, and prior-cut comparisons."""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from score_artifacts import ARTIFACT_AXES, summarize


class ArtifactScoreTests(unittest.TestCase):
    def setUp(self):
        self.script = {
            "id": "script", "kind": "script", "state": "scored", "evidence": "script v1, beats 1–20",
            "ratings": {axis: {"score": 4, "observation": "00:04, reviewed"} for axis in ARTIFACT_AXES["script"]},
            "retest": "Read the revised opening and check that beat 20 delivers the promise.",
        }
        self.audio = {"id": "mix", "kind": "audio", "state": "not_generated", "reason": "Silent proof"}
        self.ledger = {"scope": "Assembly proof", "audience": "High school", "artifacts": [self.script, self.audio]}

    def test_missing_audio_counts_as_unscored(self):
        report = summarize(self.ledger)
        self.assertEqual(report["counts"]["not_generated"], 1)
        self.assertNotIn("average", report["artifacts"][1])
        self.audio["ratings"] = {}
        with self.assertRaisesRegex(ValueError, "no ratings"):
            summarize(self.ledger)

    def test_rehooks_and_variety_are_independent(self):
        self.script["ratings"]["hook"]["score"] = 5
        self.script["ratings"]["rehooks"]["score"] = 2
        self.script["ratings"]["variety"]["score"] = 2
        row = summarize(self.ledger)["artifacts"][0]
        self.assertEqual(row["status"], "revise")
        self.assertEqual(row["below_floor"], ["rehooks", "variety"])

    def test_require_complete_axis_set(self):
        del self.script["ratings"]["payoff"]
        with self.assertRaisesRegex(ValueError, "each axis"):
            summarize(self.ledger)

    def test_compare_same_scope_and_kind(self):
        before = summarize(copy.deepcopy(self.ledger))
        self.script["ratings"]["payoff"]["score"] = 5
        self.assertEqual(summarize(self.ledger, before)["artifacts"][0]["axis_change"]["payoff"], 1)
        self.ledger["scope"] = "Final master"
        with self.assertRaisesRegex(ValueError, "scope stable"):
            summarize(self.ledger, before)
