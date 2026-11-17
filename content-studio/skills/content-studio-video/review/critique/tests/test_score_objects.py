"""Keep appearance and motion deficits visible through revisions."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from score_objects import assess, retest_checklist, score_checkpoint, summarize


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

    def test_checkpoint_rejects_aggregate_only_review_and_wrong_render(self):
        ledger = {"objects": [self.row()], "render_sha256": "proof-hash"}
        with self.assertRaisesRegex(ValueError, "Missing inventory reviews: coin.turn"):
            score_checkpoint(ledger, {"ids": ["coin", "coin.turn"]}, "proof", "proof-hash")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            score_checkpoint(ledger, {"ids": ["coin"]}, "master", "different-hash")

    def test_occluded_actor_remains_open_without_a_candidate_grade(self):
        row = self.row() | {"candidate": None, "review_note": "Hand is occluded at contact."}
        ledger = {"objects": [row], "render_sha256": "proof-hash"}
        report = score_checkpoint(ledger, {"ids": ["coin"]}, "proof", "proof-hash")
        self.assertEqual(report["counts"]["review"], 1)
        self.assertFalse(report["checkpoint"]["ready"])
        self.assertEqual(report["objects"][0]["axis_deltas"], {})
        self.assertIn("Hand is occluded at contact.", retest_checklist(report))

    def test_checkpoint_carries_regression_target_through_failed_retries(self):
        row = self.row()
        row["candidate"]["motion"]["timing"] = 5
        proof = score_checkpoint({"objects": [row], "render_sha256": "proof-hash"},
                                 {"ids": ["coin"]}, "proof", "proof-hash")
        current = self.row()
        slow = {"objects": [current], "render_sha256": "master-hash"}
        first_retry = score_checkpoint(slow, {"ids": ["coin"]}, "master", "master-hash", proof)
        repeated = score_checkpoint(slow, {"ids": ["coin"]}, "master", "master-hash", first_retry)
        self.assertEqual(repeated["counts"]["matched"], 1)
        self.assertFalse(repeated["checkpoint"]["ready"])
        self.assertIn("restore timing to 5/5", retest_checklist(repeated))
        current["candidate"]["motion"]["timing"] = 5
        corrected = score_checkpoint(slow, {"ids": ["coin"]}, "master", "master-hash", repeated)
        self.assertTrue(corrected["checkpoint"]["ready"])

    def test_cli_writes_open_report_and_retest_before_exiting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            render = root / "proof.mp4"
            render.write_bytes(b"render bytes for fingerprint validation")
            inventory = root / "inventory.json"
            inventory.write_text(json.dumps({"ids": ["coin"]}), encoding="utf-8")
            ledger = root / "ledger.json"
            ledger.write_text(json.dumps({
                "objects": [self.row() | {"candidate": None}],
                "render_sha256": hashlib.sha256(render.read_bytes()).hexdigest(),
            }), encoding="utf-8")
            report = root / "report.json"
            retests = root / "retests.md"
            script = Path(__file__).resolve().parents[1] / "scripts" / "score_objects.py"
            result = subprocess.run([sys.executable, str(script), "--checkpoint", "proof",
                                     "--inventory", str(inventory), "--render", str(render),
                                     "--ledger", str(ledger), "--out", str(report), "--retests", str(retests)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["checkpoint"]["open_ids"], ["coin"])
            self.assertIn("coin (missing,", retests.read_text(encoding="utf-8"))
