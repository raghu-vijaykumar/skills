import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import match


class MatchTest(unittest.TestCase):
    def make_video(self, path, color):
        subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", f"color=c={color}:s=320x180:r=30:d=1",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(path)], check=True, capture_output=True)

    def test_folder_matching_writes_outputs_and_manifest(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            folder = root / "clips"
            folder.mkdir()
            self.make_video(folder / "a.mp4", "red")
            self.make_video(folder / "b.mp4", "blue")
            output = root / "matched"
            manifest = match.match_folder(match.build_parser().parse_args([
                "--folder", str(folder), "--output-dir", str(output)]))
            self.assertEqual(len(manifest["results"]), 2)
            self.assertTrue((output / "a-matched.mp4").is_file())
            self.assertTrue((output / "b-matched.mp4").is_file())
            self.assertTrue((output / "color-match.json").is_file())


if __name__ == "__main__":
    unittest.main()
