import importlib.util
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "captions.py"
SPEC = importlib.util.spec_from_file_location("content_studio_captions", SCRIPT)
captions = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(captions)


class CaptionSheetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "assets").mkdir()
        self.font = self.root / "assets" / "arial.ttf"
        shutil.copyfile("C:/Windows/Fonts/arial.ttf", self.font)
        self.sheet = self.root / "cues.json"
        self.sidecar = self.root / ".content-studio" / "captions" / "captions.ass"
        self.handoff = self.sidecar.with_name("handoff.json")
        self.data = {"width": 320, "height": 180, "duration_seconds": 1.5,
                     "font_name": "Arial", "font_source": "assets/arial.ttf",
                     "font_size": 12, "margin_bottom_fraction": .1,
                     "cues": [{"start": .3, "end": .7, "text": "First line"},
                              {"start": .8, "end": 1.2, "text": "Second line"}]}

    def tearDown(self):
        self.temp.cleanup()

    def test_unapproved_create_refuses_and_has_no_output(self):
        self.sheet.write_text(json.dumps(self.data), encoding="utf-8")
        with self.assertRaises((FileNotFoundError, ValueError)):
            captions.create(self.sheet, self.root, self.sidecar, self.handoff, self.root)
        self.assertFalse(self.sidecar.exists())

    def test_cues_have_exact_ass_times_and_hashed_pending_handoff(self):
        self.sheet.write_text(json.dumps(self.data), encoding="utf-8")
        with patch.object(captions, "_require_approved_preflight"):
            report = captions.create(self.sheet, self.root, self.sidecar, self.handoff,
                                     self.root)
        text = self.sidecar.read_text(encoding="utf-8")
        self.assertIn("Dialogue: 0,0:00:00.30,0:00:00.70", text)
        self.assertIn("Dialogue: 0,0:00:00.80,0:00:01.20", text)
        self.assertEqual(report["operation"]["review_status"], "pending_review")
        self.assertEqual(report["operation"]["font_sha256"], captions.sha256_file(self.font))
        self.assertEqual(report["operation"]["sha256"], captions.sha256_file(self.sidecar))
        self.assertEqual(json.loads(self.handoff.read_text())["operation"], report["operation"])
        self.assertEqual(report["operation"]["end"], 1.5)

    def test_current_approved_plan_with_caption_method_allows_create(self):
        preflight_path = SCRIPT.parents[4] / "content-studio-workflow" / "scripts" / "preflight.py"
        spec = importlib.util.spec_from_file_location("preflight_for_caption_test", preflight_path)
        preflight = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preflight)
        plan_dir = self.root / ".content-studio" / "preflight"
        plan_dir.mkdir(parents=True)
        steps = preflight.default_steps("edited", "edited-render")
        steps[1]["method_id"] = "captions-ass"
        plan = {"schema_version": 1, "kind": "edited", "stage": "edited-render",
                "goal": "Add requested captions", "inputs": ["manual.mp4"],
                "deliverables": ["captions.ass"], "steps": steps,
                "system_profile": {"capabilities": {"methods": {
                    "captions-ass": {"status": "available"}}}}}
        plan_path = plan_dir / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        digest = hashlib.sha256(plan_path.read_bytes()).hexdigest()
        (plan_dir / "approval.json").write_text(json.dumps({
            "plan_sha256": digest, "review_note": "Approved requested captions"}), encoding="utf-8")
        (plan_dir / "checklist.json").write_text(json.dumps({
            "plan_sha256": digest, "items": [{"id": step["id"]} for step in steps]}),
            encoding="utf-8")
        self.sheet.write_text(json.dumps(self.data), encoding="utf-8")
        report = captions.create(self.sheet, self.root, self.sidecar, self.handoff,
                                 self.root)
        self.assertEqual(report["operation"]["method"], "motion-graphics-ass")
        plan["steps"][1]["route"] = "Changed after approval"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "stale"):
            captions.create(self.sheet, self.root, self.sidecar, self.handoff, self.root)

    def test_overlap_and_text_overflow_refuse(self):
        self.data["cues"][1]["start"] = .6
        with self.assertRaisesRegex(ValueError, "overlaps"):
            captions.validate_sheet(self.data, self.root)
        self.data["cues"][1]["start"] = .8
        self.data["cues"][1]["text"] = "W" * 100
        with self.assertRaisesRegex(ValueError, "safe area"):
            captions.validate_sheet(self.data, self.root)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_bounded_preview_shows_text_only_during_cue(self):
        self.data["cues"] = [{"start": .3, "end": .8, "text": "VISIBLE"}]
        self.sheet.write_text(json.dumps(self.data), encoding="utf-8")
        with patch.object(captions, "_require_approved_preflight"):
            captions.create(self.sheet, self.root, self.sidecar, self.handoff, self.root)
        source = self.root / "black.mp4"
        made = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                               "-f", "lavfi", "-i", "color=c=black:s=320x180:r=10:d=1.5",
                               "-c:v", "libx264", str(source)], capture_output=True, text=True)
        self.assertEqual(made.returncode, 0, made.stderr[-500:])
        output = self.root / "preview.mp4"
        captions.preview(source, self.sidecar, self.font, output, 0, 1.2)

        def luma(at):
            frame = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                                    "-ss", str(at), "-i", str(output), "-frames:v", "1",
                                    "-vf", "format=gray", "-f", "rawvideo", "-"],
                                   capture_output=True, check=True).stdout
            return sum(frame) / len(frame)

        self.assertGreater(luma(.5), luma(.1) + .2)
        self.assertAlmostEqual(luma(1.0), luma(.1), delta=1)


if __name__ == "__main__":
    unittest.main()
