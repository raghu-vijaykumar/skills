"""Validate decoded timing and a known movement with a deliberate occlusion."""

import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare import run
from frame_trace import build, decode, detail_boxes, hold_pictures, hold_ranges, landmark_times, seam_times, word_anchor_times
from track_objects import follow, measure_relative, retarget


class TraceTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg"), "needs FFmpeg")
    def test_fractional_bounds_keep_only_source_pts_inside_range(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref = root / "reference.mp4"
            run("ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                "testsrc2=size=160x96:rate=30:duration=2", "-c:v", "libx264", str(ref))
            frames = decode(ref, 0, 0.84, 1.205, root / "frames")
            self.assertEqual([round(pts * 30) for _, pts in frames], list(range(26, 37)))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs FFmpeg and FFprobe")
    def test_decodes_each_lane_at_its_own_rate_with_original_pts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref, draft = [root / f"{name}.mp4" for name in ("source", "draft")]
            for rate, file in ((24, ref), (30, draft)):
                run("ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=size=160x96:rate={rate}:duration=2",
                    "-c:v", "libx264", str(file))
            out = root / "trace"
            beat = {"id": "beat", "reference": [0.5, 1.5], "candidate": [0, 1],
                    "details": {"reference": [.125, .25, .625, .75], "candidate": [.5, 0, .9, .5]},
                    "seam": {"reference": 5 / 6, "candidate": .31},
                    "landmarks": [{"id": "settled", "reference": 1.15, "candidate": .75},
                                  {"id": "impact", "reference": 2 / 3, "candidate": .6}],
                    "word_anchors": [{"id": "impact", "reference": .6, "candidate": .62}],
                    "holds": [{"id": "result", "reference": [.75, 1.25], "candidate": [.4, .9]}]}
            self.assertEqual(build(ref, draft, {"beats": [beat]},
                                   "beat", out, {"full": (0, 0, 1, 1)}), {"reference":24,"candidate":30})
            with (out / "reference.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(float(rows[0]["time"]), 0.5)
            self.assertAlmostEqual(float(rows[-1]["time"]), 35 / 24, places=5)
            report = json.loads((out / "frame-trace.json").read_text())
            self.assertIsNotNone(report["inputs"]["reference"]["sha256"])
            seams = report["seam"]["lanes"]
            self.assertAlmostEqual(seams["reference"]["before"]["time"], 19 / 24, places=5)
            self.assertAlmostEqual(seams["reference"]["after"]["time"], 5 / 6, places=5)
            self.assertEqual(seams["candidate"]["before"]["time"], .3)
            self.assertAlmostEqual(seams["candidate"]["after"]["time"], 10 / 30, places=5)
            self.assertTrue((out / "seam.jpg").is_file())
            viewer = (out / "frames.html").read_text(encoding="utf-8")
            self.assertIn(rows[-1]["image"], viewer)
            self.assertIn('const cuts = {"reference": 8, "candidate": 10}', viewer)
            self.assertEqual([item["id"] for item in report["landmarks"]], ["settled", "impact"])
            impact = report["landmarks"][1]
            self.assertAlmostEqual(impact["lanes"]["reference"]["before"]["time"], 15 / 24, places=5)
            self.assertAlmostEqual(impact["lanes"]["reference"]["after"]["time"], 16 / 24, places=5)
            self.assertEqual(impact["lanes"]["candidate"]["after"]["frame"], 18)
            self.assertEqual(impact["lanes"]["reference"]["word_onset_seconds"], .6)
            self.assertEqual(impact["lanes"]["reference"]["word_to_picture_ms"], 66.7)
            self.assertEqual(impact["lanes"]["candidate"]["word_to_picture_ms"], -20.0)
            self.assertNotIn("word_to_picture_ms", report["landmarks"][0]["lanes"]["reference"])
            self.assertTrue((out / "landmark-impact.jpg").is_file())
            self.assertIn('"impact": {"reference": 4, "candidate": 18}', viewer)
            hold = report["holds"][0]
            self.assertEqual(hold["lanes"]["reference"]["decoded_frames"], 12)
            self.assertEqual(hold["lanes"]["candidate"]["decoded_frames"], 15)
            self.assertEqual(hold["lanes"]["reference"]["middle"]["time"], 1.0)
            self.assertEqual(hold["lanes"]["candidate"]["duration_seconds"], .5)
            self.assertEqual(hold["lanes"]["candidate"]["last"]["frame"], 26)
            self.assertTrue((out / "hold-result.jpg").is_file())
            self.assertIn('const holds = {"result": "hold-result.jpg"}', viewer)
            self.assertEqual(report["detail_boxes_pixels"], {"reference": [20, 24, 100, 72], "candidate": [80, 0, 144, 48]})
            self.assertEqual(len(list((out / "reference-detail").glob("*.jpg"))), 24)
            self.assertEqual(len(list((out / "candidate-detail").glob("*.jpg"))), 30)
            with Image.open(out / "candidate-detail/000011.jpg") as detail:
                self.assertEqual(detail.size, (360, 270))
            for entry in (report["seam"], impact, hold):
                self.assertTrue((out / entry["detail_sheet"]).is_file())

    def test_detail_boxes_require_separate_in_frame_bounds(self):
        meta = dict.fromkeys(("reference", "candidate"), {"width": 160, "height": 96})
        self.assertEqual(detail_boxes({}, meta), {})
        with self.assertRaisesRegex(ValueError, "separate reference and candidate"):
            detail_boxes({"details": {"reference": [0, 0, 1, 1]}}, meta)
        with self.assertRaisesRegex(ValueError, "inside the frame"):
            detail_boxes({"details": {"reference": [0, 0, 1, 1], "candidate": [.5, 0, 1.1, 1]}}, meta)

    def test_seam_requires_times_strictly_inside_each_range(self):
        row = {"reference": [0, 1], "candidate": [1, 2], "seam": {"reference": 1, "candidate": 1.4}}
        with self.assertRaisesRegex(ValueError, "strictly within"):
            seam_times(row)
        self.assertIsNone(seam_times({"reference": [0, 1]}))

    def test_landmarks_need_unique_ids_and_separate_interior_times(self):
        row = {"reference": [0, 1], "candidate": [1, 2]}
        self.assertEqual(landmark_times(row), {})
        event = {"id": "impact", "reference": .5, "candidate": 1.4}
        invalid = [([event, event], "duplicate"), ([{**event, "id": "../impact"}], "Invalid"),
                   ([{**event, "candidate": 2}], "strictly within"),
                   ([{"id": "impact", "reference": .7}], "separate reference and candidate")]
        for events, message in invalid:
            with self.subTest(events=events), self.assertRaisesRegex(ValueError, message):
                landmark_times({**row, "landmarks": events})

    def test_word_anchors_require_a_mapped_landmark_and_onsets_in_both_lanes(self):
        row = {"reference": [0, 1], "candidate": [1, 2],
               "landmarks": [{"id": "impact", "reference": .5, "candidate": 1.4}]}
        landmarks = landmark_times(row)
        anchor = {"id": "impact", "reference": 0, "candidate": 1}
        self.assertEqual(word_anchor_times({**row, "word_anchors": [anchor]}, landmarks),
                         {"impact": {"reference": 0, "candidate": 1}})
        for entry, message in (({**anchor, "id": "unknown"}, "matching landmark"),
                               ({**anchor, "candidate": 2}, "mapped half-open range"),
                               ({"id": "impact", "reference": .2}, "separate reference and candidate")):
            with self.subTest(entry=entry), self.assertRaisesRegex(ValueError, message):
                word_anchor_times({**row, "word_anchors": [entry]}, landmarks)

    def test_holds_must_fit_the_beat_and_include_a_decoded_picture(self):
        row = {"reference": [0, 1], "candidate": [1, 2],
               "holds": [{"id": "result", "reference": [.3, .7], "candidate": [1.8, 2.1]}]}
        with self.assertRaisesRegex(ValueError, "inside its mapped range"):
            hold_ranges(row)
        with self.assertRaisesRegex(ValueError, "No decoded picture"):
            hold_pictures("candidate", "result", [1.01, 1.02], [("image", 1.0)], [{}])

    def test_tracks_translation_and_does_not_bridge_occlusion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            patch = np.random.default_rng(7).integers(60, 255, size=(12, 14), dtype=np.uint8)
            rows = []
            for i in range(9):
                picture = np.zeros((80, 100), dtype=np.uint8)
                if i not in (3, 5, 6, 7, 8):
                    picture[23+i:35+i, 10+2*i:24+2*i] = patch
                name = f"{i}.png"
                Image.fromarray(picture).save(root / name)
                rows.append({"frame":i,"time":i/30,"image":name})
            points = follow(root, "reference", rows, {"first":0,"last":8,"box":[10,23,14,12],"radius":8})
            self.assertEqual(points[2]["dx"], 0.04)
            self.assertEqual(points[2]["dy"], 0.025)
            self.assertIsNone(points[3]["x"])
            self.assertEqual(points[4]["dx"], 0.08)
            self.assertTrue(all(p["x"] is None for p in points[5:]))
            keys = retarget(points, {"start_frame":10,"fps":30,"width":1000,"height":1920})
            self.assertEqual([[k["frame"] for k in band] for band in keys], [[10,11,12],[14]])
            self.assertEqual(keys[0][-1]["x"], 40)

    def test_relative_track_cancels_translation_and_exposes_loss(self):
        def record(name, path):
            return {"id": name, "lane": "candidate", "first": 0, "last": 3, "samples": [
                {"frame": i, "time": i/30, "x": x, "y": .5 if x is not None else None}
                for i, x in enumerate(path)
            ]}
        shoe = record("shoe", [.4, .36, None, .29])
        ground = record("ground", [.7, .66, .62, .58])
        request = {"id": "stance", "subject": "shoe", "anchor": "ground"}
        result, = measure_relative([shoe, ground], [request])
        self.assertEqual(result["tracked_frames"], 3)
        self.assertEqual([p["dx"] for p in result["samples"]], [0, 0, None, .01])
        self.assertEqual(result["max_abs_dx"], .01)
        with self.assertRaisesRegex(ValueError, "same lane"):
            measure_relative([shoe, {**ground, "lane": "reference"}], [request])

    def test_second_anchor_cancels_uniform_zoom_and_exposes_true_shift(self):
        def track(name, coordinates):
            return {"id": name, "lane": "candidate", "first": 0, "last": len(coordinates)-1,
                    "samples": [{"frame": i, "time": i/30, "x": x, "y": y}
                                for i, (x, y) in enumerate(coordinates)]}

        shoe = track("shoe", [(.4, .54), (.6, .62), (.63, .62), (.61, .62), (.62, .62)])
        ground = track("ground", [(.2, .3), (.3, .26), (.3, .26), (.3, .26), (.3, .26)])
        second = track("mark", [(.6, .3), (.9, .26), (.9, .26), (None, None), (.3, .26)])
        request = {"id": "stance", "subject": "shoe", "anchor": "ground", "scale_anchor": "mark"}
        result, = measure_relative([shoe, ground, second], [request])
        self.assertEqual(result["tracked_frames"], 3)
        self.assertEqual([row["dx"] for row in result["samples"]], [0, 0, .02, None, None])
        self.assertEqual([row["scale"] for row in result["samples"]], [1.0, 1.5, 1.5, None, None])
        self.assertEqual(result["max_abs_dy"], 0)
        with self.assertRaisesRegex(ValueError, "distinct tracks"):
            measure_relative([shoe, ground, second], [{**request, "scale_anchor": "ground"}])


if __name__ == "__main__":
    unittest.main()
