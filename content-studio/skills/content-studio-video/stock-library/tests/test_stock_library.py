import importlib.util
import tempfile
import unittest
from pathlib import Path
from PIL import Image


ROOT = Path(__file__).parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cta = load("cta")
library = load("library")


class CTAStyleTests(unittest.TestCase):
    def test_catalogue_gifs_show_each_variant(self):
        # A selectable design needs its own moving example in the public matrix.
        skill = ROOT.parent
        readme = (skill / "README.md").read_text(encoding="utf-8")
        for variant in cta.VARIANTS:
            self.assertIn(f"(previews/{variant}.gif)", readme)
            with Image.open(skill / "previews" / f"{variant}.gif") as preview:
                self.assertEqual(preview.size, (480, 270))
                self.assertGreaterEqual(preview.n_frames, 30)

    def test_all_variants_are_distinct_and_transparent(self):
        frames = {name: cta.draw_frame(2.5, 1280, 720, 5.0, "top-right", name)
                  for name in cta.VARIANTS}
        self.assertEqual(len(frames), 3)
        for frame in frames.values():
            self.assertEqual(frame.size, (1280, 720))
            self.assertEqual(frame.getpixel((0, 0))[3], 0)
            self.assertIsNotNone(frame.getchannel("A").getbbox())
        self.assertEqual(len({frame.tobytes() for frame in frames.values()}), 3)

    def test_default_matches_classic(self):
        self.assertEqual(cta.draw_frame(2.5, 1280, 720, 5.0, "center").tobytes(),
                         cta.draw_frame(2.5, 1280, 720, 5.0, "center",
                                        "classic-bar").tobytes())

    def test_invalid_variant_rejected(self):
        with self.assertRaises(ValueError):
            cta.draw_frame(2, 1280, 720, 5, "center", "unknown")

    def test_bell_animation_changes_after_subscription(self):
        for variant in ("minimal-pills", "bold-stack"):
            before = cta.draw_frame(3.1, 1280, 720, 5, "center", variant)
            ringing = cta.draw_frame(3.6, 1280, 720, 5, "center", variant)
            self.assertNotEqual(before.tobytes(), ringing.tobytes())


class AuthoredMediaTests(unittest.TestCase):
    def test_import_catalogue_and_deduplicate(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            source = base / "my-sticker.png"
            Image.new("RGBA", (32, 24), (255, 0, 0, 128)).save(source)
            root = base / "library"
            first = library.add(root, source, "My sticker", "sticker", "owned",
                                "Raghu", ["cooking", "smile"])
            second = library.add(root, source, "Duplicate", "sticker", "owned",
                                 "Raghu", [])
            self.assertEqual(first, second)
            self.assertEqual(len(library.read_catalogue(root)), 1)
            self.assertEqual(first["media"]["width"], 32)
            self.assertEqual((root / first["relative_path"]).read_bytes(), source.read_bytes())
            self.assertIn("My sticker", (root / "README.md").read_text(encoding="utf-8"))
            self.assertNotIn("Duplicate", (root / "README.md").read_text(encoding="utf-8"))

    def test_type_and_repo_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "clip.mp4"
            source.write_bytes(b"clip")
            with self.assertRaisesRegex(ValueError, "unsupported"):
                library.add(Path(folder) / "library", source, "Clip", "gif", "owned",
                            "Raghu", [])
            with self.assertRaisesRegex(ValueError, "outside"):
                library.validate_library(library.REPO_ROOT / "assets")

    def test_corrupt_image_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "bad.png"
            source.write_bytes(b"not a png")
            with self.assertRaisesRegex(ValueError, "cannot be decoded"):
                library.add(Path(folder) / "library", source, "Broken", "sticker",
                            "owned", "Raghu", [])

    def test_existing_media_inside_library_is_indexed_in_place(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "library"
            source = root / "media" / "sticker" / "my-original.png"
            source.parent.mkdir(parents=True)
            Image.new("RGBA", (12, 12), "#ff0000").save(source)
            item = library.add(root, source, "Original", "sticker", "owned",
                               "Raghu", [])
            self.assertEqual(item["relative_path"], "media/sticker/my-original.png")
            self.assertEqual(len(list(source.parent.glob("*.png"))), 1)


if __name__ == "__main__":
    unittest.main()
