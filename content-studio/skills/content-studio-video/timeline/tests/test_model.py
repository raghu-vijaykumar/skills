import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import approval  # noqa: E402
import model  # noqa: E402
import timeline as cli  # noqa: E402


class TimelineModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        plan_dir = self.root / "preflight"
        plan_dir.mkdir()
        self.plan = plan_dir / "plan.json"
        self.plan.write_text(json.dumps({
            "schema_version": 1, "kind": "edited", "stage": "edited-render",
            "steps": [{"id": "S01"}],
        }))
        digest = model.sha256_file(self.plan)
        (plan_dir / "approval.json").write_text(json.dumps({
            "plan_sha256": digest, "review_note": "human review"}))
        (plan_dir / "checklist.json").write_text(json.dumps({
            "plan_sha256": digest, "items": [{"id": "S01"}]}))
        self.source = self.root / "source.mp4"
        self.source.write_bytes(b"source fixture")
        self.voice = self.root / "voice.wav"
        self.voice.write_bytes(b"voice fixture")
        self.path = self.root / "timeline-v001.json"
        self.timeline = model.make_initial(
            self.plan, self.source, self.root / "final-v001.mp4",
            fps=30, width=1920, height=1080)
        self.timeline["picture"][0]["source_out"] = 4.0
        model.write_new(self.path, self.timeline)

    def tearDown(self):
        self.temp.cleanup()

    def test_approved_plan_and_source_are_required(self):
        self.assertEqual(model.validate(self.timeline)["duration"], 4)
        self.plan.write_text('{"steps":[{"id":"S02"}]}')
        with self.assertRaisesRegex(ValueError, "plan changed"):
            model.validate(self.timeline)

    def test_plan_checklist_must_match(self):
        checklist = self.plan.with_name("checklist.json")
        checklist.write_text(json.dumps({
            "plan_sha256": model.sha256_file(self.plan), "items": []}))
        with self.assertRaisesRegex(ValueError, "checklist is stale"):
            model.validate(self.timeline)

    def test_source_prep_plan_cannot_authorize_final_render(self):
        plan = json.loads(self.plan.read_text())
        plan["stage"] = "source-prep"
        self.plan.write_text(json.dumps(plan))
        digest = model.sha256_file(self.plan)
        self.timeline["plan_sha256"] = digest
        self.plan.with_name("approval.json").write_text(json.dumps({
            "plan_sha256": digest, "review_note": "approved"}))
        self.plan.with_name("checklist.json").write_text(json.dumps({
            "plan_sha256": digest, "items": [{"id": "S01"}]}))
        with self.assertRaisesRegex(ValueError, "edited-render"):
            model.validate(self.timeline)

    def test_revision_needs_new_timeline_approval(self):
        old_fingerprint = approval.fingerprint(self.path, self.timeline)
        changed = model.revise(self.timeline, {"operations": [{
            "id": "color1", "method": "color-eq", "start": 1.0, "end": 2.0,
            "brightness": 0.02, "review_status": "approved"}]},
            new_output=str(self.root / "final-v002.mp4"))
        next_path = self.root / "timeline-v002.json"
        model.write_new(next_path, changed)
        self.assertEqual(changed["revision"], 2)
        self.assertTrue(changed["parent_sha256"])
        self.assertNotEqual(old_fingerprint, approval.fingerprint(next_path, changed))
        record = self.root / "approval.json"
        record.write_text(json.dumps({
            "actor": "human", "reviewer": "editor", "review_note": "old",
            "approved_at": "2026-11-08T12:00:00+05:30",
            "fingerprint": old_fingerprint}))
        with self.assertRaisesRegex(ValueError, "stale"):
            approval.require_human_approval(next_path, changed, record)
        self.assertEqual(model.load(self.path)["revision"], 1)

    def test_renderer_capability_change_invalidates_approval(self):
        original = approval.fingerprint(self.path, self.timeline)
        with patch.object(approval, "capability_sha256", return_value="0" * 64):
            changed = approval.fingerprint(self.path, self.timeline)
        self.assertNotEqual(original, changed)

    def test_changed_plan_review_bytes_invalidate_approval(self):
        original = approval.fingerprint(self.path, self.timeline)
        approval_path = self.plan.with_name("approval.json")
        changed = json.loads(approval_path.read_text())
        changed["review_note"] = "revised human note"
        approval_path.write_text(json.dumps(changed))
        self.assertNotEqual(original, approval.fingerprint(self.path, self.timeline))

    def test_replaced_voice_invalidates_fingerprint(self):
        self.timeline["audio"] = [{
            "id": "voice", "kind": "voice", "source": "voice.wav",
            "sha256": model.sha256_file(self.voice), "start": 0.5,
            "gain": 1.0, "review_status": "approved"}]
        model.validate(self.timeline)
        self.voice.write_bytes(b"changed voice")
        with self.assertRaisesRegex(ValueError, "Audio asset changed"):
            model.validate(self.timeline)

    def test_unreviewed_transition_is_refused(self):
        self.timeline["picture"].append({
            "id": "p2", "source": "source.mp4",
            "sha256": model.sha256_file(self.source),
            "source_in": 1, "source_out": 2})
        self.timeline["transitions"] = [{
            "after": "p0001", "id": "cross-fade", "duration": 0.2}]
        with self.assertRaisesRegex(ValueError, "lacks human review"):
            model.validate(self.timeline)

    def test_custom_join_requires_two_clips_and_bounded_overlap(self):
        self.timeline["picture"].append({
            "id": "p0002", "source": self.source.name,
            "sha256": model.sha256_file(self.source),
            "source_in": 0, "source_out": 1.0,
        })
        cue = {"after": "p0001", "id": "heart", "duration": 0.5,
               "review_status": "approved"}
        self.timeline["transitions"] = [cue]
        self.assertAlmostEqual(model.validate(self.timeline)["duration"], 4.5)
        cue["duration"] = 0.1
        with self.assertRaisesRegex(ValueError, "transition.duration"):
            model.validate(self.timeline)
        cue["duration"] = 3.1
        with self.assertRaisesRegex(ValueError, "transition.duration"):
            model.validate(self.timeline)
        cue["duration"] = 0.5
        cue["review_status"] = "pending_review"
        with self.assertRaisesRegex(ValueError, "lacks human review"):
            model.validate(self.timeline)

    def test_custom_join_is_not_a_point_operation(self):
        self.timeline["operations"] = [{
            "id": "heart", "method": "heart", "start": 1, "end": 2,
            "review_status": "approved",
        }]
        with self.assertRaisesRegex(ValueError, "Unsupported timeline method"):
            model.validate(self.timeline)

    def test_unsafe_source_and_unsupported_method_are_refused(self):
        self.timeline["picture"][0]["source"] = "../other.mp4"
        with self.assertRaisesRegex(ValueError, "Missing or unsafe"):
            model.validate(self.timeline)
        self.timeline["picture"][0]["source"] = "source.mp4"
        self.timeline["operations"] = [{
            "id": "unknown", "method": "future-effect", "start": 0, "end": 1,
            "review_status": "approved"}]
        with self.assertRaisesRegex(ValueError, "Unsupported timeline method"):
            model.validate(self.timeline)

    def test_hash_command_reports_asset_identity(self):
        import contextlib
        import io

        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli.main(["hash", "--file", str(self.voice)]), 0)
        self.assertEqual(json.loads(output.getvalue())["sha256"],
                         model.sha256_file(self.voice))

    def test_renderer_recipe_change_invalidates_timeline_fingerprint(self):
        before = approval.fingerprint(self.path, self.timeline)
        original_read = Path.read_bytes
        for changed_name in ("xfade_effects.py", "transitions.json"):
            with self.subTest(changed_name=changed_name):
                def altered(path):
                    content = original_read(path)
                    return (content + b"changed recipe" if path.name == changed_name
                            else content)

                with patch.object(Path, "read_bytes", altered):
                    after = approval.fingerprint(self.path, self.timeline)
                self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
