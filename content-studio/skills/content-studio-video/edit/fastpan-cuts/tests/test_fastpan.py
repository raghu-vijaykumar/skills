"""Behavioral tests for fast-pan review and timeline handoff."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import fastpan  # noqa: E402

TIMELINE_SCRIPTS = Path(__file__).resolve().parents[3] / "timeline" / "scripts"
sys.path.insert(0, str(TIMELINE_SCRIPTS))
import model  # noqa: E402


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required")
class FastPanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.mp4"
        self._make_video(self.source)

    def tearDown(self):
        self.temp.cleanup()

    def _make_video(self, output: Path, *, scene_cut: bool = False) -> None:
        # A textured fixed view, a two-second pan, then a fixed landing makes
        # the expected camera motion observable without private footage.
        rng = np.random.default_rng(1701)
        texture = rng.integers(12, 42, (180, 320), dtype=np.uint8)
        texture = np.clip(texture.astype(np.int16) + np.arange(320)[None, :] // 2,
                          0, 255).astype(np.uint8)
        texture[20:70, 20:65] = 235
        texture[70:145, 105:160] = 190
        texture[35:105, 215:285] = 225
        texture[::30, :] = 170
        alternate = rng.integers(10, 246, (180, 320), dtype=np.uint8)
        frames = []
        for index in range(8 * 30):
            if scene_cut:
                frame = texture if index < 90 else alternate
            else:
                offset = 0 if index < 60 else min((index - 60) * 2, 120)
                frame = np.roll(texture, offset, axis=1)
            frames.append(frame.tobytes())
        argv = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                "-f", "rawvideo", "-pixel_format", "gray", "-video_size", "320x180",
                "-framerate", "30", "-i", "pipe:0", "-f", "lavfi", "-i",
                "sine=frequency=440:sample_rate=48000:duration=8", "-shortest",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-y", str(output)]
        result = subprocess.run(argv, input=b"".join(frames), capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr[-500:])

    def _decisions(self, cuts: list[dict], *, approved: bool = False) -> Path:
        stat = self.source.stat()
        data = {"schema": fastpan.DECISION_SCHEMA, "source": str(self.source),
                "source_sha256": fastpan.sha256_file(self.source),
                "source_bytes": stat.st_size, "source_mtime_ns": stat.st_mtime_ns,
                "fps": 30, "cuts": cuts}
        if approved:
            data.update({"actor": "human", "reviewer": "fixture editor",
                         "review_note": "Reviewed exact synthetic cut and sound"})
        path = self.root / "decisions.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_scan_finds_sustained_pan_but_not_isolated_scene_cut(self):
        report = self.root / "scan.json"
        result = fastpan.scan(self.source, report)
        self.assertGreater(result["candidate_count"], 0)
        data = json.loads(report.read_text())
        self.assertEqual(data["source_sha256"], fastpan.sha256_file(self.source))
        self.assertTrue(any(row["start_s"] < 4 and row["end_s"] > 2
                            for row in data["candidates"]))
        self.assertTrue(all(row["review_status"] == "pending_review"
                            for row in data["candidates"]))
        cut_only = self.root / "scene-cut.mp4"
        self._make_video(cut_only, scene_cut=True)
        cut_report = self.root / "scene-cut.json"
        self.assertEqual(fastpan.scan(cut_only, cut_report)["candidate_count"], 0)

    def test_preview_cuts_picture_and_audio_to_matching_length(self):
        decisions = self._decisions([{"id": "p1", "start_frame": 60,
                                      "end_frame": 120, "review_status": "pending_review"}])
        output = self.root / "cut-preview.mp4"
        result = fastpan.preview(self.source, decisions, "p1", output)
        self.assertTrue(output.is_file())
        self.assertTrue(result["audio_cut_with_picture"])
        metadata = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                   "format=duration:stream=codec_type,duration", "-of", "json", str(output)],
                                  capture_output=True, text=True, check=True)
        data = json.loads(metadata.stdout)
        lengths = [float(stream["duration"]) for stream in data["streams"]
                   if stream["codec_type"] in {"video", "audio"}]
        self.assertEqual(len(lengths), 2)
        self.assertLessEqual(abs(lengths[0] - lengths[1]), 1 / 30 + 0.005)
        self.assertAlmostEqual(float(data["format"]["duration"]), 4, delta=0.1)

    def test_invalid_and_stale_cuts_are_rejected_before_preview(self):
        decisions = self._decisions([{"id": "bad", "start_frame": 60,
                                      "end_frame": 260, "review_status": "pending_review"}])
        output = self.root / "must-not-exist.mp4"
        with self.assertRaisesRegex(ValueError, "out-of-bounds"):
            fastpan.preview(self.source, decisions, "bad", output)
        self.assertFalse(output.exists())
        decisions = self._decisions([{"id": "a", "start_frame": 60,
                                      "end_frame": 90, "review_status": "pending_review"},
                                     {"id": "b", "start_frame": 91,
                                      "end_frame": 120, "review_status": "pending_review"}])
        with self.assertRaisesRegex(ValueError, "too-close"):
            fastpan.preview(self.source, decisions, "a", output)
        self.assertFalse(output.exists())
        os.utime(self.source, None)
        with self.assertRaisesRegex(ValueError, "modification time changed"):
            fastpan.preview(self.source, decisions, "a", output)

    def test_approved_changes_validate_on_native_timeline(self):
        decisions = self._decisions([{"id": "p1", "start_frame": 60,
                                      "end_frame": 120, "review_status": "approved"}], approved=True)
        plan = self.root / "plan.json"
        plan.write_text(json.dumps({"schema_version": 1, "kind": "edited",
                                    "stage": "edited-render", "goal": "test",
                                    "steps": [{"id": "S01"}]}), encoding="utf-8")
        digest = fastpan.sha256_file(plan)
        plan.with_name("approval.json").write_text(json.dumps({
            "plan_sha256": digest, "review_note": "fixture human plan approval"}), encoding="utf-8")
        plan.with_name("checklist.json").write_text(json.dumps({
            "plan_sha256": digest, "items": [{"id": "S01"}]}), encoding="utf-8")
        timeline = model.make_initial(plan, self.source, self.root / "final.mp4",
                                      fps=30, width=320, height=180)
        timeline_path = self.root / "timeline-v001.json"
        timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
        changes_path = self.root / "changes.json"
        result = fastpan.timeline_changes(self.source, decisions, timeline_path, changes_path)
        self.assertEqual(result["kept_clips"], 2)
        changes = json.loads(changes_path.read_text())
        self.assertEqual(changes["audio_policy"], "mix")
        self.assertEqual(changes["picture"][0]["source_out"], 2)
        self.assertEqual(changes["picture"][1]["source_in"], 4)
        revised = model.revise(timeline, changes, new_output=str(self.root / "final-v002.mp4"))
        self.assertAlmostEqual(model.validate(revised)["duration"], 6, delta=0.05)
        shortened = json.loads(timeline_path.read_text())
        shortened["picture"][0]["source_out"] = 6
        timeline_path.write_text(json.dumps(shortened), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "full uncut source"):
            fastpan.timeline_changes(self.source, decisions, timeline_path,
                                     self.root / "shortened-changes.json")
        decisions_data = json.loads(decisions.read_text())
        decisions_data["cuts"][0]["review_status"] = "pending_review"
        decisions.write_text(json.dumps(decisions_data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "lacks human review"):
            fastpan.timeline_changes(self.source, decisions, timeline_path,
                                     self.root / "unapproved-changes.json")
        timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
        decisions_data["cuts"][0]["review_status"] = "approved"
        decisions_data["source_sha256"] = "0" * 64
        decisions.write_text(json.dumps(decisions_data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SHA-256 changed"):
            fastpan.timeline_changes(self.source, decisions, timeline_path,
                                     self.root / "stale-hash-changes.json")


if __name__ == "__main__":
    unittest.main()
