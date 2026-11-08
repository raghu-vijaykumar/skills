import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import competitors
import insights


class PublicComparisonTest(unittest.TestCase):
    def test_public_rows_never_claim_private_metrics(self):
        calls = []
        def extract(url, *, flat):
            calls.append((url, flat))
            if flat:
                return {"entries": [{"id": "ABCdef12345"}]}
            return {"id": "ABCdef12345", "title": "Mechanism", "channel": "Another channel",
                    "view_count": 1234, "like_count": 45, "comment_count": 6,
                    "upload_date": "20261029", "duration": 80}
        rows, failures = competitors.collect("distributed cache", [], 5, extract)
        self.assertEqual(len(rows), 1)
        self.assertFalse(failures)
        self.assertEqual(rows[0]["url"], "https://www.youtube.com/watch?v=ABCdef12345")
        self.assertIsNone(rows[0]["ctr"])
        self.assertIsNone(rows[0]["vtr"])
        self.assertIsNone(rows[0]["retention"])
        self.assertEqual(len(calls), 2)

    def test_oauth_failure_keeps_private_metrics_unavailable(self):
        import io
        import urllib.error
        from unittest.mock import patch
        response = io.BytesIO(b'{"error":"invalid_grant"}')
        with patch.object(insights.analytics.urllib.request, "urlopen",
                          side_effect=urllib.error.HTTPError("https://oauth2.googleapis.com/token",
                                                              400, "Bad Request", {}, response)):
            client = object.__new__(insights.analytics.ApiClient)
            with self.assertRaisesRegex(insights.analytics.OAuthError, "invalid_grant"):
                client._post({"grant_type": "refresh_token"})

    def test_bad_public_video_is_reported(self):
        rows, failures = competitors.collect("", ["not-a-video"], 2, lambda *_args, **_kwargs: {})
        self.assertFalse(rows)
        self.assertEqual(len(failures), 1)


class OwnedAnalyticsTest(unittest.TestCase):
    def test_ctr_and_creative_metadata_flow_into_cohort(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            folder = Path(scratch)
            (folder / "creative.json").write_text(json.dumps({"themeId": "revise-labs",
                "styleId": "core-explainer", "renderer": "remotion", "choices": ["dense-captions"]}), encoding="utf-8")
            videos = [{"id": "abc", "kind": "long", "title": "A", "upload_date": "2026-10-30",
                       "duration": 100, "folder": folder}]
            metrics = {"abc": {"views": 100, "impressions": 1000,
                               "impressionsClickThroughRate": 7.2, "averageViewPercentage": 42}}
            rows = insights.build_rows(videos, metrics, {})
            self.assertEqual(rows[0]["ctr"], 7.2)
            self.assertEqual(rows[0]["style_id"], "core-explainer")
            result = insights.analyse(rows)
            self.assertEqual(result["ctr_count"], 1)
            self.assertEqual(result["style_cohorts"][0]["medianCtr"], 7.2)

    def test_style_experiment_requires_comparable_samples_and_keeps_preset_unchanged(self):
        cohorts = [{"kind": "long", "styleId": style, "n": 3,
                    "medianAveragePercentage": pct, "largestDrops": []}
                   for style, pct in (("hairline", 56.0), ("core-explainer", 41.0))]
        proposal = insights.style_experiments(cohorts)
        self.assertEqual(proposal[0]["tryStyleId"], "hairline")
        self.assertEqual(proposal[0]["sampleCounts"]["hairline"], 3)
        self.assertIn("Do not edit shared presets", proposal[0]["note"])
        self.assertEqual(insights.style_experiments(cohorts[:1]), [])

    def test_owned_studio_reach_fields_are_extracted(self):
        payload = {"metricTotals": {"videoThumbnailImpressions": 1000,
                                    "videoThumbnailImpressionsCtr": 5.5}}
        _, reach = insights.analytics.extract_points([payload])
        self.assertEqual(reach["impressions"], 1000)
        self.assertEqual(reach["impressionsClickThroughRate"], 5.5)

    def test_missing_ctr_is_null(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            videos = [{"id": "abc", "kind": "shorts", "title": "A", "upload_date": "2026-10-30",
                       "duration": 30, "folder": Path(scratch)}]
            rows = insights.build_rows(videos, {"abc": {"views": 10}}, {})
            self.assertIsNone(rows[0]["ctr"])
            self.assertEqual(insights.analyse(rows)["ctr_count"], 0)


if __name__ == "__main__":
    unittest.main()
