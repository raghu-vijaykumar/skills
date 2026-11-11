import importlib.util
import tempfile
import unittest
import wave
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
            self.assertEqual(library.validate_library(library.STOCK_ASSETS),
                             library.STOCK_ASSETS.resolve())
            with self.assertRaisesRegex(ValueError, "stock skill"):
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

    def test_sfx_unknown_rights_is_reference_only_with_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            source = base / "impact.wav"
            with wave.open(str(source), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(48000)
                wav.writeframes(b"\0\0" * 4800)
            root = base / "library"
            item = library.add(root, source, "Impact", "sfx", "unknown", "Example creator",
                               ["impact", "reel"], source_url="https://www.instagram.com/reel/abc/",
                               source_start=1.2, source_end=1.3, source_sha256="a" * 64)
            self.assertEqual(item["reuse_status"], "reference-only")
            self.assertEqual(item["effect_review"], "pending")
            self.assertAlmostEqual(item["media"]["duration_seconds"], .1)
            self.assertIn("[source](https://www.instagram.com/reel/abc/)",
                          (root / "README.md").read_text(encoding="utf-8"))
            self.assertIn("`media/sfx/", (root / "README.md").read_text(encoding="utf-8"))
            self.assertNotIn("[media](media/sfx/", (root / "README.md").read_text(encoding="utf-8"))
            self.assertEqual(library.read_catalogue(root)[0]["source_start_seconds"], 1.2)
            reviewed = library.review_sfx(root, item["id"], "unknown", "passed",
                                          "Listened to complete effect; no voice or music")
            self.assertEqual(reviewed["reuse_status"], "reference-only")
            cleared = library.review_sfx(root, item["id"], "permission", "passed",
                                         "Creator granted reuse permission")
            self.assertEqual(cleared["reuse_status"], "reusable")
            self.assertEqual(len(library.read_catalogue(root)), 1)
            sticker = base / "sticker.png"
            Image.new("RGBA", (2, 2), "red").save(sticker)
            with self.assertRaisesRegex(ValueError, "Unknown rights"):
                library.add(root, sticker, "Wrong", "sticker", "unknown", "Example", [])

    def test_reviewed_sound_profile_selects_matching_shot_but_preserves_dialogue(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "library"
            assets = [
                {"id": "laugh", "name": "Laughter", "kind": "sfx", "rights": "licensed", "effect_review": "passed",
                 "reuse_status": "reusable", "relative_path": "media/sfx/laugh.wav",
                 "media": {"duration_seconds": 1.5},
                 "sfx_profile": {"label": "Group laugh", "shot_tags": ["comic-payoff"],
                                 "identification_review": "passed"}},
                {"id": "beep", "name": "Beep", "kind": "sfx", "rights": "owned", "effect_review": "passed",
                 "reuse_status": "reusable", "relative_path": "media/sfx/beep.wav",
                 "media": {"duration_seconds": .4},
                 "sfx_profile": {"label": "Digital beep", "shot_tags": ["phone-activity"],
                                 "identification_review": "passed"}},
            ]
            manifest = {"schema_version": 1, "shots": [
                {"id": "S01", "start_seconds": 0, "end_seconds": 2,
                 "shot_tags": ["phone-activity"], "audio_context": "quiet"},
                {"id": "S02", "start_seconds": 2, "end_seconds": 4,
                 "shot_tags": ["comic-payoff"], "audio_context": "dialogue"},
                {"id": "S03", "start_seconds": 4, "end_seconds": 5,
                 "shot_tags": ["comic-payoff"], "audio_context": "quiet"},
            ]}
            output = library.suggest_sfx(assets, manifest)
            self.assertEqual(output["selections"][0]["candidate"]["asset_id"], "beep")
            self.assertIsNone(output["selections"][1]["candidate"])
            self.assertIsNone(output["selections"][2]["candidate"])
            self.assertFalse(output["timeline_changed"])
            self.assertTrue(all(row["approval_required"] for row in output["selections"]))

    def test_reference_effect_is_never_selected_for_delivery(self):
        reference = {"id": "reel-laugh", "name": "Reel laugh", "kind": "sfx",
                     "rights": "unknown",
                     "effect_review": "passed", "reuse_status": "reference-only",
                     "relative_path": "media/sfx/reel-laugh.wav",
                     "media": {"duration_seconds": 1},
                     "sfx_profile": {"label": "Laugh", "shot_tags": ["comic-payoff"],
                                     "identification_review": "passed"}}
        shots = {"schema_version": 1, "shots": [
            {"id": "S01", "start_seconds": 0, "end_seconds": 2,
             "shot_tags": ["comic-payoff"], "audio_context": "quiet"}]}
        self.assertIsNone(library.suggest_sfx([reference], shots)["selections"][0]["candidate"])
        candidate = library.suggest_sfx([reference], shots, "reference")["selections"][0]["candidate"]
        self.assertEqual(candidate["asset_id"], "reel-laugh")
        self.assertFalse(candidate["placement_allowed"])

    def test_sound_description_updates_metadata_without_media_change(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "library"
            root.mkdir()
            item = {"id": "sfx-1", "name": "Beep", "kind": "sfx", "rights": "unknown",
                    "creator": "Example", "tags": ["sfx"], "reuse_status": "reference-only",
                    "effect_review": "passed", "sha256": "a" * 64,
                    "relative_path": "media/sfx/sfx-1.wav",
                    "media": {"duration_seconds": .5}, "source_url": ""}
            library.write_catalogue(root, [item])
            updated = library.describe_sfx(root, "sfx-1", "Digital beep",
                                           ["phone-activity"], "Editor listened", "passed")
            self.assertEqual(updated["sfx_profile"]["shot_tags"], ["phone-activity"])
            self.assertEqual(updated["sha256"], "a" * 64)
            self.assertEqual(updated["reuse_status"], "reference-only")
            self.assertIn("Digital beep", (root / "README.md").read_text(encoding="utf-8"))
            pending = library.describe_sfx(root, "sfx-1", "Uncertain beep",
                                           ["phone-activity"], "Needs listening")
            self.assertEqual(pending["sfx_profile"]["identification_review"], "pending")
            self.assertIsNone(library.suggest_sfx([pending], {"schema_version": 1, "shots": [
                {"id": "S01", "start_seconds": 0, "end_seconds": 1,
                 "shot_tags": ["phone-activity"], "audio_context": "quiet"}]},
                "reference")["selections"][0]["candidate"])
            with self.assertRaisesRegex(ValueError, "lowercase slugs"):
                library.describe_sfx(root, "sfx-1", "Beep", ["bad tag"], "Editor listened")


if __name__ == "__main__":
    unittest.main()
