"""Unit tests for voice enrollment safety without requiring FFmpeg."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]/"scripts"/"voice.py"
spec=importlib.util.spec_from_file_location("voice_bootstrap",SOURCE)
voice=importlib.util.module_from_spec(spec);spec.loader.exec_module(voice)

class VoiceBootstrapTests(unittest.TestCase):
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

if __name__=="__main__":unittest.main()
