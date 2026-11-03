import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "master.py"
spec = importlib.util.spec_from_file_location("master", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MasterTests(unittest.TestCase):
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
