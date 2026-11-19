"""Checkpoint validation without importing the optional Chatterbox runtime."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import chatterbox_backend


class ChatterboxBackendTests(unittest.TestCase):
    def test_requires_complete_local_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaisesRegex(SystemExit, "model directory is incomplete"):
                chatterbox_backend.validate_model_dir(root)
            for name in chatterbox_backend.REQUIRED_MODEL_FILES:
                (root / name).write_bytes(b"fixture")
            self.assertEqual(chatterbox_backend.validate_model_dir(root), root)


if __name__ == "__main__":
    unittest.main()
