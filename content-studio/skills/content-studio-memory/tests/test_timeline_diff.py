import importlib.util
import unittest
from pathlib import Path

path=Path(__file__).resolve().parents[1]/"scripts"/"timeline_diff.py"
spec=importlib.util.spec_from_file_location("timeline_diff",path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def timeline(clips,revision):
    return {"schema":"content-studio.timeline.v1","revision":revision,
            "tracks":[{"kind":"video","clips":clips}]}
def clip(ident,source="a.mp4",start=0,begin=0,end=5,gain=0):
    return {"id":ident,"source":source,"start":start,"source_in":begin,
            "source_out":end,"audio_gain_db":gain}

class TimelineDiffTests(unittest.TestCase):
    def test_trim_and_gain(self):
        result=module.compare(timeline([clip("a")],1),
                              timeline([clip("a",begin=1,end=4,gain=-3)],2))
        self.assertEqual([x["type"] for x in result["changes"]],["trimmed","gain_changed"])
    def test_reorder_not_remove(self):
        old=timeline([clip("a"),clip("b",start=5)],1)
        new=timeline([clip("b"),clip("a",start=5)],2)
        self.assertEqual([x["type"] for x in module.compare(old,new)["changes"]],["reordered"])
    def test_remove(self):
        result=module.compare(timeline([clip("a"),clip("b")],1),
                              timeline([clip("a")],2))
        self.assertEqual(result["changes"][0]["type"],"removed")
    def test_invalid_schema(self):
        with self.assertRaises(ValueError):
            module.compare({},timeline([clip("a")],1))

if __name__=="__main__":unittest.main()
