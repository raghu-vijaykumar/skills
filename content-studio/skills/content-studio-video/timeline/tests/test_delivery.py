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
        changes.write_text(json.dumps({"operations": [{
            "id": "draft-look", "method": "color-eq",
            "start": 0.2, "end": 0.5, "brightness": 0.02,
            "review_status": "pending_review",
        }]}), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main([
                "revise", "--timeline", str(initial),
                "--changes", str(changes), "--out", str(revised),
                "--output", str(self.root / "cli-final-v002.mp4")]), 0)
        self.assertEqual(model.load(initial)["revision"], 1)
        self.assertEqual(model.load(revised)["revision"], 2)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["validate", "--timeline", str(revised)]), 0)

    def test_ranges_resolve_after_cut_and_overlap(self):
        resolved = model.validate(self.timeline)
        self.assertAlmostEqual(resolved["duration"], 2.2)
        self.assertAlmostEqual(resolved["clips"][1]["start"], 1.2)
        inputs, graph = compiler.compile_graph(self.timeline, resolved)
        self.assertEqual(len(inputs), 6)
        self.assertIn("split=", graph)
        self.assertIn("xfade=", graph)
        self.assertIn("volume=0.35", graph)
        self.assertIn("hqdn3d=", graph)
        self.assertIn("scale=iw*2:ih*2:flags=lanczos", graph)
        self.assertGreaterEqual(graph.count("hqdn3d="), 4)

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

    def test_timed_audio_processing_stays_in_final_export(self):
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
        with contextlib.redirect_stdout(io.StringIO()) as result:
            self.assertEqual(cli.main(["verify", "--record", str(record)]), 0)
        mastering = json.loads(result.getvalue())["mastering"]
        self.assertIn(mastering["status"], {"FIX", "REVIEW"})
        self.assertIn("integrated_lufs", mastering)

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


if __name__ == "__main__":
    unittest.main()
