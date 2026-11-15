"""Synthetic behavior tests for tilt shortlisting and native timeline cuts."""

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
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tilt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "timeline" / "scripts"))
import model  # noqa: E402


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required")
class TiltTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.mp4"
        base = np.full((180, 320), 24, np.uint8)
        base[20:160:28, 10:310] = 245
        base[20:160, 10:310:35] = 245
        rotated = ndimage.rotate(base, 18, reshape=False, order=1, cval=24).astype(np.uint8)
        self.base, self.rotated = base, rotated
        frames = b"".join((rotated if 90 <= index < 180 else base).tobytes()
                          for index in range(9 * 30))
        argv = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                "-f", "rawvideo", "-pixel_format", "gray", "-video_size", "320x180",
                "-framerate", "30", "-i", "pipe:0", "-f", "lavfi", "-i",
                "sine=frequency=440:sample_rate=48000:duration=9", "-shortest",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-y", str(self.source)]
        result = subprocess.run(argv, input=frames, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr[-500:])

    def tearDown(self):
        self.temp.cleanup()

    def _decisions(self, *, approved: bool = False) -> Path:
        stat = self.source.stat()
        data = {"schema": tilt.DECISION_SCHEMA, "source": str(self.source),
                "source_sha256": tilt.fastpan.sha256_file(self.source),
                "source_bytes": stat.st_size, "source_mtime_ns": stat.st_mtime_ns,
                "fps": 30, "threshold_deg": 10,
                "cuts": [{"id": "tilt-1", "start_frame": 90, "end_frame": 180,
                          "review_status": "approved" if approved else "pending_review"}]}
        if approved:
            data.update({"actor": "human", "reviewer": "fixture editor",
                         "review_note": "Reviewed synthetic camera-roll interval and join"})
        path = self.root / "decisions.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_scan_threshold_and_review_state(self):
        self.assertLess(abs(tilt.estimate_roll(self.base)[0]), 3)
        self.assertGreater(abs(tilt.estimate_roll(self.rotated)[0]), 10)
        report = self.root / "scan.json"
        result = tilt.scan(self.source, report, threshold_deg=10)
        self.assertGreater(result["candidate_count"], 0)
        data = json.loads(report.read_text())
        self.assertEqual(data["source_sha256"], tilt.fastpan.sha256_file(self.source))
        self.assertTrue(all(row["review_status"] == "pending_visual_review"
                            for row in data["candidates"]))
        self.assertTrue(any(row["start_s"] <= 3 and row["end_s"] >= 5
                            for row in data["candidates"]))
        self.assertEqual(tilt.group_candidates(data["samples"], threshold_deg=30,
                                                sample_fps=1, fps=30, duration=9), [])

    def test_join_preview_matches_picture_and_audio(self):
        decisions = self._decisions()
        output = self.root / "join.mp4"
        result = tilt.preview(self.source, decisions, "tilt-1", output)
        self.assertTrue(result["audio_cut_with_picture"])
        metadata = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                   "stream=codec_type,duration", "-of", "json", str(output)],
                                  capture_output=True, text=True, check=True)
        streams = json.loads(metadata.stdout)["streams"]
        lengths = [float(item["duration"]) for item in streams]
        self.assertEqual(len(lengths), 2)
        self.assertLessEqual(abs(lengths[0] - lengths[1]), 1 / 30 + .01)
        self.assertAlmostEqual(lengths[0], 4, delta=.1)
        os.utime(self.source, None)
        with self.assertRaisesRegex(ValueError, "modification time changed"):
            tilt.preview(self.source, decisions, "tilt-1", self.root / "stale.mp4")

    def test_human_approval_and_timeline_handoff(self):
        decisions = self._decisions()
        plan = self.root / "plan.json"
        plan.write_text(json.dumps({"schema_version": 1, "kind": "edited",
                                    "stage": "edited-render", "goal": "test",
                                    "steps": [{"id": "S01"}]}), encoding="utf-8")
        digest = tilt.fastpan.sha256_file(plan)
        plan.with_name("approval.json").write_text(json.dumps({
            "plan_sha256": digest, "review_note": "fixture plan approval"}), encoding="utf-8")
        plan.with_name("checklist.json").write_text(json.dumps({
            "plan_sha256": digest, "items": [{"id": "S01"}]}), encoding="utf-8")
        timeline = model.make_initial(plan, self.source, self.root / "final.mp4",
                                      fps=30, width=320, height=180)
        timeline_file = self.root / "timeline.json"
        timeline_file.write_text(json.dumps(timeline), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "lacks human review"):
            tilt.timeline_changes(self.source, decisions, timeline_file,
                                  self.root / "unapproved.json")
        self._decisions(approved=True)
        changes_file = self.root / "changes.json"
        result = tilt.timeline_changes(self.source, decisions, timeline_file,
                                       changes_file)
        self.assertEqual(result["kept_clips"], 2)
        changes = json.loads(changes_file.read_text())
        self.assertEqual(changes["audio_policy"], "mix")
        self.assertTrue(changes["picture"][0]["id"].startswith("tilt-keep-"))
        revised = model.revise(timeline, changes,
                               new_output=str(self.root / "final-v002.mp4"))
        self.assertAlmostEqual(model.validate(revised)["duration"], 6, delta=.05)


if __name__ == "__main__":
    unittest.main()
