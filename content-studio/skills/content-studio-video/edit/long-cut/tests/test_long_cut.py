"""Check source-order assembly and review integrity without a media encode."""

from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "long_cut.py"
SPEC = importlib.util.spec_from_file_location("long_cut", SCRIPT)
long_cut = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(long_cut)


class LongCutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.draft = Path(self.temp.name) / "draft"
        self.original = self.draft / "original"
        self.original.mkdir(parents=True)
        self.pan = self.draft / ".content-studio" / "analysis" / "fastpan-long-v001"
        self.tilt = self.draft / ".content-studio" / "analysis" / "tilt-long-v001"
        self.pan.mkdir(parents=True)
        self.tilt.mkdir(parents=True)
        self.sources = []
        order = self.draft / ".content-studio" / "_timeline.csv"
        with order.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["order", "new_name", "original_name"])
            writer.writeheader()
            for index in (1, 2):
                stable = f"camera-{index}.mp4"
                source = self.original / f"{index:03d} - {stable}"
                source.write_bytes(f"source {index}".encode())
                self.sources.append(source)
                writer.writerow({"order": index, "new_name": source.name,
                                 "original_name": stable})
                blur = self.draft / ".content-studio" / "analysis" / "source-review" / stable
                blur.mkdir(parents=True)
                (blur / "report.json").write_text(json.dumps({
                    "source_sha256": long_cut.sha256_file(source)}))
                with (blur / "review.csv").open("w", newline="", encoding="utf-8") as review:
                    rows = csv.DictWriter(review, fieldnames=["id", "start", "end"])
                    rows.writeheader()
                    if index == 1:
                        rows.writerow({"id": "1", "start": "1.0", "end": "1.5"})
                for folder, candidate in ((self.pan, {"id": "pan-0001",
                                                       "start_frame": 36, "end_frame": 48}
                                          if index == 1 else None),
                                          (self.tilt, {"id": "tilt-0001",
                                                       "start_frame": 45, "end_frame": 60}
                                           if index == 2 else None)):
                    (folder / f"{index}.json").write_text(json.dumps({
                        "schema": "content-studio.fastpan-candidates.v1" if folder == self.pan
                        else "content-studio.tilt-candidates.v1",
                        "source": str(source), "source_sha256": long_cut.sha256_file(source),
                        "fps": 30, "candidates": [candidate] if candidate else []}))
        self.probe = patch.object(long_cut, "probe", return_value={
            "fps": 30.0, "duration_s": 3.0, "frames": 90, "width": 640, "height": 360})
        self.probe.start()
        self.addCleanup(self.probe.stop)
        self.proposal = self.draft / "proposal.json"
        long_cut.propose(self.draft, self.pan, self.tilt, self.proposal)

    def reviewed(self):
        manifest = long_cut.read_json(self.proposal)
        for source in manifest["sources"]:
            for candidate in source["candidates"]:
                candidate.update({"decision": "cut", "actor": "human",
                                  "reviewer": "Editor", "review_note": "Remove unusable interval"})
        path = self.draft / "review.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_overlap_merges_and_camera_order_and_audio_policy_survive(self):
        result = long_cut.build(self.reviewed(), self.draft / "changes.json")
        changes = long_cut.read_json(self.draft / "changes.json")
        self.assertEqual(result["picture_spans"], 4)
        self.assertEqual([(row["source"], row["source_in"], row["source_out"])
                          for row in changes["picture"]], [
            (self.sources[0].name, 0.0, 1.0),
            (self.sources[0].name, 1.6, 3.0),
            (self.sources[1].name, 0.0, 1.5),
            (self.sources[1].name, 2.0, 3.0)])
        self.assertEqual(changes["audio_policy"], "mix")
        self.assertEqual(changes["transitions"], [])

    def test_pending_or_forged_decision_cannot_build(self):
        path = self.reviewed()
        manifest = long_cut.read_json(path)
        manifest["sources"][0]["candidates"][0]["actor"] = "agent"
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "human decision"):
            long_cut.build(path, self.draft / "changes.json")
        manifest["sources"][0]["candidates"][0]["decision"] = "pending_review"
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "needs review"):
            long_cut.build(path, self.draft / "changes.json")

    def test_candidate_removal_or_range_change_is_rejected(self):
        path = self.reviewed()
        manifest = long_cut.read_json(path)
        manifest["sources"][0]["candidates"].pop()
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "candidate list changed"):
            long_cut.build(path, self.draft / "changes.json")
        manifest = long_cut.read_json(self.proposal)
        manifest["sources"][0]["candidates"][0]["end_frame"] += 1
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "candidate changed"):
            long_cut.build(path, self.draft / "changes.json")

    def test_human_can_refine_cut_bounds_but_not_move_away_from_candidate(self):
        path = self.reviewed()
        manifest = long_cut.read_json(path)
        blur = next(row for row in manifest["sources"][0]["candidates"]
                    if row["kind"] == "blur")
        blur["cut_start_frame"] = 29
        blur["cut_end_frame"] = 46
        path.write_text(json.dumps(manifest))
        long_cut.build(path, self.draft / "changes.json")
        picture = long_cut.read_json(self.draft / "changes.json")["picture"]
        self.assertAlmostEqual(picture[0]["source_out"], 29 / 30, places=5)
        blur["cut_start_frame"] = 70
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "miss the candidate"):
            long_cut.build(path, self.draft / "changes-v002.json")

    def test_source_or_detector_changes_invalidate_review(self):
        path = self.reviewed()
        self.sources[0].write_bytes(b"replaced")
        with self.assertRaisesRegex(ValueError, "Blur evidence changed"):
            long_cut.build(path, self.draft / "changes.json")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required")
