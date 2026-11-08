"""Unit tests for the IndicF5 backend without importing Torch."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import indicf5_backend


class ModelDirTest(unittest.TestCase):
    def test_default_is_quality_mode(self):
        self.assertEqual(indicf5_backend.DEFAULT_NFE_STEP, 32)
        self.assertEqual(indicf5_backend.DEFAULT_CFG_STRENGTH, 2.0)

    def test_returns_weights_and_vocab(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "checkpoints").mkdir()
            (root / "model.safetensors").write_bytes(b"weights")
            (root / "checkpoints" / "vocab.txt").write_text("vocab", encoding="utf-8")
            weights, vocab = indicf5_backend.validate_model_dir(root)
            self.assertTrue(weights.is_file())
            self.assertTrue(vocab.is_file())

    def test_rejects_missing_weights(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "checkpoints").mkdir()
            (root / "checkpoints" / "vocab.txt").write_text("vocab", encoding="utf-8")
            with self.assertRaises(SystemExit):
                indicf5_backend.validate_model_dir(root)

    def test_rejects_missing_vocab(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "model.safetensors").write_bytes(b"weights")
            with self.assertRaises(SystemExit):
                indicf5_backend.validate_model_dir(root)


if __name__ == "__main__":
    unittest.main()
