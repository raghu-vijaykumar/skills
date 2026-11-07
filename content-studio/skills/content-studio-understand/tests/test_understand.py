import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


understand = load_module("understand")
voiceover = load_module("voiceover")


def make_video(path, duration=12):
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size=320x180:rate=10:duration={duration}",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "mpeg4",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


class UnderstandTests(unittest.TestCase):
    def test_extracts_frames_and_timestamped_contact_sheet(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            video = root / "sample.mp4"
            make_video(video)
            result = understand.analyze(
                video,
                root / "out",
                interval=5,
                frame_width=160,
                grid_columns=2,
                grid_rows=2,
            )

            self.assertEqual(result["status"], "awaiting_vision_analysis")
            self.assertEqual(result["interval_seconds"], 5)
            self.assertEqual(len(result["source_sha256"]), 64)
            self.assertEqual(len(result["frames"]), 3)
            self.assertEqual([frame["id"] for frame in result["frames"]],
                             ["f0000", "f0001", "f0002"])
            self.assertEqual(len(result["contact_sheets"]), 1)
            self.assertEqual(result["contact_sheets"][0]["id"], "sheet-0001")
            self.assertEqual(
                result["contact_sheets"][0]["frame_ids"],
                ["f0000", "f0001", "f0002"],
            )
            self.assertTrue(
                (root / "out" / result["contact_sheets"][0]["path"]).is_file()
            )
            self.assertEqual(result["frames"][0]["sheet_id"], "sheet-0001")
            self.assertTrue((root / "out" / "evidence.json").is_file())
            self.assertTrue((root / "out" / "voiceover-template.json").is_file())
            self.assertTrue((root / "out" / "observations-template.json").is_file())

    def test_range_offsets_frame_times_and_records_context(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            video = root / "sample.mp4"
            make_video(video)
            context = root / "context.json"
            context.write_text(
                json.dumps({"language": "Kannada-English", "tone": "casual"}),
                encoding="utf-8",
            )
            result = understand.analyze(
                video,
                root / "out",
                interval=5,
                start=2,
                end=9,
                frame_width=160,
                grid=False,
                context=context,
            )

            times = [frame["at_seconds"] for frame in result["frames"]]
            self.assertEqual(len(times), 2)
            self.assertAlmostEqual(times[0], 2, delta=0.2)
            self.assertAlmostEqual(times[1], 7, delta=0.2)
            self.assertEqual(result["contact_sheets"], [])
            self.assertEqual(result["human_context"]["language"], "Kannada-English")
            template = json.loads(
                (root / "out" / "voiceover-template.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(template["language"], "Kannada-English")

    def test_rejects_invalid_interval(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            video = root / "sample.mp4"
            make_video(video, duration=3)
            with self.assertRaises(ValueError):
                understand.analyze(video, root / "out", interval=0)


class VoiceoverTests(unittest.TestCase):
    def evidence(self, duration=20):
        return {
            "duration_seconds": duration,
            "source_sha256": "a" * 64,
            "frames": [{"id": f"f{index:04d}"} for index in range(5)],
        }

    def script(self, **overrides):
        value = {
            "title": "Test vlog",
            "language": "Kannada-English",
            "source_sha256": "a" * 64,
            "segments": [
                {
                    "id": "v01",
                    "start": 0,
                    "end": 10,
                    "text": "Namaskara guys, idu namma Dubai day three.",
                    "evidence_frame_ids": ["f0000", "f0001"],
                    "needs_review": False,
                },
                {
                    "id": "v02",
                    "start": 10,
                    "end": 20,
                    "text": "Next we go to the frame and see the view.",
                    "evidence_frame_ids": ["f0002"],
                    "needs_review": False,
                },
            ],
        }
        value.update(overrides)
        return value

    def test_valid_script_passes(self):
        report = voiceover.validate(self.script(), self.evidence())
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["segment_count"], 2)
        self.assertAlmostEqual(report["coverage_ratio"], 1.0)

    def test_overlap_and_fast_pace_fail(self):
        script = self.script()
        script["segments"][1]["start"] = 9
        script["segments"][1]["text"] = " ".join(["word"] * 40)
        report = voiceover.validate(script, self.evidence())
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("overlaps" in item for item in report["errors"]))
        self.assertTrue(any("words/sec" in item for item in report["errors"]))

    def test_unknown_evidence_and_missing_evidence_ids_are_reported(self):
        script = self.script()
        script["segments"][0]["evidence_frame_ids"] = ["missing"]
        script["segments"][1]["evidence_frame_ids"] = []
        report = voiceover.validate(script, self.evidence())
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("unknown evidence frame" in item for item in report["errors"]))
        self.assertTrue(any("no evidence_frame_ids" in item for item in report["warnings"]))

    def test_default_review_flag_triggers_review_status(self):
        script = self.script()
        del script["segments"][0]["needs_review"]
        report = voiceover.validate(script, self.evidence())
        self.assertEqual(report["status"], "review")
        self.assertTrue(report["segments"][0]["needs_review"])

    def test_render_writes_markdown_teleprompter_csv_and_report(self):
        with tempfile.TemporaryDirectory() as scratch:
            out = Path(scratch)
            script = self.script()
            report = voiceover.validate(script, self.evidence())
            paths = voiceover.write_outputs(script, report, out)

            markdown = Path(paths["markdown"]).read_text(encoding="utf-8")
            teleprompter = Path(paths["teleprompter"]).read_text(encoding="utf-8")
            csv_text = Path(paths["csv"]).read_text(encoding="utf-8-sig")
            saved = json.loads(Path(paths["report"]).read_text(encoding="utf-8"))

            self.assertIn("## 00:00-00:10 · v01", markdown)
            self.assertIn("Namaskara guys", markdown)
            self.assertTrue(teleprompter.startswith("[00:00] Namaskara"))
            self.assertIn("v01,0.0,10.0,00:00,00:10", csv_text)
            self.assertEqual(saved["status"], "pass")


if __name__ == "__main__":
    unittest.main()
