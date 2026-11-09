import importlib.util
import tempfile
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "cta_stock", Path(__file__).parents[1] / "scripts" / "cta_stock.py")
cta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cta)


class StockCTATest(unittest.TestCase):
    def test_states_follow_like_share_subscribe_bell_order(self):
        self.assertFalse(cta.states(0.5)["like"])
        self.assertTrue(cta.states(0.8)["like"])
        self.assertFalse(cta.states(0.8)["share"])
        self.assertTrue(cta.states(1.5)["share"])
        self.assertTrue(cta.states(2.5)["subscribed"])
        self.assertTrue(cta.states(3.5)["bell"])

    def test_frame_is_transparent_outside_original_graphic(self):
        frame = cta.draw_frame(2.5, 1280, 720, 5.0, "top-right")
        self.assertEqual(frame.size, (1280, 720))
        self.assertEqual(frame.getpixel((0, 0))[3], 0)
        self.assertGreater(frame.getchannel("A").getbbox()[2], 500)
        self.assertIsNone(cta.draw_frame(0, 1280, 720, 5.0,
                                         "top-right").getchannel("A").getbbox())

    def test_refuses_to_overwrite_asset(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "cta.mov"
            output.touch()
            with self.assertRaisesRegex(ValueError, "already exists"):
                cta.render(output, 3840, 2160, 30, 5.0, "top-right")


if __name__ == "__main__":
    unittest.main()
