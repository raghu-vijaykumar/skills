import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sfx = load("sfx")
events = load("events")


def wav(path):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(b"\0\0\0\0" * 4800)


class ShippedBankTests(unittest.TestCase):
    def test_complete_bank_is_playable_hashed_and_pending_review(self):
        assets = sfx.library.STOCK_ASSETS
        items = [item for item in sfx.library.read_catalogue(assets)
                 if item.get("origin", {}).get("source") == "earshot" and
                 item["origin"].get("bank_version")]
        self.assertEqual(len(items), 252)
        self.assertTrue((assets / "earshot-gallery.html").is_file())
        for item in items:
            source = assets / item["relative_path"]
            self.assertTrue(source.is_file(), item["name"])
            self.assertEqual(sfx._sha(source), item["sha256"])
            with wave.open(str(source), "rb") as audio:
                self.assertEqual(audio.getframerate(), 48000)
                self.assertEqual(audio.getsampwidth(), 3)
                self.assertGreater(audio.getnframes(), 0)
                self.assertEqual(audio.getnchannels(), item["media"]["channels"])
            self.assertTrue(item["origin"]["recipe_id"])
            self.assertEqual(len(item["origin"]["recipe_sha256"]), 64)
            self.assertEqual(item["reuse_status"], "reference-only")
            self.assertEqual(item["effect_review"], "pending")
        self.assertEqual({item["origin"]["commit"] for item in items}, {sfx.PINNED_COMMIT})


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.assets = self.root / "library"
        sound = self.assets / "media" / "sfx" / "earshot" / "click" / "soft.wav"
        sound.parent.mkdir(parents=True)
        wav(sound)
        self.item = {"id": "sfx-click", "name": "click/soft", "kind": "sfx",
                     "rights": "licensed", "creator": "Leon Lin", "tags": ["earshot"],
                     "sha256": sfx._sha(sound),
                     "relative_path": sound.relative_to(self.assets).as_posix(),
                     "media": {"duration_seconds": .1, "sample_rate": 48000,
                               "channels": 2, "codec": "pcm_s16le"},
                     "reuse_status": "reference-only", "effect_review": "pending",
                     "sfx_profile": {"label": "Soft click", "shot_tags": [],
                                     "identification_review": "pending"},
                     "origin": {"source": "earshot", "sound_id": "click/soft",
                                "audit": {"status": "passed"},
                                "cue_roles": ["click"],
                                "sync": {"onset_s": .01, "peak_s": .02}}}
        sfx.library.write_catalogue(self.assets, [self.item])
        self.manifest = {"schema_version": 1, "route": "remotion",
                         "source": str(self.root / "scene-plan.json"),
                         "source_sha256": "a" * 64, "duration_seconds": 3,
                         "events": [
                             {"id": "button", "time": 1, "event_type": "click",
                              "confidence": .9, "audio_context": "quiet",
                              "evidence": {"frame": 30}},
                             {"id": "speech", "time": 1.5, "event_type": "click",
                              "confidence": .9, "audio_context": "dialogue",
                              "evidence": {"frame": 45}},
                             {"id": "guess", "time": 2, "event_type": "click",
                              "confidence": .4, "audio_context": "quiet",
                              "evidence": {"frame": 60}},
                         ]}

    def tearDown(self):
        self.temp.cleanup()

    def test_preview_is_pending_and_delivery_requires_listening(self):
        preview = events.propose(self.manifest, self.assets)
        self.assertEqual(preview["cues"][0]["decision"], "candidate")
        self.assertAlmostEqual(preview["cues"][0]["start"], .99)
        self.assertTrue(preview["cues"][0]["sound_review_required"])
        self.assertEqual([row["decision"] for row in preview["cues"][1:]],
                         ["no-effect", "no-effect"])
        self.assertEqual(events.propose(self.manifest, self.assets, mode="delivery")
                         ["cues"][0]["decision"], "no-effect")
        self.item["effect_review"] = "passed"
        self.item["reuse_status"] = "reusable"
        self.item["sfx_profile"]["identification_review"] = "passed"
        sfx.library.write_catalogue(self.assets, [self.item])
        delivery = events.propose(self.manifest, self.assets, mode="delivery")
        self.assertFalse(delivery["cues"][0]["sound_review_required"])
        project = self.root / "project"
        project.mkdir()
        (project / "scene-plan.json").write_text('{"fps":30,"durationFrames":90}')
        delivery["source_sha256"] = sfx._sha(project / "scene-plan.json")
        (project / "entry.tsx").write_text("import {Video} from './video';\n"
                                           "const Root = () => <Composition component={Video}/>;")
        created = events.export_remotion(delivery, project, self.assets,
                                         project / "content" / "sfx-cues.json",
                                         self.root / "public")
        self.assertEqual(created["sfx_clips"], 1)
        self.assertIn("component={SfxVideo}", (project / "entry.tsx").read_text())
        self.assertTrue((self.root / "public" / "sfx" /
                         (self.item["sha256"] + ".wav")).is_file())

    def test_audit_failure_never_becomes_candidate(self):
        self.item["origin"]["audit"]["status"] = "failed"
        sfx.library.write_catalogue(self.assets, [self.item])
        self.assertEqual(events.propose(self.manifest, self.assets)
                         ["cues"][0]["decision"], "no-effect")

    def test_music_requires_bed_measurement_and_collision_is_skipped(self):
        self.manifest["events"] = [
            {"id": "one", "time": 1, "event_type": "click", "confidence": .9,
             "audio_context": "music", "evidence": {"frame": 30}},
            {"id": "two", "time": 1.05, "event_type": "click", "confidence": .9,
             "audio_context": "music", "evidence": {"frame": 31}},
        ]
        self.assertEqual(events.propose(self.manifest, self.assets)["cues"][0]["decision"],
                         "no-effect")
        bed = self.root / "music.wav"
        wav(bed)
        proposed = events.propose(self.manifest, self.assets, music_bed=bed)
        self.assertEqual(proposed["music_bed_sha256"], sfx._sha(bed))
        self.assertEqual(proposed["cues"][0]["decision"], "candidate")
        self.assertEqual(proposed["cues"][0]["level_evidence"]["method"],
                         "pre_cue_50ms_window_measurement")
        self.assertEqual(proposed["cues"][1]["reason"], "effect collision")

    def test_authored_scene_events_keep_frame_evidence(self):
        plan = self.root / "scene-plan.json"
        plan.write_text(json.dumps({"fps": 30, "durationFrames": 90,
                                    "scenes": [{"id": "intro", "startFrame": 0,
                                                "endFrame": 90,
                                                "narrationCueIds": ["line1"],
                                                "stateChanges": [{"frame": 30,
                                                                  "label": "Click the button"}]}]}))
        analyzed = events.analyze_remotion(plan)
        self.assertEqual(analyzed["events"][0]["event_type"], "click")
        self.assertEqual(analyzed["events"][0]["audio_context"], "narration")
        self.assertEqual(analyzed["events"][0]["evidence"]["frame"], 30)

    def test_timeline_export_is_pending_and_bound_to_edited_picture(self):
        video = self.root / "edit.mp4"
        video.write_bytes(b"edited picture fixture")
        preflight = self.root / "preflight"
        preflight.mkdir()
        plan = preflight / "plan.json"
        plan.write_text(json.dumps({"schema_version": 1, "kind": "edited",
                                    "stage": "edited-render", "steps": [{"id": "S01"}]}))
        scripts = SKILL.parents[1] / "timeline" / "scripts"
        import sys
        sys.path.insert(0, str(scripts))
        import model
        digest = model.sha256_file(plan)
        (preflight / "approval.json").write_text(json.dumps({
            "plan_sha256": digest, "review_note": "Reviewed fixture", "actor": "human"}))
        (preflight / "checklist.json").write_text(json.dumps({
            "plan_sha256": digest, "items": [{"id": "S01"}]}))
        timeline = model.make_initial(plan, video, self.root / "final.mp4",
                                      fps=30, width=160, height=90)
        timeline["picture"][0]["source_out"] = 3
        timeline_path = self.root / "timeline-v001.json"
        model.write_new(timeline_path, timeline)
        self.manifest["route"] = "edited"
        self.manifest["source"] = str(video)
        self.manifest["source_sha256"] = model.sha256_file(video)
        proposal = events.propose(self.manifest, self.assets)
        changes_path = self.root / "changes.json"
        result = events.export_timeline(proposal, timeline_path, self.assets,
                                        changes_path)
        self.assertEqual(result["sfx_cues"], 1)
        changes = json.loads(changes_path.read_text())
        self.assertTrue(changes["audio"][0]["sound_review_required"])
        pending = model.revise(timeline, changes, new_output=str(self.root / "next.mp4"))
        model.validate(pending, require_review=False)
        changes["audio"][0]["review_status"] = "approved"
        pending = model.revise(timeline, changes, new_output=str(self.root / "next.mp4"))
        with self.assertRaisesRegex(ValueError, "listening review"):
            model.validate(pending)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class EditedEvidenceTests(unittest.TestCase):
    def test_detects_cut_with_frames_but_does_not_claim_semantics(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            video = root / "edit.mp4"
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                       "-f", "lavfi", "-i", "color=c=red:s=160x90:r=10:d=1",
                       "-f", "lavfi", "-i", "color=c=blue:s=160x90:r=10:d=1",
                       "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0",
                       "-c:v", "libx264", str(video)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr[-400:])
            analyzed = events.analyze_edited(video, root / "frames", .2)
            self.assertTrue(analyzed["requires_visual_review"])
            self.assertTrue(analyzed["events"])
            self.assertLess(analyzed["events"][0]["confidence"], .7)
            self.assertTrue(all(Path(frame).is_file() for frame in
                                analyzed["events"][0]["evidence"]["frames"]))


if __name__ == "__main__":
    unittest.main()
