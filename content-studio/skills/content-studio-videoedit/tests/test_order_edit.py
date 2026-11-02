import csv
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import dedupe
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
            (draft / "VID20260111050000.mp4").write_bytes(b"first clip")
            (draft / "VID20260111050100.mp4").write_bytes(b"second clip")
            args = SimpleNamespace(channel="out-of-office", draft="trip", path=None,
                                   clip=None, out=None, utc_offset="+04:00")
            cfg = {"workspace": str(Path(scratch)),
                   "channels": {"out-of-office": {"name": "Out of Office"}}}
            seen = []
            with patch.object(ordering, "probe", return_value=(1.0, None)), \
                 patch.object(preprocess, "process_clip",
                              side_effect=lambda source, *_: seen.append(source.name)):
                self.assertEqual(preprocess.run(cfg, args, lambda _: None), 0)
                (draft / "VID20260111050030.mp4").write_bytes(b"third clip!")
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


class DedupeTest(unittest.TestCase):
    def make_video(self, path, frequency):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                        "-f", "lavfi", "-i", "color=c=red:s=320x240:r=30:d=1",
                        "-f", "lavfi", "-i",
                        f"sine=frequency={frequency}:sample_rate=48000:duration=1",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                        "-shortest", str(path)], check=True, capture_output=True)

    def test_exact_duplicate_is_quarantined_by_content(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch)
            keep = draft / "IMG_1001.MOV"
            copy = draft / "IMG_1002.MOV"
            payload = b"same camera bytes" * 50
            keep.write_bytes(payload)
            copy.write_bytes(payload)
            logs = []
            report = dedupe.scan(draft, logs.append)
            self.assertTrue(keep.exists())
            self.assertFalse(copy.exists())
            self.assertEqual(report["exact"][0]["kept"], "IMG_1001.MOV")
            self.assertEqual(report["exact"][0]["removed"], ["IMG_1002.MOV"])
            moved = report["quarantined"][0]
            self.assertEqual(moved["reason"], "exact")
            self.assertTrue((draft / moved["path"]).exists())
            self.assertEqual(report["aliases"]["img_1002.mov"], "IMG_1001.MOV")
            self.assertTrue((draft / "analysis" / "duplicates" / "report.json").exists())
            again = dedupe.scan(draft, logs.append)
            self.assertEqual(again["aliases"]["img_1002.mov"], "IMG_1001.MOV")
            self.assertEqual(again["quarantined"][0]["path"], moved["path"])

    def test_timeline_order_chooses_the_kept_copy(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch)
            first = draft / "001 - IMG_1002.MOV"
            second = draft / "002 - IMG_1001.MOV"
            payload = b"timeline duplicate bytes"
            first.write_bytes(payload)
            second.write_bytes(payload)
            rows = [{"order": "1", "new_name": first.name,
                     "original_name": "IMG_1002.MOV"},
                    {"order": "2", "new_name": second.name,
                     "original_name": "IMG_1001.MOV"}]
            with (draft / "_timeline.csv").open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=ordering.FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            report = dedupe.scan(draft, lambda _: None)
            self.assertEqual(report["exact"][0]["kept"], first.name)
            self.assertTrue(first.exists())
            self.assertFalse(second.exists())
            self.assertEqual(report["aliases"]["img_1001.mov"], "IMG_1002.MOV")

    def test_near_duplicate_is_reviewed_then_quarantined_when_approved(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch)
            keep = draft / "IMG_2001.mp4"
            near = draft / "IMG_2002.mp4"
            self.make_video(keep, 440)
            self.make_video(near, 880)
            logs = []
            report = dedupe.scan(draft, logs.append)
            self.assertEqual(report["quarantined"], [])
            self.assertEqual(len(report["near"]), 1)
            self.assertEqual(report["near"][0]["action"], "review")
            review = draft / "analysis" / "duplicates" / "review.csv"
            with review.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual([row["duplicate"] for row in rows], ["IMG_2002.mp4"])
            self.assertEqual(rows[0]["remove"], "")
            rows[0]["remove"] = "yes"
            with review.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=dedupe.REVIEW_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            report = dedupe.scan(draft, logs.append)
            self.assertTrue(keep.exists())
            self.assertFalse(near.exists())
            self.assertEqual(report["quarantined"][0]["reason"], "near-duplicate")
            self.assertEqual(report["near"][0]["action"], "quarantined")
            self.assertEqual(report["aliases"]["img_2002.mp4"], "IMG_2001.mp4")
            with review.open(newline="", encoding="utf-8") as fh:
                self.assertEqual(list(csv.DictReader(fh)), [])

    def test_preprocess_folder_runs_dedupe_and_ordering_in_place(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            folder = Path(scratch) / "skilltest"
            folder.mkdir()
            first = folder / "IMG_1001.MOV"
            copy = folder / "IMG_1002.MOV"
            third = folder / "IMG_1003.MOV"
            first.write_bytes(b"same camera bytes")
            copy.write_bytes(b"same camera bytes")
            third.write_bytes(b"different camera bytes")
            args = SimpleNamespace(channel=None, draft=None, folder=str(folder),
                                   path=None, clip=None, out=None,
                                   utc_offset="+00:00")
            seen = []

            def metadata(path):
                times = {"IMG_1001.MOV": datetime(2026, 1, 11, 1, 1, tzinfo=timezone.utc),
                         "IMG_1003.MOV": datetime(2026, 1, 11, 1, 2, tzinfo=timezone.utc)}
                return 1.0, times.get(ordering.original_name(path.name))

            with patch.object(ordering, "probe", side_effect=metadata), \
                 patch.object(preprocess, "process_clip",
                              side_effect=lambda source, *_: seen.append(source.name)):
                self.assertEqual(preprocess.run({}, args, lambda _: None), 0)
            self.assertEqual(seen, ["001 - IMG_1001.MOV", "002 - IMG_1003.MOV"])
            self.assertFalse(copy.exists())
            self.assertTrue((folder / "analysis" / "duplicates" / "report.json").exists())
            self.assertTrue((folder / "processed-clips").is_dir())
            with (folder / "_timeline.csv").open(newline="", encoding="utf-8") as fh:
                self.assertEqual(len(list(csv.DictReader(fh))), 2)

    def test_preprocess_rejects_multiple_input_modes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            args = SimpleNamespace(channel=None, draft="trip", folder=str(Path(scratch)),
                                   path="clip.mp4", clip=None, out=None,
                                   utc_offset="+00:00")
            logs = []
            self.assertEqual(preprocess.run({}, args, logs.append), 1)
            self.assertIn("only one of --path, --draft, or --folder", logs[-1])

    def test_final_rejects_review_and_dolby_flags(self):
        for flag in ("apply_review", "dv_proof", "dv_approved"):
            args = SimpleNamespace(channel=None, draft=None, folder=None, path=None,
                                   clip=None, out=None, utc_offset=None, final=True,
                                   apply_review=False, dv_proof=False, dv_approved=False)
            setattr(args, flag, True)
            logs = []
            self.assertEqual(preprocess.run({}, args, logs.append), 1)
            self.assertIn("--final cannot be combined", logs[-1])

    def test_final_mode_joins_clip_exports_into_one_video(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            folder = Path(scratch) / "skilltest"
            folder.mkdir()
            (folder / "IMG_1001.MOV").write_bytes(b"first clip")
            (folder / "IMG_1002.MOV").write_bytes(b"second clip")
            args = SimpleNamespace(channel=None, draft=None, folder=str(folder),
                                   path=None, clip=None, out=None, utc_offset="+00:00",
                                   final=True, apply_review=False, dv_proof=False,
                                   dv_approved=False)
            finals = [folder / "processed-clips" / "IMG_1001.MOV" / "final.mp4",
                      folder / "processed-clips" / "IMG_1002.MOV" / "final.mp4"]
            joined = []

            def fake_final(source, *rest):
                name = ordering.original_name(source.name)
                return next(path for path in finals if path.parent.name == name)

            with patch.object(ordering, "probe", return_value=(1.0, None)), \
                 patch.object(preprocess, "final_clip", side_effect=fake_final), \
                 patch.object(editing, "join_normalized",
                              side_effect=lambda sources, target: joined.append(
                                  (sources, target))):
                self.assertEqual(preprocess.run({}, args, lambda _: None), 0)
            self.assertEqual(joined, [(finals, folder / "final-video.mp4")])

    def test_preprocess_clip_resolves_a_quarantined_name(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            draft = Path(scratch) / "out-of-office" / "drafts" / "trip"
            draft.mkdir(parents=True)
            keep = draft / "IMG_1001.MOV"
            copy = draft / "IMG_1002.MOV"
            keep.write_bytes(b"same camera bytes")
            copy.write_bytes(b"same camera bytes")
            args = SimpleNamespace(channel="out-of-office", draft="trip", path=None,
                                   clip="IMG_1002.MOV", out=None, utc_offset="+04:00")
            cfg = {"workspace": str(Path(scratch)),
                   "channels": {"out-of-office": {"name": "Out of Office"}}}
            seen = []
            with patch.object(ordering, "probe", return_value=(1.0, None)), \
                 patch.object(preprocess, "process_clip",
                              side_effect=lambda source, *_: seen.append(source.name)):
                self.assertEqual(preprocess.run(cfg, args, lambda _: None), 0)
            self.assertEqual(seen, ["001 - IMG_1001.MOV"])
            self.assertTrue((draft / "001 - IMG_1001.MOV").exists())
            self.assertFalse(copy.exists())


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

    def test_normalized_segment_cuts_and_joins_16_9_exports(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "source.mp4"
            self.make_video(source, "red")
            first = root / "first.mp4"
            editing.normalized_segment(source, None, first, ranges=[(0.2, 0.8)])
            second = root / "second.mp4"
            editing.normalized_segment(source, None, second, ranges=[(0.1, 0.5)])
            actual, video, audio = editing.probe(first)
            self.assertAlmostEqual(actual, 0.6, delta=0.12)
            self.assertEqual((video["width"], video["height"]), (1920, 1080))
            self.assertTrue(audio)
            joined = root / "final-video.mp4"
            editing.join_normalized([first, second], joined)
            actual, video, audio = editing.probe(joined)
            self.assertAlmostEqual(actual, 1.0, delta=0.2)
            self.assertEqual((video["width"], video["height"]), (1920, 1080))
            self.assertTrue(audio)

    def test_final_clip_reuses_voice_and_cuts_review_spans(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            source = root / "001 - IMG_1001.MOV"
            self.make_video(source, "red")
            output = root / "processed-clips"
            folder = ordering.analysis_folder(output, source.name)
            folder.mkdir(parents=True)
            (folder / "report.json").write_text(json.dumps({
                "source": str(source), "source_bytes": source.stat().st_size,
                "denoise_engine": "ffmpeg", "status": "dv_original_video_retained",
            }), encoding="utf-8")
            (folder / "enhanced-voice.wav").write_bytes(b"voice")
            with (folder / "review.csv").open("w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["id", "start", "end", "score", "remove", "notes"])
                writer.writerow([1, 0.2, 0.4, 100, "", ""])
            seen = {}

            def fake_render(source, sidecar, target, ranges=None):
                seen["sidecar"] = sidecar
                seen["ranges"] = ranges
                target.write_bytes(b"final")

            with patch.object(editing, "normalized_segment", side_effect=fake_render), \
                 patch.object(editing, "probe",
                              return_value=(0.8, {"width": 1920, "height": 1080}, True)):
                target = preprocess.final_clip(source, output,
                                               SimpleNamespace(force=False, denoise="auto"),
                                               lambda _: None)
            self.assertEqual(target, folder / "final.mp4")
            self.assertTrue(target.exists())
            self.assertEqual(seen["sidecar"], folder / "enhanced-voice.wav")
            self.assertEqual(len(seen["ranges"]), 2)
            self.assertAlmostEqual(seen["ranges"][0][1], 0.2)
            self.assertAlmostEqual(seen["ranges"][1][0], 0.4)
            final_report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(final_report["status"], "final_ready")
            self.assertEqual(final_report["final_output"], "final.mp4")
            self.assertEqual(final_report["final_cuts"], [[0.2, 0.4]])
            self.assertGreater(final_report["final_removed_seconds"], 0)

    def test_dolby_cut_requires_explicit_sdr(self):
        with self.assertRaisesRegex(editing.EditError, "require --sdr"):
            editing.render_ranges(Path("in.mov"), Path("out.mp4"), [(0, 1)],
                                  {"side_data_list": [{"side_data_type": "DOVI configuration record"}]},
                                  True)


if __name__ == "__main__":
    unittest.main()
