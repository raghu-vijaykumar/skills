import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

FOLDER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FOLDER / "scripts"))
sys.path.insert(0, str(FOLDER.parents[1] / "timeline" / "scripts"))
import object_blur  # noqa: E402
import approval  # noqa: E402
import compiler  # noqa: E402
import model  # noqa: E402


class RedDetector:
    def detect(self, image, target):
        assert target == "red objects"
        pixels = np.asarray(image)
        red = ((pixels[:, :, 0] > 180) & (pixels[:, :, 1] < 100)
               & (pixels[:, :, 2] < 100))
        # Synthetic objects have a clear empty-column gap.
        groups = []
        columns = np.flatnonzero(red.any(axis=0))
        for group in np.split(columns, np.where(np.diff(columns) > 1)[0] + 1):
            if group.size:
                ys = np.flatnonzero(red[:, group].any(axis=1))
                groups.append({"box": [float(group.min()), float(ys.min()),
                                       float(group.max() + 1), float(ys.max() + 1)],
                               "score": .99})
        return groups


class BoxMasker:
    def masks(self, image, boxes):
        result = []
        for x1, y1, x2, y2 in boxes:
            mask = np.zeros((image.height, image.width), dtype=bool)
            mask[int(y1):int(y2), int(x1):int(x2)] = True
            result.append(mask)
        return result


