import contextlib
import copy
import io
import json
import math
import struct
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import approval  # noqa: E402
import compiler  # noqa: E402
import model  # noqa: E402
import timeline as cli  # noqa: E402
import verify as delivery_verify  # noqa: E402


class MasteringDecisionTests(unittest.TestCase):
    def test_skip_fix_and_missed_output_stay_distinct(self):
        clean = {"integrated_lufs": -16.2, "true_peak_dbtp": -1.8}
        self.assertEqual(delivery_verify._mastering_result(
            {"decision": "SKIP", "measurement": {}}, clean)["status"], "SKIP")
        self.assertEqual(delivery_verify._mastering_result(
            {"decision": "FIX", "measurement": {}}, clean)["status"], "FIX")
        missed = {"integrated_lufs": -19.5, "true_peak_dbtp": -.5}
        self.assertEqual(delivery_verify._mastering_result(
            {"decision": "FIX", "measurement": {}}, missed)["status"], "REVIEW")
        self.assertEqual(delivery_verify._mastering_result(
            {"decision": "SKIP", "measurement": {}}, missed)["status"], "REVIEW")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required")
class DeliveryTimelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = self.root / "preflight" / "plan.json"
        self.plan.parent.mkdir()
        self.plan.write_text(json.dumps({
            "schema_version": 1, "kind": "edited", "stage": "edited-render",
            "steps": [{"id": "S01"}],
        }), encoding="utf-8")
        (self.plan.parent / "approval.json").write_text(json.dumps({
            "plan_sha256": model.sha256_file(self.plan),
            "review_note": "Approved fixture plan", "actor": "human",
        }), encoding="utf-8")
        (self.plan.parent / "checklist.json").write_text(json.dumps({
            "plan_sha256": model.sha256_file(self.plan),
            "items": [{"id": "S01"}],
        }), encoding="utf-8")
        self.source = self.root / "source.mp4"
        self.voice = self.root / "voice.wav"
        source = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10:duration=3",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(self.source),
        ], capture_output=True, text=True)
        self.assertEqual(source.returncode, 0, source.stderr)
        voice = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "sine=frequency=880:duration=0.5",
            str(self.voice),
        ], capture_output=True, text=True)
        self.assertEqual(voice.returncode, 0, voice.stderr)
        self.font = self.root / "font.ttf"
        shutil.copyfile(Path("C:/Windows/Fonts/arial.ttf"), self.font)
        self.sidecar = self.root / "graphics.ass"
        self.sidecar.write_text("""[Script Info]
ScriptType: v4.00+
PlayResX: 160
PlayResY: 90
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.20,0:00:00.60,Default,,0,0,0,,Reviewed graphic
""", encoding="utf-8")
        self.output = self.root / "delivery.mp4"
        self.timeline_path = self.root / "timeline-v001.json"
        self.timeline = model.make_initial(self.plan, self.source, self.output,
                                           fps=10, width=320, height=180)
        self.timeline["picture"] = [
            {"id": "p1", "source": self.source.name,
             "sha256": model.sha256_file(self.source),
             "source_in": 0, "source_out": 1.5, "audio_gain": 0.35},
            {"id": "p2", "source": self.source.name,
             "sha256": model.sha256_file(self.source),
             "source_in": 2, "source_out": 3},
        ]
        self.timeline["transitions"] = [
            {"after": "p1", "id": "cross-fade", "duration": 0.3,
             "review_status": "approved"}
        ]
        self.timeline["operations"] = [
            {"id": "lens", "method": "lens-correction", "k1": 0.01,
             "k2": 0, "start": 0.6, "end": 0.8,
             "review_status": "approved"},
            {"id": "crop", "method": "crop", "x": 0.1, "y": 0,
             "w": 0.8, "h": 1, "start": 0.6, "end": 0.8,
             "review_status": "approved"},
            {"id": "denoise", "method": "denoise-light", "start": 0.5,
             "end": 2.0, "review_status": "approved"},
            {"id": "upscale", "method": "upscale-lanczos", "scale": 2,
             "start": 1.0, "end": 1.5, "review_status": "approved"},
            {"id": "title", "method": "title", "text": "Reviewed title", "font_source": self.font.name,
             "font_sha256": model.sha256_file(self.font),
             "start": 0.1, "end": 0.5, "review_status": "approved"},
            {"id": "graphics", "method": "motion-graphics-ass",
             "source": self.sidecar.name,
             "sha256": model.sha256_file(self.sidecar),
             "start": 0, "end": 2.2, "review_status": "approved"},
        ]
        self.timeline["audio"] = [
            {"id": "voice1", "kind": "voice", "source": self.voice.name,
             "sha256": model.sha256_file(self.voice), "start": 0.8,
             "gain": 0.5, "review_status": "approved"}
        ]
        model.write_new(self.timeline_path, self.timeline)

    def tearDown(self):
        self.temp.cleanup()

    def test_music_loop_stays_a_finite_input_to_one_render(self):
        self.timeline["operations"] = []
        self.timeline["transitions"] = []
        self.timeline["picture"] = [{
            "id": "p1", "source": self.source.name,
            "sha256": model.sha256_file(self.source),
            "source_in": 0, "source_out": 2.2, "audio_gain": 0,
        }]
        self.timeline["audio"] = [{
            "id": "bed", "kind": "music", "source": self.voice.name,
            "sha256": model.sha256_file(self.voice), "start": 0.1,
            "duration": 2, "loop": True, "gain": 0.2,
            "fade_in": 0.1, "fade_out": 0.1,
            "review_status": "approved",
        }]
        resolved = model.validate(self.timeline)
        inputs, graph = compiler.compile_graph(self.timeline, resolved)
        self.assertIn("-stream_loop", inputs)
        self.assertIn("afade=t=out:st=1.900000:d=0.100000", graph)
        rendered = compiler.preview(self.timeline, resolved,
                                    self.root / "loop-preview.mp4", 0, 2.2)
        self.assertAlmostEqual(rendered["duration"], 2.2, delta=.15)

    def test_short_voice_tail_is_trimmed_but_long_overrun_is_rejected(self):
        self.timeline["operations"] = []
        self.timeline["transitions"] = []
        self.timeline["picture"] = [{
            "id": "p1", "source": self.source.name,
            "sha256": model.sha256_file(self.source),
            "source_in": 0, "source_out": 2.2, "audio_gain": 0,
        }]
        voice = self.root / "long-voice.wav"
        for length, accepted in ((2.3, True), (2.4, False)):
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", f"sine=frequency=880:duration={length}",
                str(voice),
            ], check=True, capture_output=True, text=True)
            self.timeline["audio"] = [{
                "id": "voice1", "kind": "voice", "source": voice.name,
                "sha256": model.sha256_file(voice), "start": 0,
                "gain": 1, "review_status": "approved",
            }]
            resolved = model.validate(self.timeline)
            if accepted:
                _, graph = compiler.compile_graph(self.timeline, resolved)
                self.assertIn("atrim=duration=2.200000", graph)
            else:
                with self.assertRaisesRegex(ValueError, "extends past the picture"):
                    compiler.compile_graph(self.timeline, resolved)

    def _approved(self):
        record = {"actor": "human", "reviewer": "fixture editor",
                  "review_note": "Reviewed timing and voice",
                  "approved_at": "2026-11-08T12:00:00+05:30",
                  "fingerprint": approval.fingerprint(
                      self.timeline_path, self.timeline)}
        path = self.root / "timeline-approval.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def test_cli_init_and_revision_follow_same_timeline_path(self):
        initial = self.root / "cli-v001.json"
        revised = self.root / "cli-v002.json"
        changes = self.root / "changes.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main([
                "init", "--plan", str(self.plan), "--source", str(self.source),
                "--output", str(self.root / "cli-final-v001.mp4"),
                "--timeline", str(initial), "--fps", "10",
                "--width", "160", "--height", "90"]), 0)
        first_plan = Path(model.load(initial)["plan_file"])
        self.assertEqual(first_plan.read_bytes(), self.plan.read_bytes())
        # The live preflight may change for a revision; the older approved
        # timeline keeps its exact plan and checklist for later audit.
        revised_plan = json.loads(self.plan.read_text(encoding="utf-8"))
        revised_plan["goal"] = "revised edit"
        self.plan.write_text(json.dumps(revised_plan), encoding="utf-8")
        digest = model.sha256_file(self.plan)
        self.plan.with_name("approval.json").write_text(json.dumps({
            "plan_sha256": digest, "review_note": "Approved revised fixture plan",
            "actor": "human"}), encoding="utf-8")
        self.plan.with_name("checklist.json").write_text(json.dumps({
            "plan_sha256": digest, "items": [{"id": "S01"}]}), encoding="utf-8")
        self.assertEqual(model.validate(model.load(initial))["duration"], 3)
        changes.write_text(json.dumps({"operations": [{
            "id": "draft-look", "method": "color-eq",
            "start": 0.2, "end": 0.5, "brightness": 0.02,
            "review_status": "pending_review",
        }]}), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main([
                "revise", "--timeline", str(initial), "--plan", str(self.plan),
                "--changes", str(changes), "--out", str(revised),
                "--output", str(self.root / "cli-final-v002.mp4")]), 0)
        self.assertEqual(model.load(initial)["revision"], 1)
        self.assertEqual(model.load(revised)["revision"], 2)
        self.assertNotEqual(model.load(initial)["plan_sha256"],
                            model.load(revised)["plan_sha256"])
        self.assertEqual(Path(model.load(revised)["plan_file"]).read_bytes(),
                         self.plan.read_bytes())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["validate", "--timeline", str(revised)]), 0)

    def test_ranges_resolve_after_cut_and_overlap(self):
        resolved = model.validate(self.timeline)
        self.assertAlmostEqual(resolved["duration"], 2.2)
        self.assertAlmostEqual(resolved["clips"][1]["start"], 1.2)
        inputs, graph = compiler.compile_graph(self.timeline, resolved)
        self.assertEqual(len(inputs), 14)
        self.assertEqual(inputs[:5], ["-ss", "0.000000", "-t", "1.500000", "-i"])
        self.assertEqual(inputs[6:11], ["-ss", "2.000000", "-t", "1.000000", "-i"])
        self.assertEqual(inputs[5].casefold(), str(self.source).casefold())
        self.assertEqual(inputs[11].casefold(), str(self.source).casefold())
        self.assertIn("split=", graph)
        self.assertIn("xfade=", graph)
        self.assertIn("volume=0.35", graph)
        self.assertIn("hqdn3d=", graph)
        self.assertIn("scale=iw*2:ih*2:flags=lanczos", graph)
        self.assertGreaterEqual(graph.count("hqdn3d="), 4)

    def test_reused_picture_source_is_hashed_once_for_fingerprint(self):
        actual = model.sha256_file
        source_reads = []

        def count_source(path):
            if Path(path).resolve() == self.source.resolve():
                source_reads.append(path)
            return actual(path)

        with patch.object(model, "sha256_file", side_effect=count_source):
            digest = approval.fingerprint(self.timeline_path, self.timeline)
        self.assertEqual(len(source_reads), 1)
        self.assertEqual(len(digest), 64)

    def test_unapproved_and_stale_render_refused_before_output(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                cli.main(["render", "--timeline", str(self.timeline_path),
                          "--approval", str(self.root / "absent.json")])
        self.assertFalse(self.output.exists())
        approval_path = self._approved()
        edited = json.loads(self.timeline_path.read_text())
        edited["operations"][0]["end"] = 1.9
        self.timeline_path.write_text(json.dumps(edited), encoding="utf-8")
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                cli.main(["render", "--timeline", str(self.timeline_path),
                          "--approval", str(approval_path)])
        self.assertFalse(self.output.exists())

    def test_checklist_evidence_can_progress_after_timeline_approval(self):
        approved = self._approved()
        checklist = self.plan.with_name("checklist.json")
        contents = json.loads(checklist.read_text(encoding="utf-8"))
        contents["items"][0].update({"status": "done", "evidence": ["source reviewed"]})
        checklist.write_text(json.dumps(contents), encoding="utf-8")
        self.assertEqual(approval.require_human_approval(
            self.timeline_path, self.timeline, approved)["actor"], "human")

    def test_preview_allows_pending_review_without_final_approval(self):
        self.timeline["operations"][0]["review_status"] = "pending_review"
        self.timeline["audio"][0]["review_status"] = "pending_review"
        self.timeline_path.write_text(json.dumps(self.timeline), encoding="utf-8")
        candidate = self.root / "preview.mp4"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main([
                "preview", "--timeline", str(self.timeline_path),
                "--output", str(candidate), "--start", "0.4",
                "--duration", "0.8"]), 0)
        self.assertTrue(candidate.is_file())
        self.assertFalse(self.output.exists())
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                cli.main(["render", "--timeline", str(self.timeline_path),
                          "--approval", str(self.root / "absent.json")])

    def test_unsupported_method_refused_before_output(self):
        self.timeline["operations"].append(
            {"id": "ai", "method": "upscale-real-esrgan",
             "start": 0.5, "end": 1.0, "review_status": "approved"})
        with self.assertRaisesRegex(ValueError, "Unsupported timeline method"):
            model.validate(self.timeline)
        self.assertFalse(self.output.exists())

    def test_upscale_requires_a_larger_delivery_canvas(self):
        self.timeline["width"] = 160
        self.timeline["height"] = 90
        resolved = model.validate(self.timeline)
        with self.assertRaisesRegex(ValueError, "needs at least 2x"):
            compiler.compile_graph(self.timeline, resolved)
        self.assertFalse(self.output.exists())

    def test_hdr_source_is_refused_before_encoding(self):
        hdr = self.root / "hdr.mp4"
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10:duration=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-x264-params",
            "transfer=arib-std-b67:colorprim=bt2020:colormatrix=bt2020nc",
            str(hdr),
        ], capture_output=True, check=True)
        self.timeline["picture"][0]["source"] = hdr.name
        self.timeline["picture"][0]["sha256"] = model.sha256_file(hdr)
        resolved = model.validate(self.timeline)
        with self.assertRaisesRegex(ValueError, "explicit supported route"):
            compiler.compile_graph(self.timeline, resolved)
        self.assertFalse(self.output.exists())

    def test_missing_voice_asset_is_refused_before_encoding(self):
        self.timeline["audio"][0]["source"] = "missing.wav"
        with self.assertRaisesRegex(ValueError, "Missing or unsafe asset"):
            model.validate(self.timeline)
        self.assertFalse(self.output.exists())

    def test_hlg_audio_only_export_copies_picture_packets(self):
        # The supplied HDR picture must bypass every video filter and encoder.
        encoder = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                                 capture_output=True, text=True)
        if "libx265" not in encoder.stdout:
            self.skipTest("libx265 required for the HLG fixture")
        source = self.root / "hlg-source.mp4"
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10:duration=2",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:v", "libx265", "-pix_fmt", "yuv420p10le",
            "-x265-params", "colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:log-level=error",
            "-color_primaries", "bt2020", "-color_trc", "arib-std-b67",
            "-colorspace", "bt2020nc", "-c:a", "aac", "-shortest", str(source),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr[-800:])
        self.assertEqual(compiler.media_info(source)["video"].get("color_transfer"),
                         "arib-std-b67")
        self.timeline["picture"] = [{"id": "p1", "source": source.name,
                                      "sha256": model.sha256_file(source),
                                      "source_in": 0, "source_out": 2}]
        self.timeline["transitions"] = []
        self.timeline["operations"] = [{"id": "master", "method": "loudnorm",
                                        "start": 0, "end": 2,
                                        "review_status": "approved"}]
        self.timeline["audio"] = [{"id": "effect", "kind": "sfx",
                                   "source": self.voice.name,
                                   "sha256": model.sha256_file(self.voice),
                                   "start": .6, "gain": .25,
                                   "review_status": "approved"}]
        self.timeline.update({"video_policy": "copy_source",
                              "color_policy": "preserve", "width": 160,
                              "height": 90, "fps": 10})
        resolved = model.validate(self.timeline)
        record = compiler.render(self.timeline, resolved)
        self.assertEqual(record["video_encoder_invocations"], 0)
        self.assertIn(record["audio_analysis"]["decision"], {"SKIP", "FIX"})
        identity = compiler.verify_picture_copy(source, self.output)
        self.assertTrue(identity["video_packet_sha256"])
        self.assertEqual(compiler.media_info(self.output)["video"]["color_transfer"],
                         "arib-std-b67")
        # Listen by measurement: the 880 Hz fixture cue should appear at its
        # approved time while the 440 Hz source remains the natural bed.
        def cue_tone(at):
            raw = subprocess.run([
                "ffmpeg", "-v", "error", "-ss", str(at), "-t", "0.2",
                "-i", str(self.output), "-vn", "-ac", "1", "-ar", "8000",
                "-f", "f32le", "-"], capture_output=True, check=True).stdout
            samples = [value[0] for value in struct.iter_unpack("<f", raw)]
            real = sum(value * math.cos(2 * math.pi * 880 * n / 8000)
                       for n, value in enumerate(samples))
            imag = sum(value * math.sin(2 * math.pi * 880 * n / 8000)
                       for n, value in enumerate(samples))
            return math.hypot(real, imag) / len(samples)
        self.assertGreater(cue_tone(.7), cue_tone(.2) * 4)
        blocked = self.root / "blocked-hlg.mp4"
        self.timeline["output"] = str(blocked)
        with patch.object(compiler, "verify_picture_copy",
                          side_effect=ValueError("packet verification failed")):
            with self.assertRaisesRegex(ValueError, "packet verification failed"):
                compiler.render(self.timeline, model.validate(self.timeline))
        self.assertFalse(blocked.exists())
        self.timeline["operations"] = [{"id": "picture", "method": "crop",
                                        "start": 0, "end": 1, "x": 0,
                                        "y": 0, "w": 1, "h": 1,
                                        "review_status": "approved"}]
        with self.assertRaisesRegex(ValueError, "audio-only"):
            model.validate(self.timeline)

    def test_approved_render_creates_one_master_and_record(self):
        approval_path = self._approved()
        real_run = subprocess.run
        encodes = []

        def count_render(command, *args, **kwargs):
            if command[0] == "ffmpeg":
                encodes.append(command)
            return real_run(command, *args, **kwargs)

        with patch.object(compiler.subprocess, "run", side_effect=count_render):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main([
                    "render", "--timeline", str(self.timeline_path),
                    "--approval", str(approval_path)]), 0)
        self.assertEqual(len(encodes), 1)
        self.assertTrue(self.output.is_file())
        record_path = self.output.with_suffix(".mp4.render.json")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(record["video_encoder_invocations"], 1)
        self.assertEqual(record["audio_encoder_invocations"], 1)
        self.assertEqual(record["operations"],
                         ["lens", "crop", "denoise", "upscale", "title", "graphics"])
        self.assertAlmostEqual(record["duration"], 2.2, delta=0.15)
        evidence_dir = self.root / "final-review"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["verify", "--record", str(record_path),
                                       "--evidence-dir", str(evidence_dir)]), 0)
        manifest = json.loads((evidence_dir / "review-manifest.json").read_text())
        self.assertTrue(manifest["human_review_required"])
        self.assertEqual(manifest["master_inspection"]["output_sha256"],
                         record["output_sha256"])
        self.assertTrue(all(Path(guide["path"]).is_file()
                            for guide in manifest["master_inspection"]["safe_zone_guides"]))
        self.assertEqual(len(manifest["evidence"]), len(self.timeline["operations"]) + 1)
        denoise_samples = next(item["samples"] for item in manifest["evidence"]
                               if item["id"] == "denoise")
        self.assertEqual({sample["position"] for sample in denoise_samples},
                         {"before", "inside_start", "inside_end", "after"})
        self.assertTrue(all(Path(sample["frame"]).is_file()
                            for sample in denoise_samples))
        # The 880 Hz voice exists only after its approved timeline start.
        def tone_at(start):
            data = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", str(start), "-t", "0.2", "-i", str(self.output),
                "-vn", "-ac", "1", "-ar", "8000", "-f", "f32le", "-",
            ], capture_output=True, check=True).stdout
            samples = [sample[0] for sample in struct.iter_unpack("<f", data)]
            real = sum(value * math.cos(2 * math.pi * 880 * n / 8000)
                       for n, value in enumerate(samples))
            imag = sum(value * math.sin(2 * math.pi * 880 * n / 8000)
                       for n, value in enumerate(samples))
            return math.hypot(real, imag) / len(samples)
        self.assertGreater(tone_at(0.9), tone_at(0.2) * 4)
        altered = json.loads(approval_path.read_text())
        altered["review_note"] = "changed after render"
        approval_path.write_text(json.dumps(altered), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "approval record is missing or changed"):
            delivery_verify.verify_output(record_path)

    def test_color_range_changes_only_selected_frames(self):
        static = self.root / "static.mp4"
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=gray:s=64x64:r=10:d=2",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(static),
        ]
        subprocess.run(command, capture_output=True, check=True)
        self.timeline["picture"] = [{
            "id": "static", "source": static.name,
            "sha256": model.sha256_file(static),
            "source_in": 0, "source_out": 2,
        }]
        self.timeline["transitions"] = []
        self.timeline["audio"] = []
        self.timeline["width"] = 64
        self.timeline["height"] = 64
        self.timeline["operations"] = [{
            "id": "bright", "method": "color-eq",
            "brightness": 0.2, "start": 0.5, "end": 1.0,
            "review_status": "approved",
        }]
        self.timeline_path.write_text(json.dumps(self.timeline), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            cli.main(["render", "--timeline", str(self.timeline_path),
                      "--approval", str(self._approved())])

        def luma_at(start):
            data = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", str(start), "-i", str(self.output),
                "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-",
            ], capture_output=True, check=True).stdout
            return sum(data) / len(data)
        before, inside, after = (luma_at(t) for t in (0.2, 0.7, 1.3))
        self.assertGreater(inside, before + 25)
        self.assertAlmostEqual(after, before, delta=5)

    def test_caption_sidecar_uses_bound_font_in_one_export(self):
        black = self.root / "black.mp4"
        made = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=320x180:r=10:d=1.5",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1.5",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(black)], capture_output=True, text=True)
        self.assertEqual(made.returncode, 0, made.stderr[-500:])
        self.timeline["picture"] = [{"id": "black", "source": black.name,
                                     "sha256": model.sha256_file(black),
                                     "source_in": 0, "source_out": 1.5}]
        self.timeline["transitions"] = []
        self.timeline["audio"] = []
        self.timeline["operations"] = [{
            "id": "captions", "method": "motion-graphics-ass",
            "source": self.sidecar.name, "sha256": model.sha256_file(self.sidecar),
            "font_source": self.font.name, "font_sha256": model.sha256_file(self.font),
            "start": 0, "end": 1.5, "review_status": "approved"}]
        self.timeline["height"] = 180
        self.timeline["fps"] = 10
        compiler.render(self.timeline, model.validate(self.timeline))

        def luma(at):
            data = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(at),
                "-i", str(self.output), "-frames:v", "1", "-vf", "format=gray",
                "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
            return sum(data) / len(data)

        self.assertGreater(luma(.4), luma(.1) + .2)
        self.assertAlmostEqual(luma(.9), luma(.1), delta=1)

    def test_external_recorder_offset_is_mixed_once_on_manual_edit(self):
        self.timeline["picture"] = [{"id": "manual", "source": self.source.name,
                                     "sha256": model.sha256_file(self.source),
                                     "source_in": 0, "source_out": 3,
                                     "audio_gain": 0}]
        self.timeline["transitions"] = []
        self.timeline["operations"] = []
        report = self.root / "sync-report.json"
        report.write_text(json.dumps({
            "status": "REVIEW", "confidence": .9,
            "method": "rms-envelope-correlation-v1",
            "reference_sha256": model.sha256_file(self.source),
            "external_sha256": model.sha256_file(self.voice),
            "reference_duration_seconds": 3, "offset_seconds": .8,
            "drift_ppm": 1200}), encoding="utf-8")
        self.timeline["audio"] = [{
            "id": "mic", "kind": "external_sync", "source": self.voice.name,
            "sha256": model.sha256_file(self.voice), "sync_report_source": report.name,
            "sync_report_sha256": model.sha256_file(report), "start": 0,
            "offset_seconds": .8, "drift_ppm": 1200,
            "review_status": "approved"}]
        resolved = model.validate(self.timeline)
        _, graph = compiler.compile_graph(self.timeline, resolved)
        self.assertIn("atempo=0.99880000", graph)
        record = compiler.render(self.timeline, resolved)
        self.assertEqual(record["audio_encoder_invocations"], 1)

        def tone_at(start):
            decoded = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-i", str(self.output), "-ss", str(start), "-t", "0.2",
                "-vn", "-ac", "1",
                "-ar", "8000", "-f", "f32le", "-"],
                capture_output=True)
            self.assertEqual(decoded.returncode, 0, decoded.stderr[-500:])
            data = decoded.stdout
            samples = [item[0] for item in struct.iter_unpack("<f", data)]
            return abs(sum(value * complex(math.cos(2 * math.pi * 880 * n / 8000),
                                           math.sin(2 * math.pi * 880 * n / 8000))
                           for n, value in enumerate(samples))) / len(samples)

        self.assertGreater(tone_at(.9), tone_at(.2) * 8)

    def test_timed_audio_processing_stays_in_final_export(self):
        for clip in self.timeline["picture"]:
            clip["audio_gain"] = .05
        self.timeline["audio"][0]["gain"] = .1
        self.timeline["audio"].append({
            "id": "music", "kind": "music", "source": self.voice.name,
            "sha256": model.sha256_file(self.voice), "start": .1,
            "duration": 2, "loop": True, "gain": .05,
            "review_status": "approved"})
        self.timeline["operations"].extend([
            {"id": "highpass", "method": "highpass", "hz": 80,
             "start": 0.2, "end": 1.0, "review_status": "approved"},
            {"id": "cleanup", "method": "audio-denoise",
             "start": 0.2, "end": 1.0, "review_status": "approved"},
            {"id": "compression", "method": "compress",
             "start": 1.0, "end": 2.0, "review_status": "approved"},
            {"id": "master", "method": "loudnorm",
             "start": 0, "end": 2.2, "review_status": "approved"},
        ])
        self.timeline_path.write_text(json.dumps(self.timeline), encoding="utf-8")
        resolved = model.validate(self.timeline)
        _, graph = compiler.compile_graph(self.timeline, resolved)
        self.assertIn("highpass=", graph)
        self.assertIn("afftdn=", graph)
        self.assertIn("acompressor=", graph)
        self.assertIn("loudnorm=", graph)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main([
                "render", "--timeline", str(self.timeline_path),
                "--approval", str(self._approved())]), 0)
        self.assertTrue(self.output.is_file())
        record = self.output.with_suffix(".mp4.render.json")
        rendered = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(rendered["audio_analysis"]["decision"], "FIX")
        self.assertEqual(rendered["audio_encoder_invocations"], 1)
        with contextlib.redirect_stdout(io.StringIO()) as result:
            self.assertEqual(cli.main(["verify", "--record", str(record)]), 0)
        mastering = json.loads(result.getvalue())["mastering"]
        self.assertEqual(mastering["status"], "FIX")
        self.assertIn("integrated_lufs", mastering)
        self.assertAlmostEqual(mastering["integrated_lufs"], -16, delta=1)
        self.assertLessEqual(mastering["true_peak_dbtp"], -1.5)

    def test_already_acceptable_mix_skips_normalization_and_stays_acceptable(self):
        self.timeline["picture"] = [{"id": "p1", "source": self.source.name,
                                     "sha256": model.sha256_file(self.source),
                                     "source_in": 0, "source_out": 2,
                                     "audio_gain": 1.9}]
        self.timeline["transitions"] = []
        self.timeline["audio"] = []
        self.timeline["operations"] = [{"id": "master", "method": "loudnorm",
                                        "start": 0, "end": 2,
                                        "review_status": "approved"}]
        record = compiler.render(self.timeline, model.validate(self.timeline))
        self.assertEqual(record["audio_analysis"]["decision"], "SKIP")
        self.assertEqual(record["audio_encoder_invocations"], 1)
        inspection = delivery_verify._inspect_master(
            self.output, record["output_sha256"], None)
        mastering = delivery_verify._mastering_result(record["audio_analysis"],
                                                       inspection["loudness"])
        self.assertEqual(mastering["status"], "SKIP")

    def test_advertised_transition_adapters_render(self):
        for method in model.JOIN_TRANSITIONS:
            with self.subTest(mode="join", method=method):
                candidate = copy.deepcopy(self.timeline)
                candidate["operations"] = []
                candidate["audio"] = []
                candidate["transitions"][0]["id"] = method
                candidate["output"] = str(self.root / f"join-{method}.mp4")
                record = compiler.render(candidate, model.validate(candidate))
                self.assertTrue(Path(record["output"]).is_file())
                self.assertAlmostEqual(record["duration"], 2.2, delta=.15)
        for method in model.POINT_TRANSITIONS:
            with self.subTest(mode="point", method=method):
                candidate = copy.deepcopy(self.timeline)
                candidate["operations"] = [{
                    "id": "point", "method": method, "start": .5, "end": .9,
                    "review_status": "approved",
                }]
                candidate["audio"] = []
                candidate["transitions"] = []
                candidate["output"] = str(self.root / f"point-{method}.mp4")
                record = compiler.render(candidate, model.validate(candidate))
                self.assertTrue(Path(record["output"]).is_file())
                self.assertAlmostEqual(record["duration"], 2.5, delta=.15)

    def test_custom_join_and_point_effect_share_one_approved_export(self):
        source_hash = model.sha256_file(self.source)
        self.timeline["transitions"][0]["id"] = "page-turn"
        self.timeline["operations"] = [{
            "id": "glitch-beat", "method": "glitch-reveal",
            "start": .4, "end": .8, "review_status": "approved",
        }]
        self.timeline["audio"] = []
        self.timeline_path.write_text(json.dumps(self.timeline), encoding="utf-8")
        approved = self._approved()
        real_run = subprocess.run
        encodes = []

        def count_ffmpeg(command, *args, **kwargs):
            if command[0] == "ffmpeg":
                encodes.append(command)
            return real_run(command, *args, **kwargs)

        with patch.object(compiler.subprocess, "run", side_effect=count_ffmpeg):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main([
                    "render", "--timeline", str(self.timeline_path),
                    "--approval", str(approved)]), 0)
        self.assertEqual(len(encodes), 1)
        record_path = self.output.with_suffix(".mp4.render.json")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(record["video_encoder_invocations"], 1)
        self.assertEqual(record["audio_encoder_invocations"], 1)
        self.assertEqual(record["operations"], ["glitch-beat"])
        self.assertAlmostEqual(record["duration"], 2.2, delta=.15)
        self.assertEqual(model.sha256_file(self.source), source_hash)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["verify", "--record", str(record_path)]), 0)

    def test_full_source_audio_can_be_copied_without_encoding(self):
        self.timeline["picture"] = [{
            "id": "whole", "source": self.source.name,
            "sha256": model.sha256_file(self.source),
            "source_in": 0, "source_out": 3,
        }]
        self.timeline["transitions"] = []
        self.timeline["operations"] = [{
            "id": "graphic", "method": "motion-graphics-ass",
            "source": self.sidecar.name,
            "sha256": model.sha256_file(self.sidecar),
            "start": 0, "end": 3, "review_status": "approved",
        }, {
            "id": "slow-change", "method": "cross-blur",
            "start": 0.5, "end": 2.0, "blur_sigma": 55,
            "review_status": "approved",
        }]
        self.timeline["audio"] = []
        self.timeline["audio_policy"] = "copy_source"
        self.timeline["video_preset"] = "veryfast"
        resolved = model.validate(self.timeline)
        _, graph = compiler.compile_graph(self.timeline, resolved)
        self.assertNotIn("afinal", graph)
        self.assertIn("sendcmd=c='0.500000-1.250000", graph)
        self.assertIn("gblur@blur1 sigma 55*TI", graph)
        record = compiler.render(self.timeline, resolved)
        self.assertEqual(record["audio_encoder_invocations"], 0)
        self.assertAlmostEqual(record["duration"], 3, delta=.15)
        self.assertEqual(compiler.media_info(self.output)["audio"]["codec_name"], "aac")

        def packet_hash(path):
            result = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
                "-map", "0:a:0", "-c:a", "copy", "-f", "hash", "-hash", "SHA256", "-",
            ], capture_output=True, text=True, check=True)
            return result.stdout.strip()

        self.assertEqual(packet_hash(self.source), packet_hash(self.output))
        self.timeline["audio"].append({
            "id": "extra", "kind": "voice", "source": self.voice.name,
            "sha256": model.sha256_file(self.voice), "start": 0.5,
            "review_status": "approved",
        })
        with self.assertRaisesRegex(ValueError, "one uncut clip and no audio edits"):
            model.validate(self.timeline)
        self.timeline["audio"] = []
        self.timeline["operations"][1]["blur_sigma"] = 100
        with self.assertRaisesRegex(ValueError, "blur_sigma must be <= 80"):
            model.validate(self.timeline)


if __name__ == "__main__":
    unittest.main()
