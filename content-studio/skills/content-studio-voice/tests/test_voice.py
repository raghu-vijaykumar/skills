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

if __name__=="__main__":unittest.main()
