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
sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "content-studio-video" / "timeline" / "scripts"))
import preflight
import compiler


class PreflightTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg tools unavailable")
    def test_real_media_probe_accepts_utf8_metadata_on_windows(self):
        with tempfile.TemporaryDirectory() as scratch:
            sample = Path(scratch) / "dolphin-🐬.mp4"
            made = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                "testsrc2=size=160x90:rate=5:duration=1", "-metadata", "title=Dolphin 🐬",
                "-c:v", "mpeg4", str(sample),
            ], capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(made.returncode, 0, made.stderr[-500:])
            self.assertEqual(preflight.probe(sample)["width"], 160)
            self.assertEqual(compiler.media_info(sample)["video"]["width"], 160)

    def test_clipping_method_has_preflight_components(self):
        self.assertEqual(preflight._method_components("reviewed-hero-range"), [
            ("filter", "trim"), ("filter", "atrim"), ("filter", "crop"),
            ("filter", "scale"), ("filter", "concat"),
            ("encoder", "libx264"), ("encoder", "aac"),
        ])

    def test_long_cut_methods_are_profileable_without_claiming_an_encode(self):
        self.assertEqual(preflight._method_components("fastpan-scan"), [
            ("filter", "fps"), ("filter", "scale"), ("filter", "format")])
        self.assertEqual(preflight._method_components("tilt-scan"),
                         preflight._method_components("fastpan-scan"))
        self.assertEqual(preflight._method_components("long-cut-propose"), [])
        self.assertEqual(preflight._method_components("long-cut-build"), [])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg tools unavailable")
    def test_profile_reports_all_audio_streams_and_hash(self):
        with tempfile.TemporaryDirectory() as scratch:
            draft = Path(scratch)
            sample = draft / "two-mics.mp4"
            made = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                "testsrc2=size=160x90:rate=5:duration=1", "-f", "lavfi", "-i",
                "sine=frequency=440:duration=1", "-f", "lavfi", "-i",
                "sine=frequency=880:duration=1", "-map", "0:v:0", "-map", "1:a:0",
                "-map", "2:a:0", "-c:v", "mpeg4", "-c:a", "aac", str(sample)],
                capture_output=True, text=True)
            self.assertEqual(made.returncode, 0, made.stderr[-500:])
            report = preflight.profile(draft, sample, None, None, methods=["loudnorm"])
            media = report["sample"]
            self.assertEqual(media["sha256"], preflight._hash_file(sample))
            self.assertEqual([stream["index"] for stream in media["audio_streams"]], [1, 2])
            self.assertEqual(media["display"], {"width": 160, "height": 90, "rotation": 0})
            self.assertEqual(media["frame_timing"]["status"], "sampled")
            self.assertEqual(report["capabilities"]["methods"]["loudnorm"]["status"], "available")

    def test_sampled_frame_timing_distinguishes_variable_windows(self):
        def rows(interval, start):
            return subprocess.CompletedProcess([], 0, json.dumps({"frames": [
                {"best_effort_timestamp_time": str(start + i * interval)} for i in range(7)]}), "")
        with patch.object(preflight, "run_quiet", side_effect=[rows(.2, 0), rows(.1, 4)]):
            timing = preflight._sample_frame_timing(Path("unused.mp4"), 10)
        self.assertEqual(timing["status"], "sampled")
        self.assertTrue(timing["variable_frame_rate_suspected"])
        self.assertEqual(len(timing["windows"]), 2)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg tools unavailable")
    def test_actual_variable_rate_fixture_is_flagged(self):
        with tempfile.TemporaryDirectory() as scratch:
            sample = Path(scratch) / "variable.mkv"
            made = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                "testsrc2=size=160x90:rate=5:duration=1", "-f", "lavfi", "-i",
                "testsrc2=size=160x90:rate=10:duration=1", "-filter_complex",
                "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-fps_mode", "vfr",
                "-c:v", "ffv1", str(sample)], capture_output=True, text=True)
            self.assertEqual(made.returncode, 0, made.stderr[-500:])
            timing = preflight.probe(sample)["frame_timing"]
            self.assertEqual(timing["status"], "sampled")
            self.assertTrue(timing["variable_frame_rate_suspected"])

    def test_component_detection_keeps_missing_and_unknown_distinct(self):
        filters = subprocess.CompletedProcess([], 0, "Filters:\n .. loudnorm A->A\n", "")
        encoders = subprocess.CompletedProcess([], 1, "", "encoder listing failed")
        version = subprocess.CompletedProcess([], 0, "ffmpeg version 9.0\n", "")
        with patch.object(preflight.shutil, "which", return_value="ffmpeg"), patch.object(
                preflight, "run_quiet", side_effect=[version, filters, encoders]):
            report = preflight.capability_report(["loudnorm", "crop", "new-method"])
        self.assertEqual(report["methods"]["loudnorm"]["status"], "unknown")
        self.assertEqual(report["methods"]["crop"]["requirements"][0]["status"], "missing")
        self.assertEqual(report["methods"]["new-method"]["status"], "unknown")
        self.assertEqual(report["detection"]["encoder"]["status"], "unknown")

    def test_named_plan_method_requires_available_profile_capability(self):
        plan = {"schema_version": 1, "kind": "edited", "stage": "edited-render",
                "goal": "Render reviewed crop", "inputs": ["manual.mp4"],
                "deliverables": ["final.mp4"], "steps": preflight.default_steps("edited", "edited-render"),
                "system_profile": {"capabilities": {"methods": {"crop": {"status": "missing"}}}}}
        plan["steps"][1]["method_id"] = "crop"
        with self.assertRaisesRegex(ValueError, "capability is missing"):
            preflight.validate_plan(plan)
        plan["system_profile"]["capabilities"]["methods"]["crop"]["status"] = "available"
        preflight.validate_plan(plan)

    def test_every_supported_timeline_method_has_capability_mapping(self):
        registry = (Path(__file__).resolve().parents[2] / "content-studio-video" /
                    "timeline" / "methods.json")
        methods = json.loads(registry.read_text(encoding="utf-8"))["methods"]
        self.assertEqual([item["id"] for item in methods if item["status"] == "supported"
                          and preflight._method_components(item["id"]) is None], [])

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
            self.assertIn("analysis-only", initial["steps"][2]["route"])
            self.assertIn("no permanent", initial["steps"][2]["acceptance"])
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

    def test_supplied_render_plan_requires_timeline_approval_and_one_render(self):
        steps = preflight.default_steps("edited", "edited-render")
        self.assertIn("timeline-ready adapters", steps[1]["route"])
        self.assertEqual(steps[3]["title"], "Review and approve timeline")
        self.assertEqual(steps[4]["title"], "Render approved timeline once")
        self.assertEqual(steps[-1]["title"], "Review exact final render")

    def test_linkedin_precheck_is_media_optional_and_requires_package_review(self):
        with tempfile.TemporaryDirectory() as scratch:
            draft = Path(scratch)
            report = preflight.profile(draft, None, None, None, social=True)
            self.assertNotIn("No sample supplied", " ".join(report["recommendations"]))
            preflight.write_json(preflight.paths(draft)[0], report)
            with contextlib.redirect_stdout(io.StringIO()):
                preflight.main(["--folder", str(draft), "init", "--kind", "linkedin", "--goal", "Share an opinion",
                                "--input", "idea.md", "--deliverable", "LinkedIn package"])
            plan = preflight.read_json(preflight.paths(draft)[1])
            self.assertEqual(plan["stage"], "linkedin")
            self.assertEqual(plan["steps"][-1]["title"], "Review exact LinkedIn package")
            self.assertTrue(all(step["required"] for step in plan["steps"]))
            preflight.validate_plan(plan)

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

    def test_new_plan_can_read_published_video_insights_without_draft_copy(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "channel"
            draft = root / "drafts" / "next-video"
            draft.mkdir(parents=True)
            store = root / "analytics"
            store.mkdir()
            note = store / "video-insights.md"
            note.write_text("# Channel observations\n", encoding="utf-8")
            index = store / "published-index.json"
            index.write_text('{"videos": {}}', encoding="utf-8")
            result = preflight.published_video_insights(draft)
            self.assertTrue(result["available"])
            self.assertEqual(result["channel_note"], str(note))
            self.assertEqual(result["channel_note_sha256"], preflight._hash_file(note))
            self.assertEqual(result["published_index"], str(index))
            self.assertFalse((draft / "video-insights.md").exists())


if __name__ == "__main__":
    unittest.main()
