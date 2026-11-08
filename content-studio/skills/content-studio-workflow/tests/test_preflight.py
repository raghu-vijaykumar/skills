import json
import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import preflight


class PreflightTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg tools unavailable")
    def test_short_media_profile_reports_measured_and_unknown_times(self):
        with tempfile.TemporaryDirectory() as scratch:
            draft = Path(scratch)
            sample = draft / "sample.mp4"
            made = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                                   "-i", "testsrc2=size=320x180:rate=5", "-t", "0.4", "-c:v", "mpeg4", str(sample)],
                                  capture_output=True, text=True)
            self.assertEqual(made.returncode, 0, made.stderr[-500:])
            report = preflight.profile(draft, sample, planned_minutes=2, ai_seconds_per_frame=None)
            self.assertEqual(report["sample"]["width"], 320)
            self.assertTrue(report["benchmarks"]["decode_2s"]["ok"])
            self.assertTrue(report["benchmarks"]["lanczos_2s"]["ok"])
            self.assertIsNone(report["estimates"]["ai_upscale_hours"])
            self.assertIn("pilot", report["estimates"]["basis"])

    def test_profile_plan_review_and_revision_gate(self):
        with tempfile.TemporaryDirectory() as scratch:
            draft = Path(scratch)
            report = preflight.profile(draft, None, None, None)
            self.assertIsNone(report["sample"])
            self.assertIn("cpu_logical", report["machine"])
            system_file, plan_file, _, _ = preflight.paths(draft)
            preflight.write_json(system_file, report)
            def call(*args):
                with contextlib.redirect_stdout(io.StringIO()):
                    return preflight.main(["--folder", str(draft), *args])
            self.assertEqual(call("init", "--kind", "edited", "--goal", "Make a vlog",
                                  "--input", "raw footage", "--deliverable", "prepared clips"), 0)
            initial = preflight.read_json(plan_file)
            self.assertEqual(initial["stage"], "source-prep")
            self.assertEqual(len(initial["steps"]), 4)
            self.assertIn("no AutoCut", initial["steps"][2]["route"])
            self.assertIn("manual edit", initial["steps"][3]["route"])
            self.assertEqual(call("review"), 0)
            with self.assertRaisesRegex(ValueError, "approval.*missing"):
                preflight.approved(draft)
            self.assertEqual(call("approve", "--note", "User approved the clip handoff plan"), 0)
            self.assertEqual(call("verify"), 0)
            with self.assertRaisesRegex(ValueError, "incomplete"):
                call("verify", "--phase", "complete")
            with self.assertRaisesRegex(ValueError, "Only optional"):
                call("set", "--id", "S01", "--status", "not_applicable", "--reason", "skip")
            plan = preflight.read_json(plan_file)
            plan["steps"][3]["route"] = "Use only selected timeline ranges for AI previews"
            preflight.write_json(plan_file, plan)
            with self.assertRaisesRegex(ValueError, "stale"):
                call("verify")
            self.assertEqual(call("approve", "--note", "User approved the revised clip route"), 0)
            for step in plan["steps"]:
                call("set", "--id", step["id"], "--status", "done", "--evidence", "reviewed result")
            self.assertEqual(call("verify", "--phase", "complete"), 0)
            if shutil.which("node"):
                module = (Path(__file__).resolve().parents[3] / "scripts" / "preflight.mjs").as_uri()
                code = f"import {{validatePreflight}} from {json.dumps(module)}; validatePreflight({json.dumps(str(draft))}, 'complete');"
                checked = subprocess.run(["node", "--input-type=module", "-e", code], capture_output=True, text=True)
                self.assertEqual(checked.returncode, 0, checked.stderr[-500:])

    def test_runner_does_not_execute_without_approved_plan(self):
        with tempfile.TemporaryDirectory() as scratch:
            draft = Path(scratch)
            sentinel = draft / "ran.txt"
            config = draft / "workflow.json"
            config.write_text(json.dumps({"workspace": str(draft), "steps": [{"id": "run", "plan_step": "S03",
                "command": [sys.executable, "-c", f"from pathlib import Path; Path({str(sentinel)!r}).write_text('ran')"]}]}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPTS / "workflow.py"), "--prompt", str(config)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(sentinel.exists())
            report = preflight.profile(draft, None, None, None)
            preflight.write_json(preflight.paths(draft)[0], report)
            with contextlib.redirect_stdout(io.StringIO()):
                preflight.main(["--folder", str(draft), "init", "--kind", "edited", "--goal", "Test run",
                                "--input", "sample", "--deliverable", "result"])
                plan_file = preflight.paths(draft)[1]
                plan = preflight.read_json(plan_file)
                plan["steps"][2]["command"] = json.loads(config.read_text())["steps"][0]["command"]
                preflight.write_json(plan_file, plan)
                preflight.main(["--folder", str(draft), "approve", "--note", "User reviewed"])
            result = subprocess.run([sys.executable, str(SCRIPTS / "workflow.py"), "--prompt", str(config)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Complete approved plan step S01", result.stderr)
            for step_id in ("S01", "S02"):
                with contextlib.redirect_stdout(io.StringIO()):
                    preflight.main(["--folder", str(draft), "set", "--id", step_id, "--status", "done",
                                    "--evidence", "reviewed"])
            result = subprocess.run([sys.executable, str(SCRIPTS / "workflow.py"), "--prompt", str(config)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(sentinel.exists())
            sentinel.unlink()
            config_data = json.loads(config.read_text())
            config_data["steps"][0]["command"].append("changed")
            config.write_text(json.dumps(config_data))
            result = subprocess.run([sys.executable, str(SCRIPTS / "workflow.py"), "--prompt", str(config)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("differs from the approved plan", result.stderr)
            self.assertFalse(sentinel.exists())

    def test_supplied_render_plan_orders_voice_upscale_and_graphics(self):
        steps = preflight.default_steps("edited", "edited-render")
        self.assertIn("voice then upscale then code graphics", steps[1]["route"])
        self.assertEqual(steps[-1]["title"], "Review exact final render")

    def test_new_plan_reads_same_confirmed_memory_database(self):
        with tempfile.TemporaryDirectory() as scratch:
            database = Path(scratch) / "editing-memory.sqlite"
            with patch.dict("os.environ", {"CONTENT_STUDIO_MEMORY_DB": str(database)}):
                missing = preflight.confirmed_preferences("travel", "trip")
                self.assertFalse(missing["database_exists"])
                self.assertFalse(database.exists())
                scripts = Path(__file__).resolve().parents[3] / "skills" / "content-studio-video" / "memory" / "scripts"
                sys.path.insert(0, str(scripts))
                import memory
                connection = memory.connect(database)
                connection.execute("INSERT INTO preferences(scope,key,value_json) VALUES(?,?,?)",
                                   ("travel", "meme_intensity", '"low"'))
                connection.commit()
                connection.close()
                found = preflight.confirmed_preferences("travel", "trip")
                self.assertEqual(found["preferences"]["meme_intensity"]["value"], "low")


if __name__ == "__main__":
    unittest.main()
