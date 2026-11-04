import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"memory.py"
spec=importlib.util.spec_from_file_location("content_studio_memory",SCRIPT)
memory=importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)

class MemoryTests(unittest.TestCase):
    def test_scope_override(self):
        with tempfile.TemporaryDirectory() as temp:
            db=memory.connect(Path(temp)/"memory.sqlite")
            for scope,value in [("global","medium"),("travel","low"),("project:dubai","off")]:
                db.execute("INSERT INTO preferences(scope,key,value_json) VALUES(?,?,?)",(scope,"meme_intensity",'"'+value+'"'))
            db.commit()
            self.assertEqual(memory.retrieve(db,"travel","dubai")["preferences"]["meme_intensity"]["value"],"off")
            self.assertEqual(memory.retrieve(db,"travel","other")["preferences"]["meme_intensity"]["value"],"low")
            self.assertEqual(memory.retrieve(db,"cooking","")["preferences"]["meme_intensity"]["value"],"medium")

    def test_event_history(self):
        with tempfile.TemporaryDirectory() as temp:
            db=memory.connect(Path(temp)/"memory.sqlite")
            db.execute("INSERT INTO events(scope,feature,decision,actor) VALUES(?,?,?,?)",("travel","meme","rejected","human"))
            db.commit()
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0],1)

    def test_invalid_scope(self):
        with self.assertRaises(ValueError):memory.valid_scope("untrusted")

if __name__=="__main__":unittest.main()
