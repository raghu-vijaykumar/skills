"""Keep the scored README showcase and all 94 route claims in one audit."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


BLENDER = Path(__file__).resolve().parents[1]
SCRIPT = BLENDER / "scripts" / "audit_roadmap.py"


class RoadmapAuditTests(unittest.TestCase):
    def test_all_rows_and_winning_gifs_decode(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            subprocess.run([sys.executable, str(SCRIPT), "--output", str(output)],
                           check=True, capture_output=True, text=True)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["catalog_rows"], 94)
        self.assertEqual(report["scored_candidate_records"], 137)
        self.assertEqual(report["statuses"], {"Catalogued": 1, "Prototype": 3,
                                               "Rendered": 90, "Integrated": 0})
        self.assertEqual(report["distinct_style_gifs"], 31)
        self.assertEqual(report["distinct_visual_route_gifs"], 55)
        self.assertGreaterEqual(report["distinct_selected_gifs_decoded"], 55)
        self.assertTrue(all(row["gif_decode"]["frames"] > 1 for row in report["rows"]
                            if row["status"] == "Rendered"))


if __name__ == "__main__":
    unittest.main()
