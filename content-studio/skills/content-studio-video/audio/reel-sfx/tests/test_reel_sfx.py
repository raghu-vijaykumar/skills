import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "reel_sfx.py"
spec = importlib.util.spec_from_file_location("reel_sfx", SCRIPT)
reel_sfx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reel_sfx)


class ReelSFXTests(unittest.TestCase):
    def test_canonical_url_strips_tracking_and_rejects_other_sites(self):
        self.assertEqual(
            reel_sfx.canonical_url("https://www.instagram.com/reel/DeipetNNFCX/?obrf=abc"),
            ("https://www.instagram.com/reel/DeipetNNFCX/", "DeipetNNFCX"))
        for url in ("http://www.instagram.com/reel/abc/",
                    "https://example.com/reel/abc/",
                    "https://www.instagram.com/p/abc/"):
            with self.assertRaises(ValueError):
                reel_sfx.canonical_url(url)

    def test_export_exact_candidate_with_provenance_and_preserved_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.wav"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                            "-i", "sine=frequency=750:duration=2", "-c:a", "pcm_s16le", str(source)],
                           check=True, capture_output=True)
            original = reel_sfx.sha256(source)
            source_record = root / "source.json"
            source_record.write_text(json.dumps({"sha256": original,
                                                 "url": "https://www.instagram.com/reel/abc/",
                                                 "creator": "Example"}), encoding="utf-8")
            output = root / "candidates" / "hit.wav"
            record = reel_sfx.extract(source, output, .4, .85, "Hit", "impact", source_record)
            self.assertEqual(record["source_sha256"], original)
            self.assertEqual(record["source_url"], "https://www.instagram.com/reel/abc/")
            self.assertEqual(record["effect_review"], "pending")
            self.assertEqual(record["reuse_status"], "reference-only")
            self.assertAlmostEqual(reel_sfx.probe(output)["duration_seconds"], .45, places=2)
            self.assertEqual(reel_sfx.sha256(source), original)
            self.assertEqual(json.loads(output.with_suffix(".json").read_text())["sha256"],
                             reel_sfx.sha256(output))
            with self.assertRaisesRegex(ValueError, "inside the source"):
                reel_sfx.extract(source, root / "bad.wav", 1.9, 2.5, "Bad", "impact")

    def test_existing_download_is_verified_before_reuse(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            media = root / "reel-abc.mp4"
            media.write_bytes(b"already downloaded")
            record = {"url": "https://www.instagram.com/reel/abc/",
                      "sha256": reel_sfx.sha256(media), "media": str(media)}
            (root / "reel-abc.source.json").write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual(reel_sfx.download(record["url"], root), record)
            media.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "differs"):
                reel_sfx.download(record["url"], root)


if __name__ == "__main__":
    unittest.main()
