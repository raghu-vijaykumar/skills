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
        self.assertEqual(module.seconds("2m30s"),150)
        self.assertEqual(module.seconds("1h2m3s"),3723)
        self.assertEqual(module.seconds("150"),150)
        with self.assertRaises(ValueError):
            module.seconds("soon")

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

    def test_orientation_filtering_and_size_parsing(self):
        sources={"land.mp4":10,"port.mp4":20,"square.mp4":30}
        dimensions={"land.mp4":(1920,1080),"port.mp4":(1080,1920),"square.mp4":(1080,1080)}
        kept,skipped=module.filter_source_map(sources,dimensions,"landscape")
        self.assertEqual(kept,{"land.mp4":10})
        self.assertEqual({item["source"] for item in skipped},{"port.mp4","square.mp4"})
        kept,_=module.filter_source_map(sources,dimensions,"landscape",include_mismatched=True)
        self.assertEqual(len(kept),3)
        kept,_=module.filter_source_map(sources,dimensions,"landscape",allow=["port.mp4"])
        self.assertEqual(set(kept),{"land.mp4","port.mp4"})
        self.assertEqual(module.parse_size("1080x1920"),(1080,1920))
        self.assertEqual(module.orientation(1080,1920),"portrait")
        with self.assertRaises(ValueError):
            module.parse_size("1080x1919")

    def test_empty_annotations(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"empty.json"
            path.write_text('{"segments":[]}')
            self.assertEqual(module.read_segments(path,{"clip.mp4":10},True),[])

if __name__=="__main__": unittest.main()
