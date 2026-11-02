import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import content


class DraftCreationTest(unittest.TestCase):
    def test_safe_folder_id_keeps_human_title(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as scratch:
            workspace = Path(scratch)
            cfg = {"workspace": str(workspace), "channels": {"revise-labs": {
                "channelId": "UCtest", "name": "Revise Labs"}}}
            args = SimpleNamespace(channel="revise-labs", action="new", name="Working Title",
                                   id="00077-working-title", force=False)
            self.assertEqual(content.draft(cfg, args, lambda message: None), 0)
            folder = workspace / "revise-labs" / "drafts" / "00077-working-title"
            self.assertEqual((folder / "title.txt").read_text(encoding="utf-8").strip(),
                             "Working Title")
            self.assertEqual(json.loads((folder / "draft.json").read_text(encoding="utf-8"))["sourceId"],
                             "00077-working-title")
            args.id = "../escape"
            with self.assertRaisesRegex(SystemExit, "--id"):
                content.draft(cfg, args, lambda message: None)


if __name__ == "__main__":
    unittest.main()
