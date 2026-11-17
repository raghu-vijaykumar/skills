"""The picture evidence gate must cover every cue and bind exact revisions."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "scene_review.py"
spec = importlib.util.spec_from_file_location("scene_review", SOURCE)
scene_review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scene_review)


class SceneReviewTests(unittest.TestCase):
    def test_prepares_boundary_frames_then_requires_visual_decisions(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            video = root / "picture.mp4"
            subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                 "-i", "testsrc=size=160x90:rate=5:duration=8", "-c:v", "mpeg4", str(video)],
                check=True, capture_output=True,
            )
            script = {"segments": [
                {"id": "a", "start": 0, "end": 4, "text": "First scene"},
                {"id": "b", "start": 4, "end": 8, "text": "Second scene"},
            ]}
            script_path = root / "script.json"
            script_path.write_text(json.dumps(script), encoding="utf-8")
            out = root / "review"
            review = scene_review.generate(video, script_path, out, width=160)
            self.assertEqual(len(review["cue_sheets"]), 1)
            self.assertEqual([item["role"] for item in review["cues"][0]["frames"]],
                             ["before", "start", "middle", "end", "after"])
            self.assertTrue((out / review["cue_sheets"][0]).is_file())
            self.assertIn("First scene", (out / "scene-review.md").read_text(encoding="utf-8"))
            self.assertTrue(scene_review.validate(review, script, scene_review.sha256(script_path),
                                                  scene_review.sha256(video)))

            for cue in review["cues"]:
                cue.update(visual_start=cue["start"], visual_end=cue["end"],
                           visual_description="Reviewed test pattern", scene_match="match")
            self.assertEqual(scene_review.validate(review, script, scene_review.sha256(script_path),
                                                   scene_review.sha256(video), out), [])

            review["cues"][1]["visual_end"] = 7.5
            self.assertTrue(any("exceeds reviewed visual bounds" in error for error in
                                scene_review.validate(review, script)))
            review["cues"][1]["visual_end"] = 8
            altered = {"segments": [script["segments"][0]]}
            self.assertTrue(any("cover every" in error for error in
                                scene_review.validate(review, altered)))
            self.assertTrue(any("exact picture" in error for error in
                                scene_review.validate(review, script, picture_sha256="wrong")))
            self.assertTrue(any("exact narration script" in error for error in
                                scene_review.validate(review, script, script_sha256="wrong")))
            (out / review["cues"][0]["frames"][0]["path"]).unlink()
            self.assertTrue(any("missing or unsafe frame" in error for error in
                                scene_review.validate(review, script, review_root=out)))


if __name__ == "__main__":
    unittest.main()
