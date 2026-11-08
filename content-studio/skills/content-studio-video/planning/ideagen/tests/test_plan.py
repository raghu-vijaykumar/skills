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
    def test_long_revise_labs_scaffold_is_landscape(self):
        self.assertEqual(plan.video_scaffold_args("long", "revise-labs"),
                         ["--duration", "300", "--width", "1920", "--height", "1080"])
        self.assertEqual(plan.video_scaffold_args("short", "revise-labs"), [])

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


class DigestLeadTest(unittest.TestCase):
    def test_snapshot_leads_are_labeled_unverified(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            path = Path(scratch) / "digest.json"
            path.write_text(json.dumps({"schemaVersion": 1, "generatedAt": "2026-11-01T12:00:00Z",
                "items": [{"title": "A new cache design", "url": "https://example.test/cache",
                           "source": "Engineering Blog", "topic": "systems", "publishedAt": None}]}), encoding="utf-8")
            result = plan.digest_appendix(path)
            self.assertIn("Digest leads (unverified)", result)
            self.assertIn("undated; verify", result)
            self.assertIn("https://example.test/cache", result)

    def test_rejects_unknown_digest_schema(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            path = Path(scratch) / "digest.json"
            path.write_text('{"schemaVersion": 2, "items": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported digest snapshot"):
                plan.digest_appendix(path)


if __name__ == "__main__":
    unittest.main()
