"""Reject stale or corrupted frame caches before a resumable encode."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "resume_render.py"
MODULE_SPEC = importlib.util.spec_from_file_location("blender_resume_render", SCRIPT)
resume = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(resume)


class ResumeRenderTests(unittest.TestCase):
    def test_signature_changes_with_inputs_and_render_profile(self):
        scene = SimpleNamespace(
            render=SimpleNamespace(engine="BLENDER_EEVEE", resolution_x=320,
                                   resolution_y=240, fps=24, fps_base=1),
            frame_start=1, frame_end=3,
            view_settings=SimpleNamespace(view_transform="AgX"),
        )
        first = resume.signature({"builder.py": "a"}, scene, "Blender 5.3")
        self.assertNotEqual(first, resume.signature({"builder.py": "b"}, scene, "Blender 5.3"))
        scene.render.fps = 30
        self.assertNotEqual(first, resume.signature({"builder.py": "a"}, scene, "Blender 5.3"))

    def test_cached_frame_hash_and_signature_are_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            frame = resume.frame_path(cache, 1)
            frame.write_bytes(b"reviewed frame")
            manifest = {"schema_version": 1, "signature": "same", "frame_range": [1, 3],
                        "frames": {"1": {"sha256": resume.sha256(frame), "bytes": frame.stat().st_size}}}
            resume.verify_manifest(manifest, cache, "same", 1, 3)
            with self.assertRaisesRegex(ValueError, "differs"):
                resume.verify_manifest(manifest, cache, "changed", 1, 3)
            frame.write_bytes(b"corrupted frame")
            with self.assertRaisesRegex(ValueError, "missing or changed"):
                resume.verify_manifest(manifest, cache, "same", 1, 3)

    def test_manifest_write_is_complete_and_low_space_stops_before_render(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            resume.atomic_json(path, {"frame_range": [1, 3]})
            self.assertEqual(json.loads(path.read_text())["frame_range"], [1, 3])
            self.assertFalse(path.with_name("manifest.json.tmp").exists())
            with patch.object(resume.shutil, "disk_usage", return_value=SimpleNamespace(free=100)):
                with self.assertRaisesRegex(OSError, "Insufficient render space"):
                    resume.disk_budget(directory, 320, 240, 3)


if __name__ == "__main__":
    unittest.main()
