import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import enhance


class EnhanceTest(unittest.TestCase):
    def make_video(self, path, video_filter="null"):
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=2",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
            "-vf", video_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(path)], check=True, capture_output=True)

    def test_dark_frame_detects_underexposure(self):
        dark = np.zeros((60, 80, 3), dtype=np.float32)
        metrics = enhance.frame_metrics(dark)
        self.assertLess(metrics["luma_mean"], 0.10)
        self.assertGreater(metrics["clip_low"], 0.9)

    def test_blue_cast_produces_white_balance_issue(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "cast.mp4"
            self.make_video(source, "hue=s=0.25,colorchannelmixer=bb=1.4:rr=0.8")
            report = enhance.analyze_clip(source, root / "enhancement")
            self.assertEqual(report["analysis_version"], "1")
            names = {name for scene in report["clips"][0]["scenes"]
                     for name in scene["issues"]}
            self.assertIn("white_balance", names)

    def test_analysis_writes_manifest_and_html_and_reuses_cache(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "clean.mp4"
            self.make_video(source)
            first = enhance.analyze_clip(source, root / "enhancement")
            work = root / "enhancement" / "clean"
            self.assertTrue((work / "analysis" / "report.json").is_file())
            self.assertTrue((work / "manifests" / "enhancement.yaml").is_file())
            self.assertTrue((work / "reports" / "quality.html").is_file())
            second = enhance.analyze_clip(source, root / "enhancement")
            self.assertEqual(first["generated_at"], second["generated_at"])
            manifest = yaml.safe_load((work / "manifests" / "enhancement.yaml").read_text())
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["clips"][0]["source_hash"], first["clips"][0]["source_hash"])

    def test_approved_color_correction_renders_and_validates(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "dark.mp4"
            self.make_video(source, "hue=s=0.2,colorchannelmixer=bb=1.6:rr=0.7")
            output_root = root / "enhancement"
            report = enhance.analyze_clip(source, output_root, auto_fix=True)
            manifest_path = output_root / "dark" / "manifests" / "enhancement.yaml"
            manifest = yaml.safe_load(manifest_path.read_text())
            approved = False
            for scene in manifest["clips"][0]["scenes"]:
                if scene["corrections"] and scene["decision"] == "FIX":
                    scene["review"]["status"] = "auto_approved"
                    approved = True
            self.assertTrue(approved, "test clip did not produce a fixable color scene")
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            target = root / "corrected.mp4"
            validation = enhance.render_manifest(manifest_path, target)
            self.assertEqual(validation["status"], "passed")
            self.assertTrue(target.is_file())
            self.assertGreater(target.stat().st_size, 0)

    def test_reflection_benchmark_runs_external_adapter(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "glare.mp4"
            self.make_video(source, "drawbox=x=100:y=40:w=120:h=100:color=white:t=fill")
            adapter = root / "adapter.py"
            adapter.write_text(
                "import shutil, sys\nshutil.copy2(sys.argv[1], sys.argv[2])\n",
                encoding="utf-8")
            config = root / "backend.json"
            config.write_text(json.dumps({
                "name": "copy-test", "license": "test-only",
                "command": [sys.executable, str(adapter), "{input}", "{output}"],
            }), encoding="utf-8")
            document = enhance.run_benchmark(source, config, root / "benchmarks", frames=1)
            self.assertEqual(document["summary"]["samples"], 1)
            self.assertEqual(document["summary"]["accepted"], 1)
            self.assertTrue((root / "benchmarks" / "copy-test" / "benchmarks.json").is_file())
            self.assertTrue((root / "benchmarks" / "copy-test" / "benchmark.html").is_file())

    def test_timeline_analysis_uses_referenced_sources(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "clip.mp4"
            self.make_video(source)
            timeline = root / "timeline.json"
            timeline.write_text(json.dumps({
                "schema": "content-studio.timeline.v1",
                "source_root": str(root),
                "tracks": [{"kind": "video", "clips": [
                    {"source": "clip.mp4", "source_in": 0, "source_out": 2,
                     "start": 0, "duration": 2}]}],
            }), encoding="utf-8")
            report = enhance.analyze_timeline(timeline, root / "enhancement",
                                              selected_clips=True)
            self.assertEqual(report["selected_clips"], True)
            self.assertEqual(report["clips"][0]["name"], "clip.mp4")

    def test_strong_glare_is_never_auto_corrected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "glare.mp4"
            self.make_video(source, "drawbox=x=100:y=40:w=120:h=100:color=white:t=fill")
            report = enhance.analyze_clip(source, root / "enhancement", auto_fix=True)
            scenes = report["clips"][0]["scenes"]
            reflection = [scene["issues"]["reflection"] for scene in scenes
                          if "reflection" in scene["issues"]]
            self.assertTrue(reflection)
            self.assertTrue(all(issue["action"] in {"REVIEW", "UNSUPPORTED"}
                                for issue in reflection))
            self.assertTrue(all(scene["review"]["status"] == "pending"
                                for scene in scenes if "reflection" in scene["issues"]))


if __name__ == "__main__":
    unittest.main()
