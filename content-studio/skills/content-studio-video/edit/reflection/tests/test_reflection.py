import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "clip-edit" / "scripts"))
import reflection


class ReflectionTest(unittest.TestCase):
    def make_video(self, path, video_filter="null"):
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=0x404040:s=320x180:r=30:d=2",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
            "-vf", video_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(path)],
            check=True, capture_output=True)

    def test_clean_scene_is_skipped(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "clean.mp4"
            self.make_video(source)
            report = reflection.detect_clip(source, root / "reflection")
            scene = report["clips"][0]["scenes"][0]
            self.assertEqual(scene["decision"], "SKIP")
            self.assertFalse(scene["issue"]["detected"])
            self.assertEqual(scene["region_masks"], [])

    def test_minor_glare_is_fixable_with_a_mask(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "minor.mp4"
            self.make_video(
                source,
                "drawbox=x=130:y=70:w=56:h=42:color=0xF2F2F2:t=fill")
            report = reflection.detect_clip(source, root / "reflection")
            scene = report["clips"][0]["scenes"][0]
            self.assertEqual(scene["decision"], "FIX")
            self.assertEqual(scene["issue"]["type"], "glare_veil")
            self.assertTrue(scene["region_masks"])
            self.assertTrue(Path(scene["region_masks"][0]["mask"]).is_file())
            self.assertTrue(scene["evidence"]["overlays"])

    def test_strong_reflection_is_unsupported(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "strong.mp4"
            self.make_video(
                source,
                "drawbox=x=80:y=30:w=160:h=120:color=0xF2F2F2:t=fill")
            report = reflection.detect_clip(source, root / "reflection")
            scene = report["clips"][0]["scenes"][0]
            self.assertEqual(scene["decision"], "UNSUPPORTED")
            self.assertEqual(scene["issue"]["type"], "strong_reflection")
            self.assertEqual(scene["region_masks"], [])

    def test_analysis_writes_package_and_reuses_cache(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "minor.mp4"
            self.make_video(
                source,
                "drawbox=x=130:y=70:w=56:h=42:color=0xF2F2F2:t=fill")
            first = reflection.detect_clip(source, root / "reflection")
            work = root / "reflection" / "minor"
            self.assertTrue((work / "analysis" / "report.json").is_file())
            self.assertTrue((work / "manifests" / "reflection.yaml").is_file())
            self.assertTrue((work / "reports" / "reflection.html").is_file())
            self.assertTrue((work / "previews" / "contact-sheet.jpg").is_file())
            second = reflection.detect_clip(source, root / "reflection")
            self.assertEqual(first["generated_at"], second["generated_at"])
            manifest = yaml.safe_load(
                (work / "manifests" / "reflection.yaml").read_text())
            self.assertEqual(manifest["clips"][0]["source_hash"],
                             first["clips"][0]["source_hash"])

    def test_approved_minor_fix_renders_and_validates(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "minor.mp4"
            self.make_video(
                source,
                "drawbox=x=130:y=70:w=56:h=42:color=0xF2F2F2:t=fill")
            output_root = root / "reflection"
            reflection.detect_clip(source, output_root)
            manifest_path = (output_root / "minor" / "manifests" /
                             "reflection.yaml")
            manifest = yaml.safe_load(manifest_path.read_text())
            approved = False
            for scene in manifest["clips"][0]["scenes"]:
                if scene["decision"] == "FIX":
                    scene["review"]["status"] = "auto_approved"
                    approved = True
            self.assertTrue(approved, "minor clip did not produce a FIX scene")
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
            target = root / "minor-fixed.mp4"
            validation = reflection.fix_manifest(manifest_path, target)
            self.assertEqual(validation["status"], "passed")
            self.assertTrue(target.is_file())
            self.assertGreater(target.stat().st_size, 0)
            self.assertTrue((manifest_path.parent / "validation.json").is_file())

    def test_fix_refuses_strong_reflection_without_approval(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "strong.mp4"
            self.make_video(
                source,
                "drawbox=x=80:y=30:w=160:h=120:color=0xF2F2F2:t=fill")
            output_root = root / "reflection"
            reflection.detect_clip(source, output_root)
            manifest_path = (output_root / "strong" / "manifests" /
                             "reflection.yaml")
            with self.assertRaises(reflection.ReflectionError):
                reflection.fix_manifest(manifest_path, root / "fixed.mp4")

    def test_preview_renders_bounded_comparison(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "strong.mp4"
            self.make_video(
                source,
                "drawbox=x=80:y=30:w=160:h=120:color=0xF2F2F2:t=fill")
            output_root = root / "reflection"
            reflection.detect_clip(source, output_root)
            manifest_path = (output_root / "strong" / "manifests" /
                             "reflection.yaml")
            target = root / "preview.mp4"
            validation = reflection.preview_manifest(
                manifest_path, target, seconds=1.0)
            self.assertEqual(validation["status"], "review_required")
            self.assertTrue(target.is_file())
            self.assertGreater(target.stat().st_size, 0)
            self.assertTrue((manifest_path.parent /
                             "preview-scene-001-validation.json").is_file())

    def test_benchmark_runs_external_backend(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "strong.mp4"
            self.make_video(
                source,
                "drawbox=x=80:y=30:w=160:h=120:color=0xF2F2F2:t=fill")
            adapter = root / "adapter.py"
            adapter.write_text(
                "import sys\n"
                "from PIL import Image, ImageEnhance\n"
                "image = Image.open(sys.argv[1]).convert('RGB')\n"
                "ImageEnhance.Brightness(image).enhance(0.70).save(sys.argv[2])\n",
                encoding="utf-8")
            config = root / "backend.json"
            config.write_text(json.dumps({
                "name": "darken-test",
                "license": "test-only",
                "checkpoint": "none",
                "command": [sys.executable, str(adapter), "{input}", "{output}"],
            }), encoding="utf-8")
            document = reflection.run_benchmark(
                source, config, root / "benchmarks", frames=1)
            self.assertEqual(document["summary"]["samples"], 1)
            self.assertEqual(document["summary"]["accepted"], 1)
            work = root / "benchmarks" / "darken-test"
            self.assertTrue((work / "benchmarks.json").is_file())
            self.assertTrue((work / "benchmark.html").is_file())


if __name__ == "__main__":
    unittest.main()
