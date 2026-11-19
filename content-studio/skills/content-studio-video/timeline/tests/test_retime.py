"""End-to-end retime fixtures through the native single-export timeline."""

import copy
from array import array
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "edit" / "retime" / "scripts"))
import approval  # noqa: E402
import compiler  # noqa: E402
import model  # noqa: E402
import retime  # noqa: E402
import verify as delivery_verify  # noqa: E402


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required")
class RetimeTests(unittest.TestCase):
    @staticmethod
    def luma_frames(path: Path) -> list[bytes]:
        raw = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                              "-i", str(path), "-map", "0:v:0", "-pix_fmt", "yuv420p",
                              "-f", "rawvideo", "-"], check=True, capture_output=True).stdout
        frame_size, luma_size = 160 * 90 * 3 // 2, 160 * 90
        return [raw[i:i + luma_size] for i in range(0, len(raw), frame_size)]

    @staticmethod
    def sampled_mae(left: bytes, right: bytes) -> float:
        positions = range(0, len(left), 8)
        return sum(abs(left[i] - right[i]) for i in positions) / len(positions)

    @staticmethod
    def audio_level(path: Path, start: float, end: float) -> float:
        raw = subprocess.run([
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(path), "-map", "0:a:0",
            "-af", f"atrim=start={start}:end={end}", "-ac", "1", "-ar", "48000",
            "-f", "s16le", "-"], check=True, capture_output=True).stdout
        values = array("h")
        values.frombytes(raw)
        return sum(abs(value) for value in values) / max(1, len(values))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = self.root / "preflight" / "plan.json"
        self.plan.parent.mkdir()
        self.plan.write_text(json.dumps({"schema_version": 1, "kind": "edited",
                                         "stage": "edited-render", "steps": [{"id": "S01"}]}))
        digest = model.sha256_file(self.plan)
        self.plan.with_name("approval.json").write_text(json.dumps(
            {"plan_sha256": digest, "review_note": "fixture approval", "actor": "human"}))
        self.plan.with_name("checklist.json").write_text(json.dumps(
            {"plan_sha256": digest, "items": [{"id": "S01"}]}))
        self.source = self.root / "source.mp4"
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10:duration=4",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=4",
            "-vf", "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-x264-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709",
            "-c:a", "aac", "-shortest", str(self.source),
        ], check=True, capture_output=True)
        self.voice = self.root / "voice.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                        "-f", "lavfi", "-i", "sine=frequency=880:duration=0.3",
                        str(self.voice)], check=True, capture_output=True)
        self.timeline_path = self.root / "timeline-v001.json"
        self.timeline = model.make_initial(self.plan, self.source,
                                           self.root / "final-v001.mp4",
                                           fps=10, width=160, height=90)
        self.timeline["picture"][0]["source_out"] = 4
        model.write_new(self.timeline_path, self.timeline)

    def tearDown(self):
        self.temp.cleanup()

    def proposed(self, method: str, first: float, last: float, **params):
        changes, report = retime.propose(
            self.timeline_path, "p0001", first, last,
            {"method": method, **params}, self.root / f"final-{method}.mp4")
        revised = model.revise(self.timeline, changes,
                               new_output=str(self.root / f"final-{method}.mp4"))
        # The fixture stands in for the separate human boundary review before
        # fingerprinting or rendering the new immutable revision.
        next(clip for clip in revised["picture"] if clip.get("retime"))[
            "retime_review_status"] = "approved"
        return revised, report

    def test_all_four_modes_render_one_export_with_expected_frames_and_sound(self):
        cases = [
            ("speed", 1, 2, {"factor": 0.5, "audio": "tempo"}, 5.0, "atempo="),
            ("freeze", 1, 1.1, {"hold_seconds": 0.5, "audio": "mute"}, 4.4, "tpad="),
            ("reverse", 1, 2, {"audio": "reverse"}, 4.0, "areverse"),
            ("loop", 1, 1.5, {"count": 3, "audio": "repeat"}, 5.0, "aloop="),
        ]
        for method, first, last, params, expected, filter_name in cases:
            with self.subTest(method=method):
                timeline, report = self.proposed(method, first, last, **params)
                resolved = model.validate(timeline)
                inputs, graph = compiler.compile_graph(timeline, resolved)
                self.assertIn(filter_name, graph)
                self.assertAlmostEqual(resolved["duration"], expected, places=3)
                self.assertEqual(report["human_preview_review"], "pending")
                # Exercise the actual single-export backend; approval is
                # separately enforced by timeline.py before a real render.
                result = compiler.render(timeline, resolved)
                output = resolved["output"]
                self.assertEqual(result["video_encoder_invocations"], 1)
                self.assertEqual(result["audio_encoder_invocations"], 1)
                self.assertAlmostEqual(result["duration"], expected, delta=.12)
                count = subprocess.run([
                    "ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-count_frames", "-show_entries", "stream=nb_read_frames",
                    "-of", "csv=p=0", str(output)], check=True,
                    capture_output=True, text=True).stdout.strip()
                self.assertEqual(int(count), round(expected * 10))
                original = self.luma_frames(self.source)
                delivered = self.luma_frames(output)
                expected_source = {
                    "speed": [10 + i // 2 for i in range(20)],
                    "freeze": [10] * 5,
                    "reverse": list(range(19, 9, -1)),
                    "loop": list(range(10, 15)) * 3,
                }[method]
                for offset, source_frame in enumerate(expected_source):
                    self.assertLess(self.sampled_mae(delivered[10 + offset],
                                                     original[source_frame]), 6,
                                    (method, offset, source_frame))
                level = self.audio_level(output, 1.15, 1.25)
                if method == "freeze":
                    self.assertLess(level, 50)
                else:
                    self.assertGreater(level, 200)

    def test_later_cues_shift_and_old_approval_becomes_stale(self):
        self.timeline["operations"] = [{"id": "look", "method": "color-eq",
                                        "start": 2.2, "end": 2.4,
                                        "review_status": "approved"}]
        self.timeline["audio"] = [{"id": "voice", "kind": "voice",
                                   "source": self.voice.name,
                                   "sha256": model.sha256_file(self.voice),
                                   "start": 2.6, "review_status": "approved"}]
        self.timeline_path.write_text(json.dumps(self.timeline))
        old = approval.fingerprint(self.timeline_path, self.timeline)
        revised, report = self.proposed("speed", 1, 2, factor=.5, audio="tempo")
        self.assertAlmostEqual(report["candidate"]["downstream_shift_seconds"], 1)
        self.assertAlmostEqual(revised["operations"][0]["start"], 3.2)
        self.assertAlmostEqual(revised["audio"][0]["start"], 3.6)
        path = self.root / "timeline-v002.json"
        model.write_new(path, revised)
        self.assertNotEqual(old, approval.fingerprint(path, revised))

    def test_guards_refuse_unbounded_loop_wrong_audio_and_overlapping_effect(self):
        for method, params, reason in (
            ("loop", {"count": 0, "audio": "repeat"}, "Loop needs"),
            ("speed", {"factor": .5, "audio": "reverse"}, "Speed needs"),
            ("freeze", {"hold_seconds": 1, "audio": "tempo"}, "Freeze needs"),
        ):
            with self.subTest(method=method):
                timeline = copy.deepcopy(self.timeline)
                timeline["picture"][0]["source_in"] = 1
                timeline["picture"][0]["source_out"] = 1.1 if method == "freeze" else 2
                timeline["picture"][0]["retime"] = {"method": method, **params}
                timeline["picture"][0]["retime_review_status"] = "approved"
                with self.assertRaisesRegex(ValueError, reason):
                    model.validate(timeline)
        self.timeline["operations"] = [{"id": "look", "method": "color-eq",
                                        "start": 1.2, "end": 1.4,
                                        "review_status": "approved"}]
        self.timeline_path.write_text(json.dumps(self.timeline))
        with self.assertRaisesRegex(ValueError, "overlaps retime"):
            self.proposed("speed", 1, 2, factor=.5, audio="tempo")

    def test_pending_retime_cannot_be_fingerprinted_for_delivery(self):
        changes, _ = retime.propose(self.timeline_path, "p0001", 1, 2,
                                    {"method": "speed", "factor": .5,
                                     "audio": "tempo"},
                                    self.root / "pending-final.mp4")
        pending = model.revise(self.timeline, changes,
                               new_output=str(self.root / "pending-final.mp4"))
        with self.assertRaisesRegex(ValueError, "lacks human motion and sound review"):
            model.validate(pending)

    def test_no_change_speed_records_skip_without_timeline_edit(self):
        changes, report = retime.propose(
            self.timeline_path, "p0001", 1, 2,
            {"method": "speed", "factor": 1, "audio": "tempo"},
            self.root / "unused.mp4")
        self.assertEqual(changes, {})
        self.assertEqual(report["status"], "SKIP")
        self.assertEqual(report["baseline"]["source_sha256"],
                         model.sha256_file(self.source))

    def test_hdr_and_variable_frame_timing_refuse_before_export(self):
        for name, filters, transfer, reason in (
            ("hdr", "setparams=color_primaries=bt709:color_trc=smpte2084:colorspace=bt709",
             "smpte2084", "SDR"),
            ("vfr", "setpts=if(gte(N\\,10)\\,PTS+0.2/TB\\,PTS),"
             "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709",
             "bt709", "frame"),
        ):
            with self.subTest(name=name):
                source = self.root / f"{name}.mp4"
                subprocess.run([
                    "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10:duration=4",
                    "-vf", filters, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-x264-params", f"colorprim=bt709:transfer={transfer}:colormatrix=bt709",
                    "-fps_mode", "passthrough", str(source)],
                    check=True, capture_output=True)
                timeline = copy.deepcopy(self.timeline)
                timeline["picture"][0].update(
                    source=source.name, sha256=model.sha256_file(source),
                    source_in=0, source_out=1,
                    retime={"method": "reverse", "audio": "mute"},
                    retime_review_status="approved")
                with self.assertRaisesRegex(ValueError, reason):
                    model.validate(timeline)

    def test_existing_caption_sidecar_must_be_regenerated(self):
        sidecar = self.root / "captions.ass"
        sidecar.write_text("[Script Info]\n", encoding="utf-8")
        self.timeline["operations"] = [{
            "id": "captions", "method": "motion-graphics-ass",
            "source": sidecar.name, "sha256": model.sha256_file(sidecar),
            "start": 0, "end": 4, "review_status": "approved"}]
        self.timeline_path.write_text(json.dumps(self.timeline))
        with self.assertRaisesRegex(ValueError, "regenerated timing"):
            self.proposed("speed", 1, 2, factor=.5, audio="tempo")

    def test_exact_master_records_retime_review_evidence(self):
        timeline, _ = self.proposed("freeze", 1, 1.1,
                                    hold_seconds=.5, audio="mute")
        path = self.root / "timeline-v002.json"
        model.write_new(path, timeline)
        fingerprint = approval.fingerprint(path, timeline)
        approved = self.root / "timeline-approval.json"
        approved.write_text(json.dumps({
            "actor": "human", "reviewer": "fixture editor",
            "review_note": "Reviewed retime fixture", "approved_at": "2026-11-19T00:00:00Z",
            "fingerprint": fingerprint}))
        record = compiler.render(timeline, model.validate(timeline))
        record.update({"timeline": str(path), "timeline_sha256": model.sha256_file(path),
                       "approval": str(approved), "approval_sha256": model.sha256_file(approved),
                       "approval_fingerprint": fingerprint,
                       "capability_sha256": approval.capability_sha256(),
                       "revision": timeline["revision"]})
        record_path = self.root / "render.json"
        model.write_new(record_path, record)
        verified = delivery_verify.verify_output(record_path,
                                                 self.root / "final-review")
        self.assertEqual(verified["retime_verification"]["expected_master_frames"], 44)
        self.assertEqual(verified["retime_verification"]["delivered_master_frames"], 44)
        self.assertEqual(verified["retime_verification"]["human_motion_and_sound_review"],
                         "pending")
        samples = next(item["samples"] for item in verified["evidence"]
                       if item.get("method") == "freeze")
        self.assertEqual(len(samples), 3)
        self.assertTrue(all(Path(item["frame"]).is_file() and
                            Path(item["audio"]).is_file() for item in samples))


if __name__ == "__main__":
    unittest.main()
