"""Real FFmpeg fixtures for the guarded cuts-only candidate."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import smart_cut


class SmartCutTest(unittest.TestCase):
    def make_source(self, path: Path, codec: str = "libx264", transfer: str = "bt709",
                    vfr: bool = False) -> None:
        picture = "testsrc2=size=320x180:rate=30:duration=10"
        filters = []
        if vfr:
            # The one-frame gap is still decodable but violates the CFR guard.
            filters.append("setpts=if(gte(N\\,60)\\,PTS+0.2/TB\\,PTS)")
        filters.append(f"setparams=color_primaries=bt709:color_trc={transfer}:colorspace=bt709")
        command = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                   "-f", "lavfi", "-i", picture, "-f", "lavfi", "-i",
                   "sine=frequency=440:sample_rate=48000:duration=10",
                   "-vf", ",".join(filters), "-c:v", codec, "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-b:a", "128k", "-fps_mode", "passthrough"]
        if codec == "libx264":
            command += ["-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
                        "-x264-params", f"colorprim=bt709:transfer={transfer}:colormatrix=bt709"]
        command += ["-shortest", str(path)]
        subprocess.run(command, check=True, capture_output=True)

    def test_between_keyframes_copies_interior_and_checks_picture_audio(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            root = Path(temp)
            source, output, report = root / "source.mp4", root / "candidate.mp4", root / "report.json"
            self.make_source(source)
            result = smart_cut.render(source, output, report, ["2.333333-4.666667"])
            self.assertEqual(result["status"], "PASS_CANDIDATE", result.get("reason"))
            self.assertEqual(result["frame_proof"]["decoded_count"], 230)
            self.assertEqual(result["baseline"]["picture_frames_reencoded"], 230)
            self.assertGreater(result["candidate_plan"]["copy_fraction"], 0.5)
            self.assertEqual(result["human_boundary_review"], "pending")
            self.assertEqual(result["exact_master_review"], "pending")
            self.assertLess(result["frame_proof"]["maximum_sampled_luma_mae"], 1)
            self.assertGreater(result["copied_packets"]["identical_interior_packets"], 150)
            self.assertGreater(result["copied_packets"]["rewritten_first_packets"], 0)
            self.assertEqual(len(result["audio_proof"]["boundary_windows"]), 3)
            self.assertGreater(min(item["correlation"] for item in
                                   result["audio_proof"]["boundary_windows"]), 0.94)
            self.assertTrue(output.is_file())
            self.assertEqual(len(result["candidate_sha256"]), 64)
            self.assertEqual(json.loads(report.read_text())["source_sha256"], result["source_sha256"])

    def test_rejects_hdr_incompatible_codec_and_variable_timing(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            root = Path(temp)
            for name, options, reason in (
                ("hdr", {"transfer": "smpte2084"}, "HDR"),
                ("codec", {"codec": "mpeg4"}, "H.264"),
                ("vfr", {"vfr": True}, "frame"),
            ):
                with self.subTest(name=name):
                    source = root / f"{name}.mp4"
                    self.make_source(source, **options)
                    with self.assertRaisesRegex(smart_cut.SmartCutError, reason):
                        smart_cut.source_profile(source)

    def test_dolby_metadata_and_unaligned_cut_fail_closed(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            source = Path(temp) / "source.mp4"
            self.make_source(source)
            _, _, frames, rate = smart_cut.source_profile(source)
            with self.assertRaisesRegex(smart_cut.SmartCutError, "align"):
                smart_cut.retained_frames(len(frames) / float(rate),
                                          ["2.31-4.7"], rate, len(frames))
            video = {"side_data_list": [{"side_data_type": "DOVI configuration record"}]}
            self.assertTrue(smart_cut.editing.is_dolby(video))


if __name__ == "__main__":
    unittest.main()