class LongCutRenderTest(unittest.TestCase):
    def test_reviewed_multisource_spans_render_once_with_audio(self):
        # This synthetic approval fixture proves the long-cut changes reach
        # the native renderer; production still needs real human approval.
        with tempfile.TemporaryDirectory() as temporary:
            draft = Path(temporary) / "draft"
            original = draft / "original"
            original.mkdir(parents=True)
            analysis = draft / ".content-studio" / "analysis"
            pan, tilt = analysis / "pan", analysis / "tilt"
            pan.mkdir(parents=True)
            tilt.mkdir(parents=True)
            order = draft / ".content-studio" / "_timeline.csv"
            sources = []
            with order.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["order", "new_name", "original_name"])
                writer.writeheader()
                for index, frequency in ((1, 440), (2, 880)):
                    name = f"camera-{index}.mp4"
                    source = original / f"{index:03d} - {name}"
                    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                               "-f", "lavfi", "-i", f"testsrc2=size=160x90:rate=10:duration=2",
                               "-f", "lavfi", "-i", f"sine=frequency={frequency}:duration=2",
                               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                               "-shortest", str(source)]
                    result = subprocess.run(command, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr[-500:])
                    sources.append(source)
                    writer.writerow({"order": index, "new_name": source.name,
                                     "original_name": name})
                    blur = analysis / "source-review" / name
                    blur.mkdir(parents=True)
                    (blur / "report.json").write_text(json.dumps({
                        "source_sha256": long_cut.sha256_file(source)}))
                    with (blur / "review.csv").open("w", newline="", encoding="utf-8") as review:
                        rows = csv.DictWriter(review, fieldnames=["id", "start", "end"])
                        rows.writeheader()
                        if index == 1:
                            rows.writerow({"id": 1, "start": 0.5, "end": 1.0})
                    for folder, candidates in ((pan, []), (tilt, [])):
                        (folder / f"{index}.json").write_text(json.dumps({
                            "schema": "content-studio.fastpan-candidates.v1" if folder == pan
                            else "content-studio.tilt-candidates.v1",
                            "source": str(source),
                            "source_sha256": long_cut.sha256_file(source),
                            "fps": 10, "candidates": candidates}))
            proposal = analysis / "long-cut" / "proposal.json"
            long_cut.propose(draft, pan, tilt, proposal)
            reviewed = long_cut.read_json(proposal)
            reviewed["sources"][0]["candidates"][0].update({
                "decision": "cut", "actor": "human", "reviewer": "fixture",
                "review_note": "Synthetic cut for renderer test"})
            review_path = proposal.with_name("review.json")
            review_path.write_text(json.dumps(reviewed))
            changes_path = proposal.with_name("changes.json")
            long_cut.build(review_path, changes_path)
            sys.path.insert(0, str(SCRIPT.parents[3] / "timeline" / "scripts"))
            import compiler  # noqa: E402
            import model  # noqa: E402
            plan = draft / ".content-studio" / "preflight" / "plan.json"
            plan.parent.mkdir()
            plan.write_text(json.dumps({"schema_version": 1, "kind": "edited",
                                        "stage": "edited-render", "steps": [{"id": "S01"}]}))
            digest = model.sha256_file(plan)
            plan.with_name("approval.json").write_text(json.dumps({
                "plan_sha256": digest, "review_note": "Synthetic fixture review"}))
            plan.with_name("checklist.json").write_text(json.dumps({
                "plan_sha256": digest, "items": [{"id": "S01"}]}))
            output = draft / "long-cut-test.mp4"
            initial = model.make_initial(plan, sources[0], output, fps=10,
                                         width=160, height=90)
            initial["picture"][0]["source_out"] = 2
            timeline = model.revise(initial, long_cut.read_json(changes_path),
                                    new_output=str(output))
            resolved = model.validate(timeline)
            self.assertAlmostEqual(resolved["duration"], 3.5)
            compiler.compile_graph(timeline, resolved)
            compiler.render(timeline, resolved)
            media = compiler.media_info(output)
            self.assertTrue(media["video"])
            self.assertTrue(media["audio"])
            self.assertAlmostEqual(media["duration"], 3.5, delta=.15)


if __name__ == "__main__":
    unittest.main()
