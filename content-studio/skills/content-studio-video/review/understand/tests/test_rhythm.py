import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "script_rhythm.py"
spec = importlib.util.spec_from_file_location("script_rhythm", SCRIPT)
rhythm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rhythm)


class RhythmTests(unittest.TestCase):
    def test_long_run_points_to_source_cues_and_times(self):
        passages = [
            {"id": "v01", "start": 2, "end": 8,
             "text": "We searched every street near the station for the last open library."},
            {"id": "v02", "start": 9, "end": 15,
             "text": "The first building looked promising but its doors were already locked."},
            {"id": "v03", "start": 16, "end": 22,
             "text": "Another place across town stayed open later according to the sign outside."},
        ]
        report = rhythm.analyze(passages)
        run = next(item for item in report["observations"] if item["kind"] == "long_run")
        self.assertEqual(run["cue_ids"], ["v01", "v02", "v03"])
        self.assertEqual((run["start"], run["end"]), (2, 22))
        self.assertEqual(len(run["sentence_word_counts"]), 3)

    def test_short_pivot_breaks_run_without_required_alternation(self):
        lines = [
            "We searched every street near the station for the last open library.",
            "The first building looked promising but its doors were already locked.",
            "Then we got lucky.",
            "Another place across town stayed open later according to the sign outside.",
        ]
        report = rhythm.analyze([{"id": f"v{i}", "text": line}
                                 for i, line in enumerate(lines)])
        self.assertFalse(any(item["kind"] == "long_run" for item in report["observations"]))
        self.assertEqual(report["status"], "advisory")

    def test_repeated_opening_and_tight_cue_are_advisory(self):
        passages = [
            {"id": "a", "text": "I first checked the old entrance."},
            {"id": "b", "text": "I first went down the stairs."},
            {"id": "c", "text": "I first asked at reception.",
             "start": 8, "end": 10, "words_per_second": 3.1},
        ]
        report = rhythm.analyze(passages)
        self.assertEqual({item["kind"] for item in report["observations"]},
                         {"repeated_opening", "tight_cue"})
        self.assertEqual(report["status"], "advisory")

    def test_bilingual_necessary_explanation_and_silence(self):
        passages = [
            {"id": "k1", "text": "Naavu market ge hodvi. Then it rained."},
            {"id": "k2", "text": "The pump opens when pressure pushes this valve against the spring."},
            {"id": "k3", "text": ""},
        ]
        report = rhythm.analyze(passages)
        self.assertEqual(report["observations"], [])
        self.assertEqual(rhythm.analyze([])["observations"], [])

    def test_natural_sound_gap_ends_a_long_line_run(self):
        lines = [
            "We searched every street near the station for the last open library.",
            "The first building looked promising but its doors were already locked.",
            "Another place across town stayed open later according to the sign outside.",
        ]
        passages = [{"id": f"v{i}", "start": start, "end": start + 5,
                     "text": line} for i, (start, line) in
                    enumerate(zip((0, 5, 15), lines))]
        report = rhythm.analyze(passages)
        self.assertFalse(any(item["kind"] == "long_run" for item in report["observations"]))

    def test_code_driven_phrases_use_same_analyzer(self):
        passages = [{"id": f"p{i}", "text": text} for i, text in enumerate([
            "The first valve opens after pressure rises enough.",
            "The second valve closes when the arm returns.",
            "The final switch resets before the cycle repeats.",
        ])]
        report = rhythm.analyze(passages, mode="narration")
        self.assertEqual(report["observations"][0]["kind"], "long_run")

    def test_json_stdin_cli(self):
        payload = {"mode": "narration", "passages": [
            {"id": "p1", "text": "A short line."}]}
        result = subprocess.run([sys.executable, str(SCRIPT), "--stdin"],
                                input=json.dumps(payload), text=True,
                                capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)["passage_count"], 1)


if __name__ == "__main__":
    unittest.main()
