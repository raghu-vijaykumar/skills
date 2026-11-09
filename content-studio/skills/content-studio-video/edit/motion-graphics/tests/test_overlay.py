import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "motion_overlay", Path(__file__).parents[1] / "scripts" / "overlay.py")
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)


class OverlayTest(unittest.TestCase):
    def test_rejects_cues_beyond_video(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mp4"
            source.touch()
            data = {"source": str(source), "events": [
                {"kind": "ingredient", "start": 9, "end": 12, "label": "Rice",
                 "action": "ADD", "evidence": "Visible rice"}]}
            probe = {"format": {"duration": "10"}, "streams": [
                {"codec_type": "video"}, {"codec_type": "audio"}]}
            with patch.object(overlay, "probe", return_value=probe):
                with self.assertRaisesRegex(ValueError, "outside the source duration"):
                    overlay.validate(data)

    def test_preview_shifts_cue_and_escapes_ass_controls(self):
        data = {"events": [{"kind": "ingredient", "start": 12, "end": 16,
                            "label": r"Rice{\bord20}", "action": "ADD", "evidence": "Visible rice"}]}
        rendered = overlay.ass(data, offset=10, length=5)
        self.assertIn("0:00:02.00,0:00:05.00", rendered)
        self.assertNotIn(r"{\bord20}", rendered)
        self.assertIn("Rice(/bord20)", rendered)

    def test_kinetic_cues_keep_bilingual_text_and_emoji(self):
        data = {"events": [
            {"kind": "title", "start": 3, "end": 7, "label": "VEGETABLE PALAV", "kannada": "ತರಕಾರಿ ಪಲಾವ್"},
            {"kind": "ingredient_list", "start": 14, "end": 50,
             "items": [{"at": 14, "label": "Palak", "kannada": "ಪಾಲಕ್ ಸೊಪ್ಪು"},
                       {"at": 20, "label": "Onions"}]},
            {"kind": "leaves", "start": 218, "end": 224,
             "pairs": [{"english": "Palak", "kannada": "ಪಾಲಕ್ ಸೊಪ್ಪು"},
                       {"english": "Methi", "kannada": "ಮೆಂತ್ಯ ಸೊಪ್ಪು"},
                       {"english": "Coriander", "kannada": "ಕೊತ್ತಂಬರಿ ಸೊಪ್ಪು"}]},
            {"kind": "cta", "start": 482, "end": 491,
             "beats": [{"label": "LIKE", "emoji": "👍"},
                       {"label": "SHARE", "emoji": "📤"},
                       {"label": "SUBSCRIBE", "emoji": "🔔"}]}]}
        rendered = overlay.ass(data)
        # The cue data drives text and retains the script and emoji characters in ASS.
        for expected in ("VEGETABLE", "PALAV", "ತರಕಾರಿ ಪಲಾವ್", "ಪಾಲಕ್ ಸೊಪ್ಪು",
                         "ಮೆಂತ್ಯ ಸೊಪ್ಪು", "ಕೊತ್ತಂಬರಿ ಸೊಪ್ಪು", "👍", "📤", "🔔"):
            self.assertIn(expected, rendered)
        self.assertIn("0:00:14.00,0:00:50.00", rendered)

    def test_location_card_has_pin_and_escapes_place_name(self):
        event = {"kind": "location", "start": 12, "end": 15,
                 "label": r"Gold {Souk}", "evidence": "Gate sign visible"}
        rendered = overlay.ass({"events": [event]}, canvas=(1920, 1080))
        self.assertIn("0:00:12.00,0:00:15.00", rendered)
        self.assertIn("Gold (Souk)", rendered)
        self.assertNotIn("Gold {Souk}", rendered)
        self.assertIn("m 23 0 b 36 0", rendered)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mp4"
            source.touch()
            probe = {"format": {"duration": "30"}, "streams": [
                {"codec_type": "video", "width": 1920, "height": 1080}]}
            with patch.object(overlay, "probe", return_value=probe):
                checked = overlay.validate({"source": str(source), "events": [event]})
                self.assertEqual(len(checked[2]), 1)
                with self.assertRaisesRegex(ValueError, "short place name"):
                    overlay.validate({"source": str(source), "events": [
                        {**event, "evidence": ""}]})

    def test_rejects_out_of_order_ingredient_list(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mp4"
            source.touch()
            data = {"source": str(source), "events": [{"kind": "ingredient_list", "start": 14, "end": 50,
                    "items": [{"at": 23, "label": "Beans"}, {"at": 20, "label": "Onions"}]}]}
            probe = {"format": {"duration": "60"}, "streams": [
                {"codec_type": "video"}, {"codec_type": "audio"}]}
            with patch.object(overlay, "probe", return_value=probe):
                with self.assertRaisesRegex(ValueError, "must be chronological"):
                    overlay.validate(data)

    def test_ingredient_heading_can_be_changed_without_changing_default(self):
        event = {"kind": "ingredient_list", "start": 2, "end": 5,
                 "items": [{"at": 2, "label": "Rice"}], "heading": "INGREDIENTS"}
        rendered = overlay.ass({"events": [event]})
        self.assertIn("}INGREDIENTS\n", rendered)
        self.assertNotIn("ONE BY ONE", rendered)
        del event["heading"]
        self.assertIn("INGREDIENTS  /  ONE BY ONE", overlay.ass({"events": [event]}))

    def test_effect_presets_conceal_midpoint_and_scale_to_portrait(self):
        data = {"events": [
            {"kind": "effect", "preset": "flash", "start": 1, "end": 1.4},
            {"kind": "effect", "preset": "swipe", "start": 2, "end": 2.6,
             "color": "#123456", "accent": "#ABCDEF"},
            {"kind": "effect", "preset": "shutter", "start": 3, "end": 3.6},
            {"kind": "effect", "preset": "speed-lines", "start": 4, "end": 4.5},
            {"kind": "effect", "preset": "frame-pop", "start": 5, "end": 5.5},
        ]}
        rendered = overlay.ass(data, canvas=(608, 1080))
        self.assertIn("PlayResX: 608", rendered)
        self.assertIn("\\move(-608,0,0,0,0,252)", rendered)
        self.assertIn("\\move(0,0,608,0,0,252)", rendered)
        self.assertIn("\\1c&H563412&", rendered)
        self.assertIn("0:00:03.00,0:00:03.35", rendered)
        self.assertIn("0:00:03.35,0:00:03.60", rendered)

    def test_effect_validation_rejects_unknown_or_unsafe_cues(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mp4"
            source.touch()
            probe = {"format": {"duration": "10"}, "streams": [
                {"codec_type": "video"}, {"codec_type": "audio"}]}
            event = {"kind": "effect", "preset": "wipe", "start": 1, "end": 1.4}
            with patch.object(overlay, "probe", return_value=probe):
                with self.assertRaisesRegex(ValueError, "unsupported preset"):
                    overlay.validate({"source": str(source), "events": [event]})
                event = {**event, "preset": "swipe", "color": "red"}
                with self.assertRaisesRegex(ValueError, "invalid color"):
                    overlay.validate({"source": str(source), "events": [event]})
                event = {**event, "color": "#123456", "end": 1.1}
                with self.assertRaisesRegex(ValueError, "at least 0.30"):
                    overlay.validate({"source": str(source), "events": [event]})

    def test_hlg_render_preserves_source_signal_and_audio(self):
        video = {"width": 3840, "height": 2160, "pix_fmt": "yuv420p10le",
                 "color_primaries": "bt2020", "color_transfer": "arib-std-b67",
                 "color_space": "bt2020nc"}
        command = overlay.render_command(Path("source.mp4"), Path("review.mp4"),
                                         Path("overlay.ass"), 0, 497.7, video, "nvenc")
        joined = " ".join(command)
        self.assertIn("ass=overlay.ass,format=p010le", joined)
        self.assertIn("-color_trc arib-std-b67", joined)
        self.assertIn("-color_primaries bt2020", joined)
        self.assertIn("-colorspace bt2020nc", joined)
        self.assertIn("-c:a copy", joined)
        self.assertNotIn("zscale", joined)
        self.assertNotIn("tonemap", joined)
        self.assertNotIn("scale=", joined)

    def test_video_only_effect_keeps_a_silent_render_silent(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "silent.mp4"
            source.touch()
            data = {"source": str(source), "events": [
                {"kind": "effect", "preset": "frame-pop", "start": 1, "end": 1.5}]}
            video = {"codec_type": "video", "width": 1080, "height": 1920,
                     "pix_fmt": "yuv420p"}
            probe = {"format": {"duration": "3"}, "streams": [video]}
            with patch.object(overlay, "probe", return_value=probe):
                _, _, _, checked, has_audio = overlay.validate(data)
            self.assertFalse(has_audio)
            command = overlay.render_command(source, Path("review.mp4"), Path("overlay.ass"),
                                             0, 3, checked, "x264", has_audio)
            self.assertNotIn("0:a:0", command)
            self.assertNotIn("-c:a", command)

    def test_dolby_vision_requires_explicit_preview_decision(self):
        video = {"side_data_list": [{"side_data_type": "DOVI configuration record",
                                     "rpu_present_flag": 1}]}
        self.assertTrue(overlay.has_dolby_vision(video))
        with self.assertRaisesRegex(ValueError, "RPU cannot survive"):
            overlay.require_preview_color_decision(video, False)
        overlay.require_preview_color_decision(video, True)


if __name__ == "__main__":
    unittest.main()
