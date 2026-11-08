import importlib.util
from contextlib import closing
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"memory.py"
spec=importlib.util.spec_from_file_location("content_studio_memory",SCRIPT)
memory=importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)

class MemoryTests(unittest.TestCase):
    def test_scope_override(self):
        with tempfile.TemporaryDirectory() as temp:
            with closing(memory.connect(Path(temp)/"memory.sqlite")) as db:
                for scope,value in [("global","medium"),("travel","low"),("project:dubai","off")]:
                    db.execute("INSERT INTO preferences(scope,key,value_json) VALUES(?,?,?)",(scope,"meme_intensity",'"'+value+'"'))
                db.commit()
                self.assertEqual(memory.retrieve(db,"travel","dubai")["preferences"]["meme_intensity"]["value"],"off")
                self.assertEqual(memory.retrieve(db,"travel","other")["preferences"]["meme_intensity"]["value"],"low")
                self.assertEqual(memory.retrieve(db,"cooking","")["preferences"]["meme_intensity"]["value"],"medium")

    def test_event_history(self):
        with tempfile.TemporaryDirectory() as temp:
            with closing(memory.connect(Path(temp)/"memory.sqlite")) as db:
                db.execute("INSERT INTO events(scope,feature,decision,actor) VALUES(?,?,?,?)",("travel","meme","rejected","human"))
                db.commit()
                self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0],1)

    def test_invalid_scope(self):
        with self.assertRaises(ValueError):memory.valid_scope("untrusted")

    def test_default_database_path_can_be_shared_across_chats(self):
        with tempfile.TemporaryDirectory() as temp:
            location = Path(temp) / "editing-memory.sqlite"
            with patch.dict(os.environ, {"CONTENT_STUDIO_MEMORY_DB": str(location)}):
                self.assertEqual(memory.default_db_path(), location)
                self.assertFalse(location.exists())

if __name__=="__main__":unittest.main()