class EmptyDetector:
    def detect(self, image, target):
        return []


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required")
class ObjectBlurTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "edit.mp4"
        frames = []
        for index in range(4):
            image = np.full((90, 160, 3), 65, dtype=np.uint8)
            image[25:56, 20 + index * 9:44 + index * 9] = [245, 20, 20]
            image[52:77, 112:132] = [245, 20, 20]
            frames.append(image)
        raw = b"".join(frame.tobytes() for frame in frames)
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "160x90",
            "-r", "4", "-i", "-", "-f", "lavfi", "-i",
            "sine=frequency=440:duration=1", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
            str(self.source)], input=raw, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        plan_dir = self.root / "preflight"
        plan_dir.mkdir()
        plan = plan_dir / "plan.json"
        plan.write_text(json.dumps({"schema_version": 1, "kind": "edited",
                                    "stage": "edited-render", "steps": [{"id": "S01"}]}))
        plan_hash = model.sha256_file(plan)
        (plan_dir / "approval.json").write_text(json.dumps({
            "plan_sha256": plan_hash, "review_note": "synthetic fixture"}))
        (plan_dir / "checklist.json").write_text(json.dumps({
            "plan_sha256": plan_hash, "items": [{"id": "S01"}]}))
        self.timeline = model.make_initial(plan, self.source,
                                           self.root / "final.mp4",
                                           fps=4, width=160, height=90)
        self.timeline["picture"][0]["source_out"] = 1.0
        self.timeline["audio_policy"] = "copy_source"

    def tearDown(self):
        self.temp.cleanup()

    def analyze(self):
        out = self.root / "object-blur" / "run-001"
        report = object_blur.analyze(self.timeline, out, "red objects",
                                     detector_factory=RedDetector,
                                     masker_factory=BoxMasker)
        self.assertEqual(report["frames"], 4)
        self.assertEqual(report["flagged_frames"], [])
        return out, report

    def review(self, out, report):
        path = out / "coverage-review.json"
        path.write_text(json.dumps({
            "actor": "human", "reviewer": "Fixture editor",
            "review_note": "Inspected all four synthetic frames",
            "source_sha256": report["source_sha256"],
            "analysis_sha256": model.sha256_file(out / "analysis.json"),
            "mask_sha256": report["mask_sha256"],
            "frames_reviewed": report["frames"],
            "resolved_frames": report["flagged_frames"]}))
        return path

    def test_full_frame_mask_and_single_export_blur_only_targets(self):
        out, report = self.analyze()
        frames = [json.loads(line) for line in (out / "frames.jsonl").read_text().splitlines()]
        self.assertEqual([frame["selected"] for frame in frames], [2] * 4)
        review = self.review(out, report)
        self.timeline.update(object_blur.changes(
            self.timeline, out / "analysis.json"))
        self.timeline["operations"][0].update({
            "coverage_review_source": str(review.relative_to(self.root)),
            "coverage_review_sha256": model.sha256_file(review)})
        self.timeline["operations"][0]["review_status"] = "approved"
        resolved = model.validate(self.timeline)
        record = compiler.render(self.timeline, resolved)
        self.assertEqual(record["video_encoder_invocations"], 1)
        self.assertEqual(record["audio_encoder_invocations"], 0)
        self.assertTrue(Path(record["output"]).is_file())
        original = self.frame(self.source, .625)
        blurred = self.frame(self.root / "final.mp4", .625)
        # Strong blur substantially changes red target interiors while the
        # untouched corner stays visually equivalent after video encoding.
        self.assertGreater(np.abs(original[40, 54].astype(int)
                                  - blurred[40, 54].astype(int)).sum(), 45)
        self.assertLess(np.abs(original[6, 6].astype(int)
                               - blurred[6, 6].astype(int)).sum(), 20)
        self.assertEqual(self.audio_hash(self.source),
                         self.audio_hash(self.root / "final.mp4"))

    def test_coverage_record_and_changed_mask_block_export(self):
        out, report = self.analyze()
        self.timeline.update(object_blur.changes(self.timeline, out / "analysis.json"))
        self.timeline["operations"][0]["review_status"] = "approved"
        with self.assertRaisesRegex(ValueError, "coverage review is missing"):
            model.validate(self.timeline)
        review = self.review(out, report)
        self.timeline["operations"][0].update({
            "coverage_review_source": str(review.relative_to(self.root)),
            "coverage_review_sha256": model.sha256_file(review)})
        model.validate(self.timeline)
        with (out / "mask.mkv").open("ab") as target:
            target.write(b"changed")
        with self.assertRaisesRegex(ValueError, "mask or analysis changed"):
            model.validate(self.timeline)

    def test_click_and_correction_input(self):
        rows = [{"box": [10., 10., 30., 30.], "score": .9},
                {"box": [80., 10., 110., 40.], "score": .9}]
        selected, ambiguous = object_blur._select_one(rows, (0, .6, .3),
                                                        0, None, 160, 90)
        self.assertFalse(ambiguous)
        self.assertEqual(selected, rows[1:])
        corrected = self.root / "corrections.json"
        corrected.write_text(json.dumps({"frames": [{
            "index": 1, "replace_boxes": [[.1, .2, .3, .4]],
            "add_polygons": [[[.1, .1], [.2, .1], [.2, .2]]]}]}))
        corrections = object_blur._load_corrections(corrected, 4)
        self.assertEqual(len(corrections), 1)
        self.assertEqual(object_blur._box(corrections[1]["replace_boxes"][0],
                                         160, 90), [16., 18., 48., 36.])

    def test_click_tracks_one_instance_backward_and_forward(self):
        out = self.root / "object-blur" / "clicked"
        report = object_blur.analyze(
            self.timeline, out, "red objects", click=(2, .31, .44),
            detector_factory=RedDetector, masker_factory=BoxMasker)
        rows = [json.loads(line) for line in (out / "frames.jsonl").read_text().splitlines()]
        self.assertEqual([row["selected"] for row in rows], [1] * 4,
                         (out / "detections.jsonl").read_text())
        self.assertEqual(report["flagged_frames"], [])

    def test_repeated_clicks_can_reseed_after_a_cut(self):
        rows = [{"index": index, "detections": [
            {"box": [10., 20., 30., 40.]},
            {"box": [80., 20., 100., 40.]}]}
            for index in range(4)]
        selected, uncertain = object_blur._track_selections(
            rows, [(0, .12, .33), (2, .56, .33)], 160, 90)
        self.assertEqual(selected, {0: 0, 1: 0, 2: 1, 3: 1})
        self.assertEqual(uncertain, set())

    def test_zero_detection_flags_every_frame_for_review(self):
        out = self.root / "object-blur" / "no-matches"
        report = object_blur.analyze(
            self.timeline, out, "red objects", detector_factory=EmptyDetector,
            masker_factory=BoxMasker)
        self.assertEqual(report["flagged_frames"], [0, 1, 2, 3])
        review = self.review(out, report)
        evidence = json.loads(review.read_text())
        evidence["resolved_frames"] = []
        review.write_text(json.dumps(evidence))
        self.timeline.update(object_blur.changes(
            self.timeline, out / "analysis.json"))
        self.timeline["operations"][0].update({
            "coverage_review_source": str(review.relative_to(self.root)),
            "coverage_review_sha256": model.sha256_file(review)})
        self.timeline["operations"][0]["review_status"] = "approved"
        with self.assertRaisesRegex(ValueError, "coverage review is incomplete"):
            model.validate(self.timeline)

    def test_corrected_box_and_polygon_change_the_mask(self):
        corrections = self.root / "corrections.json"
        corrections.write_text(json.dumps({"frames": [{
            "index": 1, "replace_boxes": [],
            "add_polygons": [[[.1, .1], [.2, .1], [.2, .2], [.1, .2]]]}]}))
        out = self.root / "object-blur" / "corrected"
        report = object_blur.analyze(
            self.timeline, out, "red objects", corrections_path=corrections,
            detector_factory=RedDetector, masker_factory=BoxMasker)
        self.assertEqual(len(report["corrections_sha256"]), 64)
        frame = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i",
            str(out / "mask.mkv"), "-vf", "select=eq(n\\,1)",
            "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
            capture_output=True, check=True)
        pixels = np.frombuffer(frame.stdout, dtype=np.uint8).reshape(90, 160)
        self.assertGreater(pixels[13, 22], 200)
        self.assertLess(pixels[40, 35], 10)

    def test_timeline_fingerprint_binds_human_coverage(self):
        out, report = self.analyze()
        review = self.review(out, report)
        self.timeline.update(object_blur.changes(
            self.timeline, out / "analysis.json", review))
        self.timeline["operations"][0]["review_status"] = "approved"
        timeline_path = self.root / "timeline.json"
        timeline_path.write_text(json.dumps(self.timeline))
        first = approval.fingerprint(timeline_path, self.timeline)
        self.assertEqual(len(first), 64)
        review.write_text(review.read_text().replace("four", "all"))
        with self.assertRaisesRegex(ValueError, "coverage review changed"):
            approval.fingerprint(timeline_path, self.timeline)

    def test_rejects_remapped_or_preserved_picture(self):
        self.timeline["audio_policy"] = "mix"
        self.timeline["picture"][0]["source_in"] = .25
        with self.assertRaisesRegex(ValueError, "one uncut SDR picture"):
            object_blur.source_contract(self.timeline)
        self.timeline["picture"][0]["source_in"] = 0
        self.timeline["video_policy"] = "copy_source"
        self.timeline["color_policy"] = "preserve"
        self.timeline["audio_policy"] = "mix"
        with self.assertRaisesRegex(ValueError, "one uncut SDR picture"):
            object_blur.source_contract(self.timeline)

    def frame(self, source, time):
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(time),
            "-i", str(source), "-frames:v", "1", "-f", "rawvideo",
            "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
        return np.frombuffer(result.stdout, dtype=np.uint8).reshape(90, 160, 3)

    def audio_hash(self, source):
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_packets", "-show_data_hash", "sha256",
            "-show_entries", "packet=data_hash", "-of", "json", str(source)],
            capture_output=True, text=True, check=True)
        packets = json.loads(result.stdout)["packets"]
        return [packet["data_hash"] for packet in packets]


if __name__ == "__main__":
    unittest.main()
