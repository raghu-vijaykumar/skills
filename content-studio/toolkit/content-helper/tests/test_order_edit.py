import csv
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import editing
import ordering
import preprocess


class OrderingTest(unittest.TestCase):
    def test_legacy_processed_folder_follows_original_camera_name(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            legacy = root / "027 - IMG_1003.MOV"
            legacy.mkdir()
            (legacy / "report.json").write_text("{}", encoding="utf-8")
            stable = ordering.analysis_folder(root, "028 - IMG_1003.MOV")
            self.assertEqual(stable.name, "IMG_1003.MOV")
            self.assertTrue((stable / "report.json").exists())
            self.assertFalse(legacy.exists())

    def test_preprocess_refreshes_order_before_selecting_a_clip(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch) / "out-of-office" / "drafts" / "trip"
            draft.mkdir(parents=True)
            (draft / "VID20260111050000.mp4").touch()
            (draft / "VID20260111050100.mp4").touch()
            args = SimpleNamespace(channel="out-of-office", draft="trip", path=None,
                                   clip=None, out=None, utc_offset="+04:00")
            cfg = {"workspace": str(Path(scratch)),
                   "channels": {"out-of-office": {"name": "Out of Office"}}}
            seen = []
            with patch.object(ordering, "probe", return_value=(1.0, None)), \
                 patch.object(preprocess, "process_clip",
                              side_effect=lambda source, *_: seen.append(source.name)):
                self.assertEqual(preprocess.run(cfg, args, lambda _: None), 0)
                (draft / "VID20260111050030.mp4").touch()
                args.clip = "VID20260111050030.mp4"
                self.assertEqual(preprocess.run(cfg, args, lambda _: None), 0)
            self.assertEqual(seen, ["001 - VID20260111050000.mp4",
                                    "002 - VID20260111050100.mp4",
                                    "002 - VID20260111050030.mp4"])

    def test_new_clip_reorders_existing_names_and_keeps_prior_estimate(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch)
            first = draft / "VID20260111050000.mp4"
            last = draft / "IMG_1003.MOV"
            first.touch()
            last.touch()

            def metadata(path):
                times = {"IMG_1003.MOV": datetime(2026, 1, 11, 1, 3, tzinfo=timezone.utc),
                         "VID20260111050100.mp4": datetime(2026, 1, 11, 1, 1, tzinfo=timezone.utc)}
                return 1.0, times.get(ordering.original_name(path.name))

            with patch.object(ordering, "probe", side_effect=metadata):
                rows = ordering.ensure_current(draft, lambda _: None, utc_offset="+04:00")
                self.assertEqual([r["original_name"] for r in rows],
                                 [first.name, last.name])
                rows[1]["time_estimated"] = "yes"
                ordering.apply_order(draft, rows, [])
                (draft / "VID20260111050100.mp4").touch()
                preview = ordering.ensure_current(draft, lambda _: None,
                                                  utc_offset="+04:00", dry_run=True)
                self.assertTrue((draft / "002 - IMG_1003.MOV").exists())
                rows = ordering.ensure_current(draft, lambda _: None, utc_offset="+04:00")
            self.assertEqual([r["original_name"] for r in rows],
                             [first.name, "VID20260111050100.mp4", last.name])
            self.assertEqual(rows[2]["time_estimated"], "yes")
            self.assertEqual(preview, rows)
            self.assertTrue((draft / "003 - IMG_1003.MOV").exists())
            self.assertEqual(ordering.ensure_current(draft, lambda _: None), rows)
            self.assertFalse(list(draft.glob(".order-*.tmp")))
            with (draft / "_timeline.csv").open(newline="", encoding="utf-8") as fh:
                self.assertEqual(len(list(csv.DictReader(fh))), 3)


class EditingTest(unittest.TestCase):
    def make_video(self, path, color):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                        "-f", "lavfi", "-i", f"color=c={color}:s=320x240:r=30:d=1",
                        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                        "-shortest", str(path)], check=True, capture_output=True)

    def test_trim_cut_join_real_media(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "source.mp4"
            self.make_video(source, "red")
            duration, video, audio = editing.probe(source)
            trimmed = root / "trim.mp4"
            editing.render_ranges(source, trimmed, [(0.2, 0.8)], video, audio)
            self.assertAlmostEqual(editing.probe(trimmed)[0], 0.6, delta=0.12)
            cut = root / "cut.mp4"
            editing.render_ranges(source, cut,
                                  editing.cut_ranges(duration, ["0.3-0.6"]), video, audio)
            self.assertAlmostEqual(editing.probe(cut)[0], 0.7, delta=0.15)
            joined = root / "joined.mp4"
            editing.join([(trimmed, None), (cut, None)], joined, lambda _: None)
            actual, output_video, output_audio = editing.probe(joined)
            self.assertAlmostEqual(actual, 1.3, delta=0.3)
            self.assertEqual((output_video["width"], output_video["height"]), (1920, 1080))
            self.assertTrue(output_audio)

    def test_dolby_cut_requires_explicit_sdr(self):
        with self.assertRaisesRegex(editing.EditError, "require --sdr"):
            editing.render_ranges(Path("in.mov"), Path("out.mp4"), [(0, 1)],
                                  {"side_data_list": [{"side_data_type": "DOVI configuration record"}]},
                                  True)


if __name__ == "__main__":
    unittest.main()
