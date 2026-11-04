import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "master.py"
spec = importlib.util.spec_from_file_location("master", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MasterTests(unittest.TestCase):
    def test_loudness_fix_is_measured_on_output_and_has_listenable_evidence(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            source = root / "quiet.mp4"
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-hide_banner",
                            "-loglevel", "error", "-f", "lavfi", "-i",
                            "sine=frequency=440:duration=3", "-af", "volume=0.05",
                            "-c:a", "aac", str(source)], check=True,
                           capture_output=True)
            result = module.master(source, root, False, audio_only=True,
                                   review_dir=root / "review")
            self.assertEqual(result["decision"], "FIX")
            self.assertEqual(result["validation"]["status"], "passed")
            self.assertTrue(Path(result["review_audio"]["before"]).is_file())
            self.assertTrue(Path(result["review_audio"]["after"]).is_file())

    def test_failed_cleanup_candidate_falls_back_with_review_evidence(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            source = root / "quiet.mp4"
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-hide_banner",
                            "-loglevel", "error", "-f", "lavfi", "-i",
                            "sine=frequency=440:duration=3", "-af", "volume=0.05",
                            "-c:a", "aac", str(source)], check=True,
                           capture_output=True)
            original_measure = module.measure
            output_reads = 0

            def measured(path, filters):
                nonlocal output_reads
                result = original_measure(path, "" if filters else filters)
                if Path(path).name.endswith(".mastered.tmp.wav"):
                    output_reads += 1
                    if output_reads == 1:
                        result["input_i"] = "-22.68"
                return result

            with patch.object(module, "measure", side_effect=measured):
                result = module.master(source, root, False, audio_only=True,
                                       filters=module.build_filter(cleanup=True))
            self.assertEqual(result["decision"], "REVIEW")
            self.assertEqual(result["filters"], "")
            self.assertEqual(result["validation"]["status"], "review_required")
            self.assertEqual(len(result["rejected_candidates"]), 1)

    def test_cleanup_adds_deesser_and_gate_in_order(self):
        chain = module.build_filter(cleanup=True)
        self.assertIn("highpass=f=80", chain)
        self.assertIn("afftdn", chain)
        self.assertIn("deesser", chain)
        self.assertIn("agate", chain)
        self.assertLess(chain.index("deesser"), chain.index("agate"))

    def test_arnndn_replaces_afftdn(self):
        chain = module.build_filter(arnndn_model="model.rnnn")
        self.assertIn("arnndn", chain)
        self.assertNotIn("afftdn", chain)

    def test_measure_filter_handles_empty_and_nonempty_chains(self):
        self.assertEqual(
            module.measure_filter(""),
            "loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json",
        )
        self.assertEqual(
            module.measure_filter("highpass=f=80,afftdn=nf=-28"),
            "highpass=f=80,afftdn=nf=-28,"
            "loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json",
        )


if __name__ == "__main__":
    unittest.main()
