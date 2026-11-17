"""Safety and comparison contract for the script-only Indic-Mio preview."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "indic_mio_compare.py"
SPEC = importlib.util.spec_from_file_location("indic_mio_compare", SOURCE)
compare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare)


class IndicMioCompareTests(unittest.TestCase):
    def test_paired_text_and_emotion_suffixes(self):
        by_id = {item[0]: item for item in compare.CONDITIONS}
        self.assertEqual(by_id["kn-neutral"][2], by_id["kn-happy"][2])
        self.assertEqual(by_id["mixed-neutral"][2], by_id["mixed-surprise"][2])
        self.assertEqual(compare.EMOTIONS["neutral"], "")
        self.assertEqual(compare.EMOTIONS["happy"], "<happy>")
        self.assertEqual(compare.EMOTIONS["surprise"], "<surprise>")
        self.assertEqual(compare.model_text("hello!", "happy"), "hello! <happy>")
        self.assertTrue(all(len(text.split()) <= 6 for _, _, text in compare.CONDITIONS))

    def test_consent_is_required_before_reference_use(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory)
            (profile / "profile.json").write_text(
                json.dumps({"consent": {"affirmed": False, "note": ""}}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "consent"):
                compare.checked_profile(profile)

    def test_bundle_must_be_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "bundle is incomplete"):
                compare.checked_bundle(Path(directory))


if __name__ == "__main__":
    unittest.main()
