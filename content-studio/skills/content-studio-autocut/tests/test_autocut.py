"""Fast tests for AutoCut's selection and input handling. Run: python -m unittest discover -s content-studio/skills/content-studio-autocut/tests"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"autocut.py"
spec=importlib.util.spec_from_file_location("autocut",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class AutoCutTests(unittest.TestCase):
    def test_duration_parsing(self):
        self.assertEqual(module.seconds("12m"),720)
        self.assertEqual(module.seconds("45s"),45)
        self.assertEqual(module.seconds("2.5"),2.5)

    def test_annotation_bounds_and_source_safety(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"annotations.json"
            path.write_text(json.dumps({"segments":[
                {"source":"../clip.mp4","start":1,"end":3,"score":0.8},
                {"source":"clip.mp4","start":5,"end":30},
                {"source":"missing.mp4","start":1,"end":2}]}))
            items=module.read_segments(path,{"clip.mp4":10},True)
            self.assertEqual(len(items),1)
            self.assertEqual(items[0]["source"],"clip.mp4")

    def test_empty_annotations(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"empty.json"
            path.write_text('{"segments":[]}')
            self.assertEqual(module.read_segments(path,{"clip.mp4":10},True),[])

if __name__=="__main__": unittest.main()
