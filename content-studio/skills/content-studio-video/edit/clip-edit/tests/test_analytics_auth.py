import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analytics import ApiClient, OAuthError  # noqa: E402


class AnalyticsAuthTest(unittest.TestCase):
    def test_missing_client_file_uses_cached_client_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            token = root / "token.json"
            token.write_text(json.dumps({"client_id": "cached-id", "client_secret": "cached-secret"}))
            client = object.__new__(ApiClient)
            client.credentials = root / "missing-client.json"
            client.token_path = token
            self.assertEqual(client._credentials()["client_id"], "cached-id")

    def test_missing_client_pair_still_requires_client_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            token = root / "token.json"
            token.write_text(json.dumps({"client_id": "cached-id"}))
            client = object.__new__(ApiClient)
            client.credentials = root / "missing-client.json"
            client.token_path = token
            with self.assertRaisesRegex(OAuthError, "missing OAuth client file"):
                client._credentials()


if __name__ == "__main__":
    unittest.main()
