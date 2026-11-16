"""Exercise range validation and a real review render with offset clips."""

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image

spec = importlib.util.spec_from_file_location("compare", Path(__file__).resolve().parents[1] / "scripts" / "compare.py")
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


class CritiqueTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg"), "needs FFmpeg")
    def test_cut_scan_keeps_source_timestamps(self):
        with tempfile.TemporaryDirectory() as folder:
            clip = Path(folder) / "cut.mp4"
            compare.run("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=160x96:r=24:d=1",
                        "-f", "lavfi", "-i", "color=white:s=160x96:r=24:d=1",
                        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0", "-c:v", "libx264", str(clip))
            markers = compare.scan_cut_candidates(clip, 0, .24)
            self.assertEqual([mark["seconds"] for mark in markers], [1.0])

    def test_map_coverage_is_union_and_unmatched_ranges_stay_uncovered(self):
        rows = compare.validate_map({"beats": [
            {"id": "open", "reference": [0, 1.5], "candidate": [0, 1]},
            {"id": "cut", "reference": [1, 2], "candidate": [0.5, 1.5]},
            {"id": "omitted", "reference": [2, 3], "candidate": None},
        ]}, 3, 1.5)
        spans = [row["reference"] for row in rows if row["candidate"] is not None]
        self.assertEqual(compare.coverage(spans, 3), {"mapped_seconds": 2, "uncovered_ranges": [[2, 3]]})

    def test_rejects_reversed_out_of_bounds_and_unsafe_mapping(self):
        row = {"id": "valid", "reference": [0, 2], "candidate": [0, 1]}
        for bad in ({"candidate": [1, 0]}, {"reference": [0, 4]}, {"id": "../escape"},
                    {"reference": [False, 2]}, {"candidate": [0, float("nan")]}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                compare.validate_map({"beats": [{**row, **bad}]}, 3, 3)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs FFmpeg and FFprobe")
    def test_offset_and_unequal_ranges_render_motion_and_identify_exact_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            reference, candidate = root / "a.mp4", root / "b.mp4"
            for file, source in ((reference, "testsrc2"), (candidate, "testsrc")):
                compare.run("ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"{source}=duration=3:size=160x96:rate=24",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(file))
            out = root / "evidence"
            compare.build(reference, candidate, {"beats": [
                {"id": "cut", "reference": [1, 2.5], "candidate": [0, 1]},
            ]}, out)
            record = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(record["coverage"]["reference"]["uncovered_ranges"], [[0, 1], [2.5, 3]])
            self.assertEqual(record["coverage"]["candidate"]["mapped_seconds"], 1)
            self.assertNotEqual(record["reference"]["sha256"], record["candidate"]["sha256"])
            with Image.open(out / record["rows"][0]["motion"]) as gif:
                self.assertGreaterEqual(gif.n_frames, 17)
                self.assertEqual(gif.size, (480, 320))
                gif.seek(gif.n_frames - 1)
                self.assertEqual(gif.convert("RGB").getpixel((360, 160)), (0, 0, 0))
            with self.assertRaises(FileExistsError):
                compare.build(reference, candidate, {"beats": record["rows"]}, out)


if __name__ == "__main__":
    unittest.main()
