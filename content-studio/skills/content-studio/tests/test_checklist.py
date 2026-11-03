import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import checklist


class LifecycleChecklistTest(unittest.TestCase):
    def test_init_sets_main_lifecycle_and_post_publish_defaults(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch) / "001-test"
            draft.mkdir()
            data, created = checklist.init_checklist(draft, "sample", "edited")
            self.assertTrue(created)
            self.assertEqual(data["kind"], "edited")
            self.assertEqual(len(data["items"]), len(checklist.ITEMS))
            manifest = json.loads((draft / "draft.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["lifecycle"], "main")
            self.assertEqual(manifest["production"]["kind"], "edited")
            by_id = {item["id"]: item for item in data["items"]}
            self.assertEqual(by_id["C04"]["status"], "pending")
            self.assertEqual(by_id["C18"]["status"], "deferred")
            self.assertEqual(by_id["C18"]["reason"], "post-publish gate")

            again, created_again = checklist.init_checklist(draft, "sample", "edited")
            self.assertFalse(created_again)
            self.assertEqual(again["items"][0]["status"], by_id["C01"]["status"])

    def test_remotion_defaults_skip_camera_steps_with_reasons(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch) / "001-test"
            draft.mkdir()
            data, _ = checklist.init_checklist(draft, "sample", "remotion")
            by_id = {item["id"]: item for item in data["items"]}
            for item_id in ("C04", "C05", "C09", "C10"):
                self.assertEqual(by_id[item_id]["status"], "not_applicable")
                self.assertIn("Remotion", by_id[item_id]["reason"])

    def test_done_requires_evidence_and_not_applicable_requires_reason(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch) / "001-test"
            draft.mkdir()
            checklist.init_checklist(draft, "sample", "edited")
            with self.assertRaises(SystemExit):
                checklist.update_item(draft, "C01", "done")
            item = checklist.update_item(draft, "C01", "done", evidence=["channel.md"])
            self.assertEqual(item["status"], "done")
            self.assertEqual(item["evidence"], ["channel.md"])
            with self.assertRaises(SystemExit):
                checklist.update_item(draft, "C03", "not_applicable")
            item = checklist.update_item(draft, "C03", "not_applicable",
                                          reason="supplied edit already has an approved outline")
            self.assertEqual(item["status"], "not_applicable")

    def test_verify_pre_publish_ignores_post_items_then_all_requires_closure(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch) / "001-test"
            draft.mkdir()
            data, _ = checklist.init_checklist(draft, "sample", "edited")
            self.assertTrue(checklist.verify_checklist(data, "pre_publish"))

            for item_id, _, _, phase, _, _ in checklist.ITEMS:
                if phase == "pre_publish":
                    checklist.update_item(draft, item_id, "done", note="reviewed")
            data = checklist.load_checklist(draft)
            self.assertEqual(checklist.verify_checklist(data, "pre_publish"), [])
            self.assertTrue(checklist.verify_checklist(data, "all"))

            for item_id, _, _, phase, _, _ in checklist.ITEMS:
                if phase == "post_publish":
                    checklist.update_item(draft, item_id, "done", evidence=["receipt"])
            data = checklist.load_checklist(draft)
            self.assertEqual(checklist.verify_checklist(data, "all"), [])


if __name__ == "__main__":
    unittest.main()
