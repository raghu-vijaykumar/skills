import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "master.py"
spec = importlib.util.spec_from_file_location("master", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MasterTests(unittest.TestCase):
    def test_cleanup_adds_deesser_and_gate_in_order(self):
        chain = module.build_filter(cleanup=True)
        self.assertIn("highpass=f=80", chain)
        self.assertIn("afftdn", chain)
        self.assertIn("deesser", chain)
        self.assertIn("agate", chain)
        self.assertLess(chain.index("deesser"), chain.index("agate"))

    def test_arnndn_replaces_afftdn(self):
        chain = module.build_filter(arnndn_model="model.rnnn")
        self.assertIn("arnndn", chain)
        self.assertNotIn("afftdn", chain)

    def test_measure_filter_handles_empty_and_nonempty_chains(self):
        self.assertEqual(
            module.measure_filter(""),
            "loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json",
        )
        self.assertEqual(
            module.measure_filter("highpass=f=80,afftdn=nf=-28"),
            "highpass=f=80,afftdn=nf=-28,"
            "loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json",
        )


if __name__ == "__main__":
    unittest.main()
