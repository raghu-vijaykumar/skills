import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"timeline.py"
spec=importlib.util.spec_from_file_location("timeline",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        (self.root/"clip.mp4").write_bytes(b"fixture")
        self.timeline=mod.initial_timeline([
            {"source":"clip.mp4","start":0,"end":4},
            {"source":"clip.mp4","start":4,"end":8}],self.root)

    def tearDown(self): self.temp.cleanup()

    def test_valid_initial_timeline(self):
        self.assertEqual(len(mod.validate(self.timeline,self.root)),2)

    def test_initial_timeline_records_size_and_fit(self):
        timeline=mod.initial_timeline([{"source":"clip.mp4","start":0,"end":4}],
                                      self.root,width=1080,height=1920,fit="blur")
        self.assertEqual((timeline["width"],timeline["height"]), (1080,1920))
        self.assertEqual(timeline["fit"],"blur")

    def test_blur_fit_filter_uses_background_and_foreground(self):
        graph=";".join(mod.fit_filter("[0:v:0]",1920,1080,"blur","[v]"))
        self.assertIn("split=2",graph)
        self.assertIn("gblur",graph)
        self.assertIn("overlay",graph)
        self.assertIn("[v]",graph)

    def test_blur_fit_filter_supports_portrait_target(self):
        graph=";".join(mod.fit_filter("[0:v:0]",1080,1920,"blur","[v]"))
        self.assertIn("scale=1080:1920",graph)
        self.assertIn("gblur",graph)
        self.assertIn("overlay=(W-w)/2:(H-h)/2",graph)

    def test_enhancement_filters_are_clip_relative(self):
        clip={"source_in":10.0,"duration":5.0,"enhancements":[
            {"source_start":12.0,"source_end":14.0,
             "filters":["eq=brightness=0.05"]}]}
        self.assertEqual(mod.enhancement_filters(clip),
                         ["eq=brightness=0.05:enable='between(t,2.000,4.000)'"])

    def test_edit_timeline_writes_ordered_contributions(self):
        timeline=mod.initial_timeline([
            {"source":"clip.mp4","start":0,"end":2},
            {"source":"clip.mp4","start":4,"end":6}],self.root)
        path=mod.write_edit_timeline(timeline,self.root)
        self.assertEqual(path,self.root/"edit-timeline.json")
        document=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(document["schema"],"content-studio.edit-timeline.v1")
        self.assertEqual([c["order"] for c in document["clips"]],[1,2])
        self.assertEqual(document["clips"][0]["timeline_start"],0)
        self.assertEqual(document["clips"][1]["timeline_start"],2)
        self.assertEqual(document["clips"][1]["source_in"],4)
        self.assertIn("Edit timeline",(self.root/"edit-timeline.html").read_text(encoding="utf-8"))

    def test_reframe_fit_crops_and_scales_and_survives_timeline_copy(self):
        record={"source_width":640,"source_height":360,
                "crop":{"x":0.676167,"y":0,"w":0.316406,"h":1.0}}
        graph=";".join(mod.fit_filter("[0:v:0]",1080,1920,"reframe","[v]",record))
        self.assertIn("crop=202:360:433:0",graph)
        self.assertIn("scale=1080:1920",graph)
        timeline=mod.initial_timeline([
            {"source":"clip.mp4","start":0,"end":4,"reframe":record}],
            self.root,width=1080,height=1920,fit="reframe")
        self.assertEqual(timeline["tracks"][0]["clips"][0]["reframe"],record)

    def test_trim_recomputes_positions(self):
        t=mod.revise(self.timeline,[{"action":"trim","id":"v0000","source_out":2}])
        clips=mod.validate(t,self.root)
        self.assertEqual(clips[1]["start"],2)
        self.assertEqual(t["revision"],2)

    def test_move_and_remove(self):
        t=mod.revise(self.timeline,[{"action":"move","id":"v0001","index":0},
                                     {"action":"remove","id":"v0000"}])
        self.assertEqual(mod.validate(t,self.root)[0]["id"],"v0001")

    def test_reject_source_escape(self):
        self.timeline["tracks"][0]["clips"][0]["source"]="../outside.mp4"
        with self.assertRaises(ValueError): mod.validate(self.timeline,self.root)

    def test_revision_snapshots_are_immutable(self):
        mod.write_revision(self.timeline,self.root)
        with self.assertRaises(FileExistsError): mod.write_revision(self.timeline,self.root)
        t=mod.revise(self.timeline,[{"action":"gain","id":"v0000","db":-5}])
        mod.write_revision(t,self.root)
        old=json.loads((self.root/"timeline-history/timeline-v001.json").read_text())
        self.assertEqual(old["tracks"][0]["clips"][0]["audio_gain_db"],0)

if __name__=="__main__": unittest.main()
