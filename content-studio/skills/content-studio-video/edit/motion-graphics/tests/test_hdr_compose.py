import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "hdr_compose", Path(__file__).parents[1] / "scripts" / "hdr_compose.py")
compose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compose)


class HLGComposeTest(unittest.TestCase):
    def test_rejects_unlisted_manifest_operation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "manifest.json"
            path.write_text(json.dumps({"schema_version": 1, "revision": 1,
                                        "operations": ["unknown"]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsupported manifest"):
                compose.load(path)

    def test_one_encode_graph_contains_intro_overlay_and_audio_concat(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            data = {key: {"path": str(p / key)} for key in ("intro", "source", "stock", "sidecar")}
            data["stock_start"] = 482.0
            command, cwd = compose.final_command(data, p / "final.mp4")
            graph = command[command.index("-filter_complex") + 1]
            self.assertEqual(cwd, p)
            self.assertIn("transfer=arib-std-b67", graph)
            self.assertIn("ass=sidecar", graph)
            self.assertIn("PTS-STARTPTS+482.0/TB", graph)
            self.assertIn("concat=n=2:v=1:a=0", graph)
            self.assertIn("concat=n=2:v=0:a=1", graph)
            self.assertIn("hevc_nvenc", command)
            self.assertIn("arib-std-b67", command)


if __name__ == "__main__":
    unittest.main()
