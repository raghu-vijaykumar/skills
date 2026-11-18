"""Keep authored shot identity, timing, and provenance stable before Blender renders."""

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "shot_spec.py"
MODULE_SPEC = importlib.util.spec_from_file_location("blender_shot_spec", SCRIPT)
shot_spec = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(shot_spec)
EXAMPLE = ROOT / "examples" / "clamp-contract-v2.json"


class ShotSpecTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_version_two_contract_and_scene_match(self):
        contract = shot_spec.validate_spec(self.spec, EXAMPLE.parent)
        self.assertEqual(contract["beat_ids"], ["initial", "action", "result"])
        self.assertEqual(contract["review_frames"], [1, 2, 3])
        scene = SimpleNamespace(
            render=SimpleNamespace(resolution_x=320, resolution_y=240,
                                   resolution_percentage=100, fps=24,
                                   engine="BLENDER_EEVEE"),
            view_settings=SimpleNamespace(view_transform="AgX"),
            frame_start=1, frame_end=3,
            camera=SimpleNamespace(name="Hero camera"),
            objects={entry["name"]: object() for entry in self.spec["objects"]},
        )
        shot_spec.validate_scene(scene, self.spec, contract)
        scene.render.fps = 30
        with self.assertRaisesRegex(ValueError, "timing or dimensions"):
            shot_spec.validate_scene(scene, self.spec, contract)

    def test_unknown_object_and_missing_action_review_fail(self):
        invalid = copy.deepcopy(self.spec)
        invalid["beats"][1]["object_ids"] = ["unknown"]
        with self.assertRaisesRegex(ValueError, "Invalid beat"):
            shot_spec.validate_spec(invalid, EXAMPLE.parent)
        invalid = copy.deepcopy(self.spec)
        invalid["review_states"] = ["initial", "result", "result"]
        with self.assertRaisesRegex(ValueError, "Review states"):
            shot_spec.validate_spec(invalid, EXAMPLE.parent)

    def test_imported_asset_requires_safe_path_hash_and_license(self):
        invalid = copy.deepcopy(self.spec)
        invalid["assets"] = [{"id": "external", "origin": "licensed", "license": "", "path": "../other.glb"}]
        with self.assertRaisesRegex(ValueError, "origin or license"):
            shot_spec.validate_spec(invalid, EXAMPLE.parent)
        invalid["assets"][0]["license"] = "Private-use asset"
        with self.assertRaisesRegex(ValueError, "escapes the shot or is missing"):
            shot_spec.validate_spec(invalid, EXAMPLE.parent)

    def test_existing_gallery_specs_remain_readable(self):
        legacy = json.loads((ROOT / "examples" / "clamp.json").read_text(encoding="utf-8"))
        contract = shot_spec.validate_spec(legacy, EXAMPLE.parent)
        self.assertEqual(contract["schema_version"], 1)
        self.assertIn("Lead screw", contract["required_objects"])


if __name__ == "__main__":
    unittest.main()
