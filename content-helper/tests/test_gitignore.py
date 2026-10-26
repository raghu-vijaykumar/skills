import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import gitrepo


class GitIgnoreTest(unittest.TestCase):
    def test_scene_code_is_tracked_but_uploaded_media_is_ignored(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            root = Path(scratch)
            (root / ".gitignore").write_text(gitrepo.GITIGNORE, encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            for bucket in ("shorts", "long", "drafts"):
                folder = root / bucket / "example"
                folder.mkdir(parents=True)
                for name, ignored in (("video.tsx", False), ("video.mp4", True)):
                    file = folder / name
                    file.write_text("fixture", encoding="utf-8")
                    result = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", str(file)])
                    self.assertEqual(result.returncode == 0, ignored, str(file))


if __name__ == "__main__":
    unittest.main()
