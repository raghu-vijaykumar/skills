import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location("lifecycle", Path(__file__).resolve().parents[1] / "scripts" / "lifecycle.py")
lifecycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lifecycle)


class LifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = Path(self.temp.name)
        self.archive = self.root / "shorts" / "2026-10-26 - Example [abcdefghijk]"
        self.archive.mkdir(parents=True)
        (self.archive / "video.mp4").write_bytes(b"youtube-transcode")
        (self.archive / "thumbnail.jpg").write_bytes(b"public-thumbnail")
        (self.archive / "metadata.json").write_text(json.dumps({
            "id": "abcdefghijk", "title": "Published title", "description": "Exact public description",
            "availability": "public"}), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_public_backup_copies_source_and_preserves_youtube_bytes(self):
        draft = self.root / "drafts" / "001-example"
        draft.mkdir(parents=True)
        (draft / "draft.json").write_text('{"youtubeId":"abcdefghijk"}', encoding="utf-8")
        (draft / "video.mp4").write_bytes(b"original-master")
        (draft / "video.tsx").write_text("export const Video = () => null;", encoding="utf-8")
        (draft / "title.txt").write_text("old title", encoding="utf-8")
        changed, handoffs = lifecycle.reconcile(self.root, lambda message: None)
        self.assertEqual(changed, [self.archive])
        self.assertEqual(handoffs, [(draft, self.archive)])
        self.assertEqual((self.archive / "video.mp4").read_bytes(), b"youtube-transcode")
        self.assertEqual((self.archive / "title.txt").read_text(encoding="utf-8"), "Published title\n")
        self.assertEqual((self.archive / "description.txt").read_text(encoding="utf-8"), "Exact public description\n")
        self.assertTrue((self.archive / "video.tsx").is_file())
        self.assertTrue(draft.exists())

    def test_private_backup_does_not_close_draft(self):
        info = json.loads((self.archive / "metadata.json").read_text(encoding="utf-8"))
        info["availability"] = "private"
        (self.archive / "metadata.json").write_text(json.dumps(info), encoding="utf-8")
        draft = self.root / "drafts" / "001-example"
        draft.mkdir(parents=True)
        (draft / "draft.json").write_text('{"youtubeId":"abcdefghijk"}', encoding="utf-8")
        _, handoffs = lifecycle.reconcile(self.root, lambda message: None)
        self.assertEqual(handoffs, [])
        self.assertTrue(draft.exists())

    def test_duplicate_youtube_id_is_rejected(self):
        for name in ("one", "two"):
            draft = self.root / "drafts" / name
            draft.mkdir(parents=True)
            (draft / "draft.json").write_text('{"youtubeId":"abcdefghijk"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "multiple drafts"):
            lifecycle.reconcile(self.root, lambda message: None)


if __name__ == "__main__":
    unittest.main()
