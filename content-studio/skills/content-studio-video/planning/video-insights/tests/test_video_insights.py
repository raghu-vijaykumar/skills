import contextlib
import importlib.util
import io
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "video_insights.py"
SPEC = importlib.util.spec_from_file_location("published_video_insights", SCRIPT)
insights = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(insights)


class VideoInsightsTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.workspace = Path(self.scratch.name)
        self.root = self.workspace / "sample"
        self.root.mkdir()
        self.config = self.workspace / "config.json"
        self.config.write_text(json.dumps({"workspace": str(self.workspace), "channels": {
            "sample": {"name": "Sample channel", "channelId": "UC123"}}}), encoding="utf-8")
        self.video_id = "ABCdef12345"
        self.folder = self.root / "long" / f"2026-11-01 - Good Story [{self.video_id}]"
        self.folder.mkdir(parents=True)
        (self.folder / "metadata.json").write_text(json.dumps({
            "id": self.video_id, "title": "Good Story", "upload_date": "20261101",
            "availability": "public", "duration": 120}), encoding="utf-8")
        self.store = self.root / "analytics"
        (self.store / self.video_id).mkdir(parents=True)
        (self.store / self.video_id / "metrics.json").write_text(json.dumps({
            "source": "api", "metrics": {"views": 125, "averageViewPercentage": 57}}), encoding="utf-8")
        (self.store / "insights.json").write_text(json.dumps({
            "generated": "2026-11-19 12:00:00", "videos": [{"id": self.video_id, "ctr": None, "vtr": None}]}), encoding="utf-8")

    def run_main(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = insights.main([*args, "--channel", "sample", "--config", str(self.config)])
        return code, json.loads(output.getvalue())

    def test_prepare_preserves_agent_notes_and_pruned_identity(self):
        code, report = self.run_main("prepare")
        self.assertEqual(code, 0)
        self.assertEqual(report["published_videos"], 1)
        channel = self.store / "video-insights.md"
        per_video = self.store / self.video_id / "video-insights.md"
        authored = "Observed 00:11: the explanation has a long pause. Evidence: reviewed clip.\n"
        per_video.write_text(per_video.read_text(encoding="utf-8") + authored, encoding="utf-8")
        (self.store / self.video_id / "metrics.json").write_text(json.dumps({
            "metrics": {"views": 200, "averageViewPercentage": 57}}), encoding="utf-8")
        (self.folder / "metadata.json").unlink()
        self.run_main("prepare")
        updated = per_video.read_text(encoding="utf-8")
        self.assertIn("Views: 200", updated)
        self.assertTrue(updated.endswith(authored))
        self.assertTrue(channel.is_file())
        self.assertEqual(len(list(self.store.glob("*/video-insights.md"))), 1)
        self.assertIn(self.video_id, insights.published_index(self.root))

    def test_private_and_ledger_only_entries_get_no_notes(self):
        metadata = json.loads((self.folder / "metadata.json").read_text(encoding="utf-8"))
        metadata["availability"] = "private"
        (self.folder / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        (self.root / "archive.txt").write_text(f"youtube {self.video_id}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no verified published"):
            insights.prepare(self.root, "Sample channel")
        self.assertFalse((self.store / self.video_id / "video-insights.md").exists())

    def test_malformed_note_is_not_overwritten(self):
        insights.prepare(self.root, "Sample channel")
        note = self.store / self.video_id / "video-insights.md"
        note.write_text("My irreplaceable notes", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "refusing to change note"):
            insights.prepare(self.root, "Sample channel")
        self.assertEqual(note.read_text(encoding="utf-8"), "My irreplaceable notes")

    def test_old_collected_comment_text_expires_without_touching_agent_note(self):
        insights.prepare(self.root, "Sample channel")
        comments = self.store / self.video_id / "comments.json"
        comments.write_text(json.dumps({"source": "owned YouTube Data API commentThreads",
                                        "comments": [{"text": "old API data"}]}), encoding="utf-8")
        old = time.time() - insights.COMMENT_CACHE_SECONDS - 60
        os.utime(comments, (old, old))
        note = self.store / self.video_id / "video-insights.md"
        note.write_text(note.read_text(encoding="utf-8") + "Agent interpretation remains.\n", encoding="utf-8")
        insights.prepare(self.root, "Sample channel")
        self.assertFalse(comments.exists())
        self.assertIn("Agent interpretation remains.", note.read_text(encoding="utf-8"))

    def test_comments_keep_source_links_but_no_author_identity(self):
        payload = {"items": [{"snippet": {"topLevelComment": {"id": "Ugx123", "snippet": {
            "textOriginal": "Show the next step", "authorDisplayName": "Viewer Name",
            "authorChannelId": {"value": "secret"}, "publishedAt": "2026-11-18T00:00:00Z", "likeCount": 4}}}}]}
        comments = insights.parse_comment_threads(payload, self.video_id)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]["text"], "Show the next step")
        self.assertIn("lc=Ugx123", comments[0]["url"])
        self.assertNotIn("authorDisplayName", comments[0])
        self.assertNotIn("authorChannelId", comments[0])

    def test_comment_collector_uses_owned_token_and_writes_bounded_sample(self):
        item = {"snippet": {"topLevelComment": {"id": "Ugx123", "snippet": {
            "textOriginal": "Show the next step", "authorDisplayName": "Do not store"}}}}
        response = io.BytesIO(json.dumps({"items": [item]}).encode("utf-8"))
        with patch("analytics.ApiClient", return_value=SimpleNamespace(token={"access_token": "test-token"})), patch.object(
                insights.urllib.request, "urlopen", return_value=response) as get:
            result = insights.collect_comments(self.root, [{"id": self.video_id}], 1, {"slug": "sample"})
        self.assertEqual(result["videos"], 1)
        request = get.call_args.args[0]
        self.assertIn("videoId=ABCdef12345", request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        record = json.loads((self.store / self.video_id / "comments.json").read_text(encoding="utf-8"))
        self.assertEqual(len(record["comments"]), 1)
        self.assertNotIn("authorDisplayName", json.dumps(record))

    def test_refresh_reports_partial_failure_and_keeps_cached_evidence(self):
        settings = {"slug": "sample"}
        with patch.object(insights, "run_collector", side_effect=[{"status": "failed", "detail": "OAuth unavailable"},
                                                              {"status": "ok", "detail": "cached dataset"}]), patch.object(
                insights, "collect_comments", side_effect=ValueError("comments unavailable")):
            status = insights.refresh(self.root, "sample", self.config, 2, 0, 100, settings)
        self.assertEqual(status["analytics"]["status"], "failed")
        self.assertEqual(status["comments"]["status"], "unavailable")
        self.assertTrue((self.store / self.video_id / "metrics.json").exists())
        self.assertTrue((self.store / "video-insights-source-status.json").exists())

    def test_reauthorization_attempt_is_single_and_stops_dependent_collectors(self):
        with patch.object(insights, "run_collector", return_value={"status": "failed", "detail": "consent cancelled"}) as run, patch.object(
                insights, "collect_comments") as comments:
            status = insights.refresh(self.root, "sample", self.config, 2, 0, 100,
                                      {"slug": "sample"}, reauthorize=True)
        self.assertEqual(run.call_count, 1)
        self.assertIn("--reauthorize", run.call_args.args[0])
        comments.assert_not_called()
        self.assertEqual(status["dataset"]["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
