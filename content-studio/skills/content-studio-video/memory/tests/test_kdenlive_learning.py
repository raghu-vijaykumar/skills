import importlib.util
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]/"scripts"
def load(name):
    spec=importlib.util.spec_from_file_location(name,BASE/(name+".py"))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
mlt=load("kdenlive_import");compare=load("compare_kdenlive");learn=load("learn")

class ImportTests(unittest.TestCase):
    def test_import_and_compare(self):
        xml='''<mlt root="/videos"><profile frame_rate_num="30" frame_rate_den="1"/>
        <chain id="c1"><property name="resource">shot.mp4</property></chain>
        <playlist id="playlist0"><entry producer="c1" in="00:00:01.000" out="00:00:02.967"/></playlist></mlt>'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"edit.kdenlive";path.write_text(xml)
            result=mlt.import_mlt(path)
            self.assertEqual(len(result["tracks"][0]["clips"]),1)
            proposal={"schema":"content-studio.timeline.v1","tracks":[{"kind":"video","clips":[
                {"source":"shot.mp4","source_in":0,"source_out":5}]}]}
            report=compare.compare(proposal,result)
            self.assertEqual(report["observations"][0]["type"],"source_range_reduced")
    def test_no_auto_learning(self):
        with tempfile.TemporaryDirectory() as tmp:
            with closing(sqlite3.connect(Path(tmp)/"test.sqlite")) as db:
                db.execute("CREATE TABLE events(id INTEGER PRIMARY KEY,project TEXT,scope TEXT,feature TEXT,decision TEXT,reason TEXT,actor TEXT,context_json TEXT)")
                for i in range(3):
                    db.execute("INSERT INTO events(project,scope,feature,decision,reason,actor,context_json) VALUES(?,?,?,?,?,?,?)",
                               (f"p{i}","travel","meme","rejected","interrupts dialogue","human","{}"))
                db.commit()
                items=learn.candidates(db)
                self.assertEqual(items[0]["status"],"candidate_requires_confirmation")
                self.assertEqual(items[0]["support_count"],3)

if __name__=="__main__":unittest.main()
