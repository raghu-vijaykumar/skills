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
from frame_trace import build, decode, seam_times
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
                    "seam": {"reference": 5 / 6, "candidate": .31}}
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

    def test_seam_requires_times_strictly_inside_each_range(self):
        row = {"reference": [0, 1], "candidate": [1, 2], "seam": {"reference": 1, "candidate": 1.4}}
        with self.assertRaisesRegex(ValueError, "strictly within"):
            seam_times(row)
        self.assertIsNone(seam_times({"reference": [0, 1]}))

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


if __name__ == "__main__":
    unittest.main()
