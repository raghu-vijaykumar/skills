import importlib.util
from contextlib import closing
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(SCRIPTS))
def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+".py"))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

workflow=load("learn_from_edit")
confirm=load("confirm_diff")
memory=load("memory")

class EndToEndTests(unittest.TestCase):
    def test_review_then_confirm_once(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            proposed=root/"timeline.json"
            proposed.write_text(json.dumps({"schema":"content-studio.timeline.v1","revision":1,
                "tracks":[{"kind":"video","clips":[{"id":"v0000","source":"shot.mp4",
                "source_in":0,"source_out":5,"start":0}]}]}))
            project=root/"edited.kdenlive"
            project.write_text('<mlt root="/videos"><profile frame_rate_num="30" frame_rate_den="1"/>'
                '<chain id="c1"><property name="resource">shot.mp4</property></chain>'
                '<playlist id="p1"><entry producer="c1" in="00:00:01.000" out="00:00:02.967"/></playlist></mlt>')
            result=workflow.build(proposed,project,root/"review")
            self.assertEqual(result["observations"],1)
            self.assertTrue((root/"review"/"review.html").is_file())
            with closing(memory.connect(root/"memory.sqlite")) as db:
                report=json.loads((root/"review"/"comparison.json").read_text())
                first=confirm.record(db,report,"travel","trip1","too repetitive")
                second=confirm.record(db,report,"travel","trip1","too repetitive")
                self.assertEqual(first["recorded"],1)
                self.assertTrue(second["duplicate"])
                self.assertEqual(db.execute("SELECT count(*) FROM events").fetchone()[0],1)

if __name__=="__main__":unittest.main()
