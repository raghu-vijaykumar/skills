"""Behavioral tests for hero-led range selection and portrait delivery."""

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

from PIL import Image
import numpy as np

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL / "previews"))
sys.path.insert(0, str(SKILL.parents[1] / "timeline" / "scripts"))
import clipping  # noqa: E402
import build_real_demo  # noqa: E402
import approval  # noqa: E402
import compiler  # noqa: E402
import model  # noqa: E402
import timeline  # noqa: E402


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required")
class ClippingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "long-form.mp4"
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=blue:s=160x90:r=10:d=4",
            "-f", "lavfi", "-i", "sine=frequency=220:duration=1",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-f", "lavfi", "-i", "sine=frequency=880:duration=1",
            "-f", "lavfi", "-i", "sine=frequency=1100:duration=1",
            "-filter_complex", "[1:a][2:a][3:a][4:a]concat=n=4:v=0:a=1[a]",
            "-map", "0:v", "-map", "[a]",
            "-vf", "drawbox=x=102:y=15:w=28:h=60:color=red:t=fill,"
                   "drawbox=x=10:y=15:w=28:h=60:color=lime:t=fill",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(self.source),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr[-700:])
        self.selection = self.root / ".content-studio" / "clipping" / "selection-v001.json"
        self.crop_selection = self.selection.with_name("selection-v002.json")
        self.boxes = self.root / "hero-boxes.json"
        self.boxes.write_text(json.dumps({"subjects": [{
            "source": self.source.name, "start": 1, "end": 3,
            "box": {"x": 0.64, "y": 0.2, "w": 0.18, "h": 0.6},
            "confidence": 0.99, "label": "red hero",
        }]}), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def _inspect_and_crop(self):
        clipping.inspect_source(self.source, self.selection, "red hero object",
                                start=1, end=3, interval=0.5)
        clipping.propose_crop(self.selection, self.crop_selection,
                              self.root / ".content-studio" / "clipping" / "crop-v001",
                              method="subjects", subjects=self.boxes, size="90x160")
        return json.loads(self.crop_selection.read_text(encoding="utf-8"))

    def _review_selection(self):
        record = self._inspect_and_crop()
        record["editorial_review"] = {
            "status": "approved", "reviewer": "fixture editor",
            "note": "Complete hero action and source sound reviewed"}
        record["crop_intervals"][0]["review_status"] = "approved"
        record["crop_intervals"][0]["review_note"] = "Hero visible throughout"
        record["status"] = "reviewed"
        self.crop_selection.write_text(json.dumps(record), encoding="utf-8")
        return record

    def _timeline(self, method="reviewed-hero-range"):
        plan = self.root / "preflight" / "plan.json"
        plan.parent.mkdir(exist_ok=True)
        plan.write_text(json.dumps({
            "schema_version": 1, "kind": "edited", "stage": "edited-render",
            "steps": [{"id": "S01", "route": "content-studio-video-clipping",
                       "method_id": method}],
        }), encoding="utf-8")
        digest = model.sha256_file(plan)
        plan.with_name("approval.json").write_text(json.dumps({
            "actor": "human", "plan_sha256": digest,
            "review_note": "Fixture production plan approved"}), encoding="utf-8")
        plan.with_name("checklist.json").write_text(json.dumps({
            "plan_sha256": digest, "items": [{"id": "S01"}]}), encoding="utf-8")
        path = self.root / "timeline-v001.json"
        base = model.make_initial(plan, self.source, self.root / "full.mp4",
                                  fps=10, width=90, height=160)
        base["picture"][0]["source_out"] = 4
        model.write_new(path, base)
        return path, base

    def test_inspect_creates_source_linked_evidence_and_crop_proposal(self):
        source_hash = model.sha256_file(self.source)
        record = self._inspect_and_crop()
        self.assertEqual(record["source"]["sha256"], source_hash)
        self.assertEqual(record["selected"], {"source_in": 1.0, "source_out": 3.0})
        self.assertTrue(record["evidence"]["frame_ids"])
        self.assertTrue((self.selection.parent / record["evidence"]["manifest"]).is_file())
        interval = record["crop_intervals"][0]
        self.assertEqual(interval["method"], "subjects")
        self.assertTrue((self.crop_selection.parent / interval["proposal_file"]).is_file())
        framing = json.loads((self.crop_selection.parent / interval["framing_file"]).read_text())
        self.assertEqual(framing["source_sha256"], source_hash)
        self.assertTrue(framing["guide_frames"])
        self.assertIsNotNone(framing["minimum_hero_coverage"])
        self.assertEqual(clipping.validate_selection(self.crop_selection)["status"],
                         "pending_review")
        with self.assertRaisesRegex(ValueError, "review"):
            clipping.validate_selection(self.crop_selection, ready=True)
        self.assertEqual(model.sha256_file(self.source), source_hash)

    def test_wide_hero_box_reports_crop_loss_for_review(self):
        self.boxes.write_text(json.dumps({"subjects": [{
            "source": self.source.name, "start": 1, "end": 3,
            "box": {"x": .2, "y": .2, "w": .6, "h": .6},
            "confidence": .99, "label": "wide hero"}]}), encoding="utf-8")
        record = self._inspect_and_crop()
        interval = record["crop_intervals"][0]
        framing_path = self.crop_selection.parent / interval["framing_file"]
        framing = json.loads(framing_path.read_text(encoding="utf-8"))
        self.assertEqual(framing["hero_coverage_status"], "REVIEW")
        self.assertLess(framing["minimum_hero_coverage"], .98)
        self.assertGreater(framing["context_lost_fraction"], .5)
        guide = Path(framing["guide_frames"][0]["path"])
        guide.write_bytes(b"changed guide")
        with self.assertRaisesRegex(ValueError, "guide changed"):
            clipping.validate_selection(self.crop_selection)

    def test_separate_hero_boxes_expose_a_subject_lost_by_portrait_crop(self):
        self.boxes.write_text(json.dumps({"subjects": [
            {"source": self.source.name, "start": 1, "end": 3,
             "box": {"x": .64, "y": .2, "w": .18, "h": .6},
             "confidence": .99, "label": "red hero"},
            {"source": self.source.name, "start": 1, "end": 3,
             "box": {"x": .06, "y": .2, "w": .18, "h": .6},
             "confidence": .8, "label": "green hero"},
        ]}), encoding="utf-8")
        record = self._inspect_and_crop()
        interval = record["crop_intervals"][0]
        framing = json.loads((self.crop_selection.parent /
                              interval["framing_file"]).read_text(encoding="utf-8"))
        samples = framing["subject_samples"]
        self.assertEqual({item.get("label") for item in samples},
                         {"red hero", "green hero"})
        self.assertEqual(framing["hero_coverage_status"], "REVIEW")
        self.assertEqual(framing["minimum_hero_coverage"], 0)
        self.assertTrue(any(item["label"] == "green hero" and item["status"] == "REVIEW"
                            for item in samples))

    def test_readme_gif_builder_requires_an_approved_full_render_record(self):
        self._review_selection()
        with self.assertRaisesRegex(ValueError, "full-render record is missing"):
            build_real_demo.build(self.source, self.source, self.crop_selection,
                                  self.root / "readme-gifs")
        self.assertFalse((self.root / "readme-gifs").exists())

    def test_full_source_discovery_leaves_range_for_editor(self):
        record = clipping.inspect_source(self.source, self.selection,
                                         "red hero object", interval=1)
        self.assertIsNone(record["selected"])
        self.assertGreaterEqual(len(record["evidence"]["frame_ids"]), 3)
        self.assertEqual(clipping.validate_selection(self.selection)["status"],
                         "pending_review")
        with self.assertRaisesRegex(ValueError, "review"):
            clipping.validate_selection(self.selection, ready=True)
        denser = self.selection.with_name("selection-v002.json")
        narrowed = clipping.inspect_source(self.source, denser, "red hero object",
                                           start=1, end=3, interval=0.5)
        self.assertEqual(narrowed["selected"], {"source_in": 1.0, "source_out": 3.0})
        self.assertNotEqual(record["evidence"]["manifest"],
                            narrowed["evidence"]["manifest"])

    def test_missing_subject_does_not_fall_back_to_saliency(self):
        clipping.inspect_source(self.source, self.selection, "red hero",
                                start=1, end=3, interval=0.5)
        self.boxes.write_text('{"subjects": []}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "subject"):
            clipping.propose_crop(self.selection, self.crop_selection,
                                  self.root / "crop", method="subjects",
                                  subjects=self.boxes, size="90x160")
        self.assertFalse(self.crop_selection.exists())

    def test_invalid_or_changed_selection_cannot_emit(self):
        record = self._review_selection()
        timeline_path, _ = self._timeline()
        original_width = record["crop_intervals"][0]["w"]
        record["crop_intervals"][0]["w"] = 0.4
        self.crop_selection.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "aspect"):
            clipping.emit_changes(self.crop_selection, timeline_path,
                                  self.root / "invalid.json")
        record["crop_intervals"][0]["w"] = original_width
        record["crop_intervals"][0]["x"] += 0.01
        self.crop_selection.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "geometry"):
            clipping.emit_changes(self.crop_selection, timeline_path,
                                  self.root / "invalid.json")
        record["crop_intervals"][0]["x"] -= 0.01
        record["crop_intervals"][0]["source_out"] = 2.5
        self.crop_selection.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cover"):
            clipping.emit_changes(self.crop_selection, timeline_path,
                                  self.root / "invalid.json")
        record["crop_intervals"][0]["source_out"] = 3
        record["source"]["sha256"] = "0" * 64
        self.crop_selection.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed"):
            clipping.emit_changes(self.crop_selection, timeline_path,
                                  self.root / "invalid.json")
        self.assertFalse((self.root / "invalid.json").exists())

    def test_adjacent_crop_intervals_keep_one_contiguous_source_range(self):
        moving_source = self.root / "moving-hero.mp4"
        fixture = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=blue:s=160x90:r=10:d=2",
            "-f", "lavfi", "-i", "color=c=blue:s=160x90:r=10:d=2",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
            "-filter_complex", "[0:v]drawbox=x=102:y=15:w=28:h=60:color=red:t=fill[v0];"
                               "[1:v]drawbox=x=10:y=15:w=28:h=60:color=red:t=fill[v1];"
                               "[v0][v1]concat=n=2:v=1:a=0[v]",
            "-map", "[v]", "-map", "2:a", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(moving_source),
        ], capture_output=True, text=True)
        self.assertEqual(fixture.returncode, 0, fixture.stderr[-700:])
        self.source = moving_source
        self.boxes.write_text(json.dumps({"subjects": [
            {"source": self.source.name, "start": 1, "end": 1.999,
             "box": {"x": 0.64, "y": 0.2, "w": 0.18, "h": 0.6},
             "confidence": 0.99, "label": "red hero right"},
            {"source": self.source.name, "start": 2, "end": 3,
             "box": {"x": 0.08, "y": 0.2, "w": 0.18, "h": 0.6},
             "confidence": 0.99, "label": "red hero left"},
        ]}), encoding="utf-8")
        clipping.inspect_source(self.source, self.selection, "red hero",
                                start=1, end=3, interval=0.5)
        clipping.propose_crop(self.selection, self.crop_selection,
                              self.root / "crop-first", method="subjects",
                              subjects=self.boxes, size="90x160", start=1, end=2)
        third = self.selection.with_name("selection-v003.json")
        clipping.propose_crop(self.crop_selection, third, self.root / "crop-second",
                              method="subjects", subjects=self.boxes,
                              size="90x160", start=2, end=3)
        record = json.loads(third.read_text(encoding="utf-8"))
        record["status"] = "reviewed"
        record["editorial_review"] = {
            "status": "approved", "reviewer": "fixture editor",
            "note": "Both adjoining crop intervals reviewed with source audio"}
        for item in record["crop_intervals"]:
            item["review_status"] = "approved"
            item["review_note"] = "Hero and cut point reviewed"
        self.assertEqual(len(record["crop_boundaries"]), 1)
        self.assertEqual(record["crop_boundaries"][0]["candidate_status"], "REVIEW")
        self.assertGreater(record["crop_boundaries"][0]["screen_jump_fraction"], .5)
        third.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "boundary needs human review"):
            clipping.validate_selection(third, ready=True)
        for boundary in record["crop_boundaries"]:
            boundary["review_status"] = "approved"
            boundary["review_note"] = "Visible hard reframing reviewed"
        third.write_text(json.dumps(record), encoding="utf-8")
        timeline_path, base = self._timeline()
        changes = clipping.emit_changes(third, timeline_path,
                                        self.root / "two-crops.json")
        self.assertEqual([(item["source_in"], item["source_out"])
                          for item in changes["picture"]], [(1, 2), (2, 3)])
        self.assertEqual([(item["start"], item["end"])
                          for item in changes["operations"]], [(0, 1), (1, 2)])
        self.assertGreater(abs(changes["operations"][0]["x"] -
                               changes["operations"][1]["x"]), 0.4)
        for item in changes["operations"]:
            item["review_status"] = "approved"
        revision = model.revise(base, changes,
                                new_output=str(self.root / "two-crops.mp4"))
        resolved = model.validate(revision)
        rendered = compiler.render(revision, resolved)
        self.assertEqual(rendered["video_encoder_invocations"], 1)
        self.assertEqual(rendered["audio_encoder_invocations"], 1)
        self.assertAlmostEqual(compiler.media_info(self.root / "two-crops.mp4")["duration"],
                               2, delta=0.12)
        for index, at in enumerate((0.5, 1.5)):
            still = self.root / f"moving-{index}.png"
            frame = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", str(at), "-i", str(self.root / "two-crops.mp4"),
                "-frames:v", "1", str(still),
            ], capture_output=True, text=True)
            self.assertEqual(frame.returncode, 0, frame.stderr[-700:])
            with Image.open(still) as image:
                red = image.convert("RGB").getpixel((45, 80))
            self.assertGreater(red[0], red[1] * 1.5)
            self.assertGreater(red[0], red[2] * 1.5)

    def test_hdr_is_rejected_before_contact_sheet_creation(self):
        metadata = compiler.media_info(self.source)
        metadata["video"] = {**metadata["video"], "color_transfer": "arib-std-b67"}
        with patch.object(clipping, "media_info", return_value=metadata):
            with self.assertRaisesRegex(ValueError, "HDR"):
                clipping.inspect_source(self.source, self.selection, "hero",
                                        start=1, end=3)
        self.assertFalse(self.selection.exists())

    def test_approved_plan_must_name_the_clipping_method(self):
        self._review_selection()
        timeline_path, _ = self._timeline(method="different-method")
        with self.assertRaisesRegex(ValueError, "preflight plan lacks"):
            clipping.emit_changes(self.crop_selection, timeline_path,
                                  self.root / "unplanned.json")
        self.assertFalse((self.root / "unplanned.json").exists())

    def test_timeline_handoff_renders_selected_hero_and_source_audio(self):
        self._review_selection()
        timeline_path, base = self._timeline()
        changes_path = self.root / "changes.json"
        changes = clipping.emit_changes(self.crop_selection, timeline_path,
                                        changes_path)
        self.assertEqual(changes["picture"][0]["source_in"], 1)
        self.assertEqual(changes["picture"][0]["source_out"], 3)
        self.assertEqual(changes["operations"][0]["review_status"], "pending_review")
        self.assertEqual(changes["operations"][0]["clip_selection_sha256"],
                         model.sha256_file(self.crop_selection))
        revision = model.revise(base, changes,
                                new_output=str(self.root / "review.mp4"))
        self.assertAlmostEqual(model.validate(revision, require_review=False)["duration"], 2)
        framing_path = Path(revision["operations"][0]["clip_framing_file"])
        original_framing = framing_path.read_bytes()
        framing_path.write_bytes(original_framing + b"changed")
        with self.assertRaisesRegex(ValueError, "framing evidence changed"):
            model.validate(revision, require_review=False)
        framing_path.write_bytes(original_framing)
        incomplete = json.loads(json.dumps(revision))
        del incomplete["operations"][0]["clip_manifest_file"]
        del incomplete["operations"][0]["clip_manifest_sha256"]
        with self.assertRaisesRegex(ValueError, "all evidence bindings"):
            model.validate(incomplete, require_review=False)
        with self.assertRaisesRegex(ValueError, "human review"):
            model.validate(revision)
        revision["operations"][0]["review_status"] = "approved"
        final_path = self.root / "timeline-v002.json"
        model.write_new(final_path, revision)
        fingerprint = approval.fingerprint(final_path, revision)
        approval_file = self.root / "timeline-approval.json"
        approval_file.write_text(json.dumps({
            "actor": "human", "reviewer": "fixture editor",
            "review_note": "Fixture range and crop reviewed",
            "approved_at": "2026-11-19T12:00:00+05:30",
            "fingerprint": fingerprint,
        }), encoding="utf-8")
        source_hash = model.sha256_file(self.source)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(timeline.main(["render", "--timeline", str(final_path),
                                            "--approval", str(approval_file)]), 0)
        output = self.root / "review.mp4"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(timeline.main([
                "verify", "--record", str(output.with_suffix(".mp4.render.json")),
                "--evidence-dir", str(self.root / "final-review")]), 0)
        info = compiler.media_info(output)
        self.assertEqual((info["video"]["width"], info["video"]["height"]), (90, 160))
        self.assertIsNotNone(info["audio"])
        self.assertAlmostEqual(info["duration"], 2, delta=0.12)
        still = self.root / "still.png"
        frame = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", "0.5", "-i", str(output), "-frames:v", "1", str(still),
        ], capture_output=True, text=True)
        self.assertEqual(frame.returncode, 0, frame.stderr[-700:])
        with Image.open(still) as image:
            red = image.convert("RGB").getpixel((45, 80))
        self.assertGreater(red[0], red[1] * 1.5)
        self.assertGreater(red[0], red[2] * 1.5)
        decoded = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(output),
            "-vn", "-ac", "1", "-ar", "8000", "-f", "f32le", "-",
        ], capture_output=True)
        self.assertEqual(decoded.returncode, 0, decoded.stderr[-700:])
        samples = np.frombuffer(decoded.stdout, dtype="<f4")
        for center, expected in ((0.5, 440), (1.5, 880)):
            window = samples[int((center - 0.25) * 8000):int((center + 0.25) * 8000)]
            spectrum = np.abs(np.fft.rfft(window))
            frequency = np.fft.rfftfreq(len(window), 1 / 8000)[spectrum.argmax()]
            self.assertAlmostEqual(frequency, expected, delta=8)
        self.assertEqual(model.sha256_file(self.source), source_hash)
        original_selection = self.crop_selection.read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "selection changed"):
            self.crop_selection.write_text(self.crop_selection.read_text() + "\n")
            model.validate(revision)
        self.crop_selection.write_text(original_selection, encoding="utf-8")
        manifest = self.crop_selection.parent / json.loads(original_selection)["evidence"]["manifest"]
        original_manifest = manifest.read_text(encoding="utf-8")
        manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "manifest changed"):
            model.validate(revision)
        manifest.write_text(original_manifest, encoding="utf-8")
        proposal = self.crop_selection.parent / json.loads(original_selection)["crop_intervals"][0]["proposal_file"]
        proposal.write_text(proposal.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "proposal changed"):
            model.validate(revision)


if __name__ == "__main__":
    unittest.main()
