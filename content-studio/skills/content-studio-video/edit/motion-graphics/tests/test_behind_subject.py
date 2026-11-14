import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

FOLDER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FOLDER / "scripts"))
sys.path.insert(0, str(FOLDER.parents[1] / "timeline" / "scripts"))
import behind_subject  # noqa: E402
import subject_matte  # noqa: E402
import compiler  # noqa: E402
import model  # noqa: E402


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required")
class BehindSubjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "shot.mp4"
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=160x90:r=10:d=1",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(self.source)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan_dir = self.root / "preflight"
        plan_dir.mkdir()
        plan = plan_dir / "plan.json"
        plan.write_text(json.dumps({"schema_version": 1, "kind": "edited",
                                    "stage": "edited-render", "steps": [{"id": "S01"}]}))
        plan_hash = model.sha256_file(plan)
        (plan_dir / "approval.json").write_text(json.dumps({
            "plan_sha256": plan_hash, "review_note": "fixture"}))
        (plan_dir / "checklist.json").write_text(json.dumps({
            "plan_sha256": plan_hash, "items": [{"id": "S01"}]}))
        self.timeline = model.make_initial(plan, self.source,
                                           self.root / "final.mp4",
                                           fps=10, width=160, height=90)
        self.timeline["picture"][0]["source_out"] = 1.0
        self.font = self.root / "font.ttf"
        shutil.copyfile(Path("C:/Windows/Fonts/arialbd.ttf"), self.font)
        self.mask = self.root / "mask.png"
        image = Image.new("L", (160, 90), 0)
        ImageDraw.Draw(image).rectangle((70, 0, 90, 89), fill=255)
        image.save(self.mask)

    def tearDown(self):
        self.temp.cleanup()

    def cue(self):
        return {"id": "place", "start": 0, "end": 1,
                "text": "MMMM", "font_source": self.font.name,
                "matte_source": self.mask.name, "from_y": .2, "to_y": .2,
                "font_height": .5, "rise_seconds": .2}

    def test_builds_reviewable_timeline_operation_and_rejects_changed_matte(self):
        changes = behind_subject.build_changes(self.timeline, [self.cue()])
        operation = changes["operations"][0]
        self.assertEqual(operation["review_status"], "pending_review")
        self.timeline.update(changes)
        model.validate(self.timeline, require_review=False)
        self.mask.write_bytes(self.mask.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "matte changed"):
            model.validate(self.timeline, require_review=False)

    def test_single_export_keeps_foreground_above_title(self):
        self.timeline.update(behind_subject.build_changes(self.timeline, [self.cue()]))
        resolved = model.validate(self.timeline, require_review=False)
        output = self.root / "preview.mp4"
        compiler.preview(self.timeline, resolved, output, 0, 1)
        frame = self.root / "frame.png"
        extraction = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", "0.5", "-i", str(output), "-frames:v", "1", str(frame)],
            capture_output=True, text=True)
        self.assertEqual(extraction.returncode, 0, extraction.stderr)
        rendered = Image.open(frame).convert("RGB")
        # White text must show on either side of the protected center strip.
        outside = [rendered.getpixel((x, y)) for x in range(10, 65)
                   for y in range(10, 70)]
        self.assertTrue(any(min(pixel) > 190 for pixel in outside))
        center = [rendered.getpixel((x, y)) for x in range(74, 87)
                  for y in range(10, 70)]
        self.assertLess(max(max(pixel) for pixel in center), 35)

    def test_two_shots_can_have_independent_titles_and_mattes(self):
        self.timeline["picture"].append({
            "id": "p2", "source": self.source.name,
            "sha256": model.sha256_file(self.source),
            "source_in": 0, "source_out": 1})
        second = {**self.cue(), "id": "place-2", "start": 1,
                  "end": 2, "text": "NEXT"}
        self.timeline.update(behind_subject.build_changes(
            self.timeline, [self.cue(), second]))
        resolved = model.validate(self.timeline, require_review=False)
        self.assertEqual(len(resolved["operations"]), 2)
        output = self.root / "two-shots.mp4"
        compiler.preview(self.timeline, resolved, output, 0, 2)
        self.assertTrue(output.is_file())

    def test_cue_cannot_cross_a_shot_boundary(self):
        self.timeline["picture"].append({
            "id": "p2", "source": self.source.name,
            "sha256": model.sha256_file(self.source),
            "source_in": 0, "source_out": 1})
        cue = {**self.cue(), "start": .5, "end": 1.5}
        with self.assertRaisesRegex(ValueError, "crosses shots"):
            behind_subject.build_changes(self.timeline, [cue])

    def test_local_polygon_matte_without_person_model(self):
        matte = self.root / "ridge.mp4"
        result = subject_matte.generate(
            self.source, matte, start=0, duration=.5, fps=10, width=160,
            polygon=[[0, .6], [1, .6], [1, 1], [0, 1]],
            include_person=False)
        self.assertEqual(result["frames"], 5)
        self.assertEqual(result["review_status"], "pending_moving_matte_review")
        self.assertTrue(matte.is_file())
        self.assertEqual(json.loads(matte.with_suffix(".json").read_text())
                         ["matte_sha256"], model.sha256_file(matte))
        cue = {**self.cue(), "matte_source": matte.name,
               "end": .5, "rise_seconds": .2}
        behind_subject.build_changes(self.timeline, [cue])
        record = json.loads(matte.with_suffix(".json").read_text())
        record["start"] = .1
        matte.with_suffix(".json").write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "provenance does not match"):
            behind_subject.build_changes(self.timeline, [cue])


if __name__ == "__main__":
    unittest.main()
