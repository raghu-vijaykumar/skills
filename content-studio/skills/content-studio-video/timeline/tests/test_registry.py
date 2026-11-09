import json
import sys
import unittest
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FOLDER / "scripts"))
import model  # noqa: E402


class CapabilityRegistryTests(unittest.TestCase):
    def test_registry_matches_timeline_validator(self):
        registry = json.loads((FOLDER / "methods.json").read_text())
        supported = {entry["id"] for entry in registry["methods"]
                     if entry["status"] == "supported"}
        implemented = (model.PICTURE_METHODS | model.GRAPHIC_METHODS
                       | model.AUDIO_METHODS | set(model.JOIN_TRANSITIONS)
                       | model.POINT_TRANSITIONS | {"timeline-delivery"})
        self.assertEqual(supported, implemented)
        self.assertEqual(
            next(entry for entry in registry["methods"]
                 if entry["id"] == "upscale-real-esrgan")["status"],
            "unsupported")

    def test_transition_catalog_and_single_render_cover_same_methods(self):
        catalog = json.loads((FOLDER.parent / "edit" / "transitions" /
                              "presets" / "transitions.json").read_text())
        for entry in catalog["transitions"]:
            with self.subTest(entry=entry["id"]):
                if "join" in entry["modes"]:
                    self.assertEqual(model.JOIN_TRANSITIONS[entry["id"]],
                                     entry["xfade"])
                if "point" in entry["modes"]:
                    self.assertIn(entry["id"], model.POINT_TRANSITIONS)
        self.assertFalse([entry for entry in catalog["transitions"]
                          if entry["fidelity"] == "catalog-only"])


if __name__ == "__main__":
    unittest.main()
