"""Cover the preview inputs before Blender starts rendering."""

from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from headless_preview import inspect_scene, select_frames


class HeadlessPreviewTests(unittest.TestCase):
    def test_inclusive_range_and_explicit_frame_order(self):
        self.assertEqual(list(select_frames(None, [2, 4], 1, 5)), [2, 3, 4])
        self.assertEqual(select_frames([4, 2], None, 1, 5), [4, 2])

    def test_reject_duplicates_and_out_of_range_frames(self):
        for requested, span in (([2, 2], None), ([6], None), (None, [3, 2]), (None, [0, 2])):
            with self.subTest(requested=requested, span=span), self.assertRaises(ValueError):
                select_frames(requested, span, 1, 5)

    def test_require_camera_and_teaching_objects(self):
        with self.assertRaisesRegex(ValueError, "render camera"):
            inspect_scene(SimpleNamespace(camera=None), ["rotor"])
        scene = SimpleNamespace(camera=object(), objects={"rotor": object()})
        with self.assertRaisesRegex(ValueError, "outlet"):
            inspect_scene(scene, ["rotor", "outlet"])
        inspect_scene(scene, ["rotor"])
