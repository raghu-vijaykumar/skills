"""Unit tests for voice enrollment safety without requiring FFmpeg."""
import importlib.util
import json
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]/"scripts"/"voice.py"
spec=importlib.util.spec_from_file_location("voice_bootstrap",SOURCE)
voice=importlib.util.module_from_spec(spec);spec.loader.exec_module(voice)

class VoiceBootstrapTests(unittest.TestCase):
    def test_english_reference_requires_variant_and_valid_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            second = root / "take2.wav"
            third = root / "take3.wav"
            second.write_bytes(b"second")
            third.write_bytes(b"third")
            profile = {"references": {
                "take2": {"file": second.name, "sha256": voice.sha(second)},
                "take3": {"file": third.name, "sha256": voice.sha(third)},
            }}
            with self.assertRaisesRegex(SystemExit, "Choose --reference-variant"):
                voice.select_chatterbox_reference(root, profile, "")
            self.assertEqual(
                voice.select_chatterbox_reference(root, profile, "take2"),
                (second, "take2"),
            )
            self.assertEqual(
                voice.select_chatterbox_reference(root, profile, "take3"),
                (third, "take3"),
            )
            second.write_bytes(b"altered")
            with self.assertRaisesRegex(SystemExit, "hash does not match"):
                voice.select_chatterbox_reference(root, profile, "take2")
            third.unlink()
            with self.assertRaisesRegex(SystemExit, "Reference audio not found"):
                voice.select_chatterbox_reference(root, profile, "take3")

    def test_unknown_voice_backend_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "Unsupported voice backend"):
            voice.profile_backend({"backend": {"name": "unknown"}})

    def test_english_reference_cannot_escape_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "profile"
            root.mkdir()
            outside = Path(folder) / "outside.wav"
            outside.write_bytes(b"outside")
            profile = {"references": {
                "outside": {"file": "../outside.wav", "sha256": voice.sha(outside)}
            }}
            with self.assertRaisesRegex(SystemExit, "inside its profile folder"):
                voice.select_chatterbox_reference(root, profile, "outside")

    def test_english_profile_dry_run_binds_selected_reference(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile = root / "profile"
            profile.mkdir()
            reference = profile / "take2.wav"
            reference.write_bytes(b"consented voice")
            (profile / "profile.json").write_text(json.dumps({
                "language": "en",
                "backend": {"name": "ChatterboxTurbo", "model_id": "test/model",
                            "revision": "test-revision", "defaults": {"seed_base": 4}},
                "consent": {"affirmed": True},
                "samples": [{"file": reference.name}],
                "references": {"take2": {"file": reference.name, "sha256": voice.sha(reference)}},
            }), encoding="utf-8")
            script = root / "script.json"
            script.write_text(json.dumps({"segments": [
                {"id": "en01", "start": 0, "end": 4, "text": "Hello there."}
            ]}), encoding="utf-8")
            args = SimpleNamespace(profile="en-raghu", script=str(script), only="",
                                   allow_mixed_script=False, reference=None,
                                   reference_text="", reference_variant="take2",
                                   dry_run=True, nfe_step=32, cfg_strength=2.0,
                                   speed=1.0)
            with patch.object(voice, "profile_dir", return_value=profile), \
                 patch("builtins.print") as output:
                voice.cmd_synthesize(root, args)
            plan = json.loads(output.call_args.args[0])
            self.assertEqual(plan["params"]["backend"], "chatterbox-turbo")
            self.assertEqual(plan["params"]["reference_variant"], "take2")
            self.assertEqual(plan["params"]["reference_sha256"], voice.sha(reference))
            self.assertFalse((root / ".content-studio" / "voice" / "narration").exists())
            args.speed = 1.2
            with patch.object(voice, "profile_dir", return_value=profile):
                with self.assertRaisesRegex(SystemExit, "IndicF5 synthesis options"):
                    voice.cmd_synthesize(root, args)

    def test_english_script_rejects_non_latin_letters(self):
        self.assertEqual(
            voice.non_latin_script_ids([
                {"id": "one", "text": "Hello there."},
                {"id": "two", "text": "ನಮಸ್ಕಾರ"},
            ]),
            ["two"],
        )

    def test_assembly_rejects_mixed_voice_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "script.json"
            script.write_text(json.dumps({"segments": [
                {"id": "a", "start": 0, "end": 2, "text": "First."},
                {"id": "b", "start": 3, "end": 5, "text": "Second."},
            ]}), encoding="utf-8")
            narration_root = root / ".content-studio" / "voice" / "narration"
            segments_dir = narration_root / "segments"
            segments_dir.mkdir(parents=True)
            for segment_id in ("a", "b"):
                (segments_dir / f"{segment_id}.wav").write_bytes(b"audio")
            (narration_root / "manifest.json").write_text(json.dumps({
                "params": {"reference_variant": "take3"},
                "segments": {
                    "a": {"text_hash": voice.narration.sha256_text("First."),
                          "params": {"reference_variant": "take2"}},
                    "b": {"text_hash": voice.narration.sha256_text("Second."),
                          "params": {"reference_variant": "take3"}},
                },
            }), encoding="utf-8")
            args = SimpleNamespace(script=str(script))
            with patch.object(voice.shutil, "which", return_value="tool"):
                with self.assertRaisesRegex(SystemExit, "different voice settings.*a"):
                    voice.cmd_assemble(root, args)

    def test_assembly_rejects_actual_silent_gap_before_mixing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = {"segments": [{"id": "a", "start": 0, "end": 2, "text": "short line"}]}
            script_path = root / "script.json"
            script_path.write_text(json.dumps(script), encoding="utf-8")
            narration_root = root / ".content-studio" / "voice" / "narration"
            segments_dir = narration_root / "segments"
            segments_dir.mkdir(parents=True)
            with wave.open(str(segments_dir / "a.wav"), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(24000)
                audio.writeframes(b"\0\0" * 24000)
            (narration_root / "manifest.json").write_text(json.dumps({"segments": {
                "a": {"text_hash": voice.narration.sha256_text("short line"), "seconds": 1.0}
            }}), encoding="utf-8")
            review_dir = root / "review"
            review_dir.mkdir()
            frames = []
            for role in ("before", "start", "middle", "end", "after"):
                path = Path("frames") / f"a-{role}.jpg"
                (review_dir / path).parent.mkdir(exist_ok=True)
                (review_dir / path).write_bytes(b"frame")
                frames.append({"role": role, "path": str(path), "at_seconds": 1})
            review_path = review_dir / "scene-review.json"
            review_path.write_text(json.dumps({
                "script_sha256": voice.scene_review.sha256(script_path),
                "cues": [{"id": "a", "start": 0, "end": 2,
                          "visual_start": 0, "visual_end": 2,
                          "visual_description": "Reviewed shot", "scene_match": "match",
                          "frames": frames}],
            }), encoding="utf-8")
            args = SimpleNamespace(script=str(script_path), scene_review=str(review_path),
                                   video=None, duration=10.0, preview=False, gap=0.3,
                                   max_narration_gap=5.0)
            with self.assertRaisesRegex(SystemExit, "Actual narration gap 9.000s"):
                voice.cmd_assemble(root, args)
            self.assertFalse((narration_root / "narration-24k.wav").exists())

    def test_assembly_rejects_real_wav_overrun_before_mixing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = {"segments": [{"id": "a", "start": 0, "end": 2, "text": "short line"}]}
            script_path = root / "script.json"
            script_path.write_text(json.dumps(script), encoding="utf-8")
            narration_root = root / ".content-studio" / "voice" / "narration"
            segments_dir = narration_root / "segments"
            segments_dir.mkdir(parents=True)
            with wave.open(str(segments_dir / "a.wav"), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(24000)
                audio.writeframes(b"\0\0" * (24000 * 3))
            (narration_root / "manifest.json").write_text(json.dumps({"segments": {
                "a": {"text_hash": voice.narration.sha256_text("short line"), "seconds": 1.0}
            }}), encoding="utf-8")
            review_dir = root / "review"
            review_dir.mkdir()
            frames = []
            for role in ("before", "start", "middle", "end", "after"):
                path = Path("frames") / f"a-{role}.jpg"
                (review_dir / path).parent.mkdir(exist_ok=True)
                (review_dir / path).write_bytes(b"frame")
                frames.append({"role": role, "path": str(path), "at_seconds": 1})
            review_path = review_dir / "scene-review.json"
            review_path.write_text(json.dumps({
                "script_sha256": voice.scene_review.sha256(script_path),
                "cues": [{"id": "a", "start": 0, "end": 2,
                          "visual_start": 0, "visual_end": 2,
                          "visual_description": "Reviewed shot", "scene_match": "match",
                          "frames": frames}],
            }), encoding="utf-8")
            args = SimpleNamespace(script=str(script_path), scene_review=str(review_path),
                                   video=None, duration=4.0, preview=False, gap=0.3,
                                   max_narration_gap=5.0)
            with self.assertRaisesRegex(ValueError, "after visual end.*shorten the script"):
                voice.cmd_assemble(root, args)
            self.assertFalse((narration_root / "narration-24k.wav").exists())

    def test_kannada_profile_rejects_unreviewed_mixed_script_before_model_load(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile = root / "profile"
            profile.mkdir()
            (profile / "sample.wav").write_bytes(b"sample")
            (profile / "profile.json").write_text(json.dumps({
                "language": "kn-en", "consent": {"affirmed": True},
                "samples": [{"file": "sample.wav"}],
            }), encoding="utf-8")
            script = root / "script.json"
            script.write_text(json.dumps({"segments": [
                {"id": "p01", "start": 0, "end": 10,
                 "text": "ಇವತ್ತು metro ಮೂಲಕ ಪಾಮ್ ಕಡೆ"},
            ]}), encoding="utf-8")
            args = SimpleNamespace(profile="rakshitha", script=str(script),
                                   only="", allow_mixed_script=False)
            with patch.object(voice, "profile_dir", return_value=profile):
                with self.assertRaisesRegex(SystemExit, "p01.*phonetically"):
                    voice.cmd_synthesize(root, args)
            self.assertFalse((root / ".content-studio" / "voice" / "narration").exists())

    def test_assembly_target_accepts_voice_only_duration(self):
        self.assertEqual(voice.assembly_target(None, 952.0, False), (None, 952.0))

    def test_assembly_target_requires_video_for_preview(self):
        with self.assertRaisesRegex(SystemExit, "--preview requires --video"):
            voice.assembly_target(None, 952.0, True)

    def test_assembly_target_rejects_invalid_duration(self):
        for seconds in (0, -1, float("nan"), float("inf")):
            with self.subTest(seconds=seconds), self.assertRaises(SystemExit):
                voice.assembly_target(None, seconds, False)

    def test_assembly_target_uses_existing_video_duration(self):
        with tempfile.TemporaryDirectory() as d:
            video_path = Path(d) / "picture.mp4"
            video_path.write_bytes(b"fixture")
            with patch.object(voice, "media_duration", return_value=14.5) as probe_duration:
                self.assertEqual(
                    voice.assembly_target(str(video_path), None, True),
                    (video_path.resolve(), 14.5),
                )
                probe_duration.assert_called_once_with(video_path.resolve())

    def test_sha256(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"sample.wav";f.write_bytes(b"abc")
            self.assertEqual(voice.sha(f),"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    def test_probe_rejects_invalid_audio(self):
        with patch.object(voice.subprocess,"run") as run:
            run.return_value.returncode=1
            run.return_value.stdout=""
            with self.assertRaises(ValueError):voice.probe("bad.wav")
    def test_probe_duration(self):
        with patch.object(voice.subprocess,"run") as run:
            run.return_value.returncode=0
            run.return_value.stdout=json.dumps({"streams":[{"sample_rate":"48000"}],"format":{"duration":"42.25"}})
            self.assertEqual(voice.probe("ok.wav"),42.25)
    def test_require_consent_accepts_affirmed_profile(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"sample-000.wav").write_bytes(b"x")
            (root/"profile.json").write_text(json.dumps({"consent":{"affirmed":True},"samples":[{"file":"sample-000.wav"}]}),encoding="utf-8")
            data=voice.require_consent(root)
            self.assertTrue(data["consent"]["affirmed"])
    def test_require_consent_rejects_unaffirmed_profile(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"profile.json").write_text(json.dumps({"consent":{"affirmed":False},"samples":[]}),encoding="utf-8")
            with self.assertRaises(SystemExit):voice.require_consent(root)
    def test_require_consent_rejects_missing_sample(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"profile.json").write_text(json.dumps({"consent":{"affirmed":True},"samples":[{"file":"gone.wav"}]}),encoding="utf-8")
            with self.assertRaises(SystemExit):voice.require_consent(root)
    def test_profile_dir_prefers_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            ws=Path(d)
            local=ws/".content-studio"/"voice"/"profiles"/"p"
            local.mkdir(parents=True)
            self.assertEqual(voice.profile_dir(ws,"p"),local)
    def test_profile_dir_falls_back_to_bundled(self):
        with tempfile.TemporaryDirectory() as d,tempfile.TemporaryDirectory() as b:
            bundled=Path(b);(bundled/"p").mkdir()
            with patch.object(voice,"BUNDLED_PROFILES",bundled):
                self.assertEqual(voice.profile_dir(Path(d),"p"),bundled/"p")
    def test_profile_dir_returns_workspace_when_absent(self):
        with tempfile.TemporaryDirectory() as d:
            ws=Path(d)
            with patch.object(voice,"BUNDLED_PROFILES",ws/"bundled"):
                self.assertEqual(voice.profile_dir(ws,"p"),voice.local_profile_dir(ws,"p"))

if __name__=="__main__":unittest.main()
