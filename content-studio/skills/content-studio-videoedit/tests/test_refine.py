import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import refine


class RefineTest(unittest.TestCase):
    def make_video(self, path):
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=1",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
            "-vf", "noise=alls=18:allf=t", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(path)], check=True, capture_output=True)

    def test_refine_selects_candidate_and_writes_timeline(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "clip.mp4"
            self.make_video(source)
            timeline = root / "timeline.json"
            timeline.write_text(json.dumps({
                "schema": "content-studio.timeline.v1",
                "source_root": str(root),
                "tracks": [{"kind": "video", "clips": [{
                    "source": "clip.mp4", "source_in": 0, "source_out": 1,
                    "start": 0, "duration": 1}]}],
            }), encoding="utf-8")
            output = root / "timeline-refined.json"
            report = refine.refine(refine.build_parser().parse_args([
                "--timeline", str(timeline),
                "--output-timeline", str(output),
                "--analysis-dir", str(root / "enhancement")]))
            self.assertTrue(output.is_file())
            self.assertTrue((root / "refine.json").is_file())
            clip = json.loads(output.read_text())["tracks"][0]["clips"][0]
            self.assertIn("enhancements", clip)
            stages = [item.get("stage") for item in clip["enhancements"]]
            if "sharpen" in stages:
                self.assertEqual(stages[-1], "sharpen")
            self.assertEqual(report["clips"][0]["source"], "clip.mp4")
            self.assertIn(report["clips"][0]["selected"], {"off", "light", "medium"})
            self.assertEqual(len(report["clips"][0]["alternatives"]), 3)


if __name__ == "__main__":
    unittest.main()
