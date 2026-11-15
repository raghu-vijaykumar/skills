import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PLAN = Path(__file__).resolve().parents[1] / "scripts" / "plan.py"
spec = importlib.util.spec_from_file_location("video_idea_plan", PLAN)
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


class DraftIdTest(unittest.TestCase):
    def test_neutral_idea_writes_truthful_landscape_brief_and_scaffolds(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            (root / "videogen.config.ts").write_text("export default {videosDir: 'videos'};\n", encoding="utf-8")
            binary = root / "node_modules" / ".bin" / ("videogen.cmd" if sys.platform == "win32" else "videogen")
            binary.parent.mkdir(parents=True)
            binary.touch()
            calls = []

            def fake_run(argv, **kwargs):
                calls.append(argv)
                return type("Result", (), {"stdout": "videos\n"})()

            with patch.object(sys, "argv", [str(PLAN), "--project-root", str(root), "--name", "Why pages stay stale",
                                            "--kind", "long", "--promise", "Understand cache layers"]), \
                    patch.object(plan.subprocess, "run", side_effect=fake_run):
                self.assertEqual(plan.main(), 0)
            draft = root / "videos" / "why-pages-stay-stale"
            brief = (draft / "brief.md").read_text(encoding="utf-8")
            self.assertIn("Understand cache layers", brief)
            self.assertNotIn("CTR", brief)
            self.assertIn("No channel analytics were supplied", (draft / "research.md").read_text(encoding="utf-8"))
            self.assertEqual(calls[1][-6:], ["--duration", "300", "--width", "1920", "--height", "1080"])

    def test_neutral_project_uses_configured_video_directory(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            (root / "videogen.config.ts").write_text("export default {videosDir: 'drafts'};\n", encoding="utf-8")
            self.assertEqual(plan.project_videos_dir(root), root / "drafts")
    def test_long_revise_labs_scaffold_is_landscape(self):
        self.assertEqual(plan.video_scaffold_args("long", "revise-labs"),
                         ["--duration", "300", "--width", "1920", "--height", "1080"])
        self.assertEqual(plan.video_scaffold_args("short", "revise-labs"), [])
        self.assertEqual(plan.video_scaffold_args("long", "neutral"),
                         ["--duration", "300", "--width", "1920", "--height", "1080"])

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
