import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

PLAN = Path(__file__).resolve().parents[1] / "scripts" / "plan.py"
spec = importlib.util.spec_from_file_location("video_idea_plan", PLAN)
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


class DraftIdTest(unittest.TestCase):
    def test_revise_labs_allocates_next_id_from_drafts_and_archives(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            (root / "drafts" / "00075-draft").mkdir(parents=True)
            archive = root / "shorts" / "public-backup"
            archive.mkdir(parents=True)
            (archive / "source-provenance.json").write_text(
                json.dumps({"sourceId": "00076-existing"}), encoding="utf-8")
            self.assertEqual(plan.draft_id(root, "revise-labs", "Why Caches Miss?"),
                             "00077-why-caches-miss")

    def test_non_numeric_channels_and_empty_roots(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            self.assertEqual(plan.draft_id(root, "revise-labs", "New Video"), "00001-new-video")
            self.assertEqual(plan.draft_id(root, "out-of-office", "A New Trip!"), "a-new-trip")


if __name__ == "__main__":
    unittest.main()
