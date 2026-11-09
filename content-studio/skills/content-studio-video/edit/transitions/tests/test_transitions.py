"""Unit tests for the transition catalog, validation, and graph builders."""
import contextlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "transitions.py"
spec = importlib.util.spec_from_file_location("transitions", SOURCE)
transitions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transitions)


class CatalogTests(unittest.TestCase):
    def test_catalog_has_all_article_variants(self):
        items = transitions.load_catalog()["transitions"]
        self.assertEqual(len(items), 29)
        self.assertEqual(len({item["id"] for item in items}), 29)

    def test_every_entry_is_complete(self):
        for item in transitions.load_catalog()["transitions"]:
            self.assertIn(item["fidelity"], ("native", "approximate", "catalog-only"))
            self.assertIsInstance(item["modes"], list)
            self.assertIsInstance(item["name"], str)
            if item["fidelity"] == "catalog-only":
                self.assertEqual(item["modes"], [])
            else:
                self.assertTrue(item["modes"])
            if "join" in item["modes"]:
                self.assertTrue(item.get("xfade"))
            if "point" in item["modes"]:
                self.assertIn(item.get("point", {}).get("type"), ("fade", "blur", "glitch"))

    def test_point_catalog_excludes_join_only(self):
        ids = {item["id"] for item in transitions.list_transitions(mode="point")}
        self.assertIn("fade-through-black", ids)
        self.assertIn("glitch", ids)
        self.assertNotIn("wipe-left", ids)

    def test_join_catalog_excludes_point_only(self):
        ids = {item["id"] for item in transitions.list_transitions(mode="join")}
        self.assertIn("cross-fade", ids)
        self.assertIn("push-down", ids)
        self.assertNotIn("glitch", ids)

    def test_former_catalog_only_entries_have_distinct_custom_recipes(self):
        items = [item for item in transitions.load_catalog()["transitions"]
                 if item.get("xfade") == "custom"]
        self.assertEqual({item["id"] for item in items}, transitions.CUSTOM_JOIN_IDS)
        self.assertEqual(transitions.list_transitions(fidelity="catalog-only"), [])
        expressions = {
            transitions.xfade_options(item["id"], item["xfade"])
            for item in items
        }
        self.assertEqual(len(expressions), 8)
        for item in items:
            self.assertEqual(item["modes"], ["join"])
            self.assertEqual(item["fidelity"], "approximate")

    def test_animated_readme_covers_every_renderable_transition(self):
        # Keep the human-facing capability matrix in sync with the runtime catalog.
        skill = SOURCE.parents[1]
        readme = (skill / "README.md").read_text(encoding="utf-8")
        rows = {}
        for line in readme.splitlines():
            match = re.match(r"^\| \[`([a-z-]+)`\]\(scripts/([a-z_]+)\.py\) \|", line)
            if match:
                effect = match.group(1)
                self.assertNotIn(effect, rows)
                rows[effect] = line.split("|")[2:-1]
                self.assertEqual(match.group(2), effect.replace("-", "_"))
        catalog = transitions.load_catalog()["transitions"]
        self.assertEqual(set(rows), {item["id"] for item in catalog})
        for item in catalog:
            effect = item["id"]
            cells = [cell.strip() for cell in rows[effect]]
            self.assertEqual(cells[0] == "Yes", "point" in item["modes"])
            self.assertEqual(cells[1] == "Yes", "join" in item["modes"])
            self.assertEqual(cells[2], "Yes")
            self.assertEqual(cells[3].lower(), item["fidelity"])
            self.assertIn(f"(previews/{effect}.gif)", cells[5])
            gif = skill / "previews" / f"{effect}.gif"
            self.assertTrue(gif.is_file(), effect)
            self.assertTrue(gif.read_bytes().startswith((b"GIF87a", b"GIF89a")), effect)
            self.assertLess(gif.stat().st_size, 512 * 1024, effect)
            if shutil.which("ffprobe"):
                probe = subprocess.run(
                    ["ffprobe", "-v", "error", "-select_streams", "v:0",
                     "-count_frames", "-show_entries",
                     "stream=width,height,nb_read_frames", "-of", "json", str(gif)],
                    text=True, capture_output=True, check=True,
                )
                stream = json.loads(probe.stdout)["streams"][0]
                self.assertEqual((stream["width"], stream["height"]), (240, 135))
                self.assertGreaterEqual(int(stream["nb_read_frames"]), 10, effect)


class PointValidationTests(unittest.TestCase):
    def test_valid_point_sheet(self):
        data = {"transitions": [
            {"at": 10.0, "id": "fade-through-black", "duration": 0.8},
            {"at": 30.0, "id": "cross-blur", "duration": 0.5},
        ]}
        issues, resolved = transitions.validate_cues(data, video_seconds=60)
        self.assertEqual(issues, [])
        self.assertEqual(resolved[0]["start"], 9.6)
        self.assertEqual(resolved[0]["end"], 10.4)

    def test_unknown_id_rejected(self):
        issues, _ = transitions.validate_cues(
            {"transitions": [{"at": 5, "id": "not-real"}]}
        )
        self.assertTrue(any("unknown transition" in issue for issue in issues))

    def test_join_only_custom_effect_rejected_as_point(self):
        issues, _ = transitions.validate_cues(
            {"transitions": [{"at": 5, "id": "page-turn"}]}
        )
        self.assertTrue(any("not available" in issue for issue in issues))

    def test_wrong_mode_rejected(self):
        issues, _ = transitions.validate_cues(
            {"transitions": [{"at": 5, "id": "wipe-left"}]}, mode="point"
        )
        self.assertTrue(any("not available" in issue for issue in issues))

    def test_overlap_rejected(self):
        data = {"transitions": [
            {"at": 10.0, "id": "glitch", "duration": 0.6},
            {"at": 10.4, "id": "glitch", "duration": 0.6},
        ]}
        issues, _ = transitions.validate_cues(data)
        self.assertTrue(any("overlap" in issue for issue in issues))

    def test_out_of_range_rejected(self):
        issues, _ = transitions.validate_cues(
            {"transitions": [{"at": 0.2, "id": "fade-through-black", "duration": 0.8}]},
            video_seconds=60,
        )
        self.assertTrue(any("starts before" in issue for issue in issues))
        issues, _ = transitions.validate_cues(
            {"transitions": [{"at": 59.9, "id": "fade-through-black", "duration": 0.8}]},
            video_seconds=60,
        )
        self.assertTrue(any("ends after" in issue for issue in issues))

    def test_fade_uses_alpha_overlay(self):
        _, resolved = transitions.validate_cues(
            {"transitions": [{"at": 10.0, "id": "fade-through-black", "duration": 0.8}]}
        )
        graph = transitions.point_filtergraph(resolved, 1920, 1080, 30, 60)
        self.assertIn("color=c=black:s=1920x1080:r=30", graph)
        self.assertIn("fade=t=in:st=9.600000:d=0.400000:alpha=1", graph)
        self.assertIn("fade=t=out:st=10.000000:d=0.400000:alpha=1", graph)
        self.assertIn("overlay=0:0", graph)
        self.assertNotIn("fade=t=out:st=9.600000:d=0.400000:color=black", graph)
        self.assertTrue(graph.startswith("[0:v]"))
        self.assertTrue(graph.endswith("[vout]"))

    def test_burn_uses_orange_overlay(self):
        _, resolved = transitions.validate_cues(
            {"transitions": [{"at": 5.0, "id": "burn", "duration": 0.7}]}
        )
        graph = transitions.point_filtergraph(resolved, 640, 360, 30, 10)
        self.assertIn("color=c=0xFF5A1F", graph)

    def test_display_dimensions_swaps_rotated_frame(self):
        self.assertEqual(
            transitions.display_dimensions(
                {"width": 1920, "height": 1080,
                 "side_data_list": [{"rotation": -90}]}
            ),
            (1080, 1920),
        )
        self.assertEqual(
            transitions.display_dimensions({"width": 1919, "height": 1079}),
            (1918, 1078),
        )

    def test_glitch_chain_enables_each_filter(self):
        _, resolved = transitions.validate_cues(
            {"transitions": [{"at": 10.0, "id": "glitch", "duration": 0.4}]}
        )
        spec = transitions.catalog_index()["glitch"]["point"]
        chain = transitions.point_effect_filters(resolved[0], spec)
        self.assertTrue(chain)
        self.assertTrue(all("enable=" in part for part in chain))


class JoinValidationTests(unittest.TestCase):
    def sheet(self):
        return {
            "inputs": ["a.mp4", "b.mp4", "c.mp4"],
            "transitions": [
                {"after": 0, "id": "cross-fade", "duration": 0.6},
                {"after": 1, "id": "wipe-left", "duration": 0.5},
            ],
        }

    def test_valid_join(self):
        issues, resolved, inputs = transitions.validate_join(self.sheet())
        self.assertEqual(issues, [])
        self.assertEqual([item["after"] for item in resolved], [0, 1])
        self.assertEqual(inputs, ["a.mp4", "b.mp4", "c.mp4"])

    def test_missing_boundary_rejected(self):
        data = self.sheet()
        data["transitions"].pop()
        issues, _, _ = transitions.validate_join(data)
        self.assertTrue(any("missing transitions" in issue for issue in issues))

    def test_point_only_transition_rejected_at_join(self):
        data = self.sheet()
        data["transitions"][0]["id"] = "glitch"
        issues, _, _ = transitions.validate_join(data)
        self.assertTrue(any("not a join transition" in issue for issue in issues))

    def test_join_graph_offsets(self):
        media = [{"duration": 10.0}, {"duration": 8.0}]
        resolved = [{"after": 0, "id": "cross-fade", "duration": 0.5,
                     "xfade": "fade"}]
        graph, label, total = transitions.join_graph(media, resolved, 1920, 1080, 30)
        self.assertIn("offset=9.500000", graph)
        self.assertIn("xfade=transition=fade", graph)
        self.assertEqual(total, 17.5)
        self.assertEqual(label, "x1")

    def test_join_audio_graph(self):
        resolved = [{"duration": 0.6}, {"duration": 0.5}]
        graph, label = transitions.join_audio_graph(3, resolved)
        self.assertIn("acrossfade=d=0.600000", graph)
        self.assertIn("acrossfade=d=0.500000", graph)
        self.assertEqual(label, "ax2")


class TimelineAnnotationTests(unittest.TestCase):
    def test_annotation_attaches_to_matching_clip(self):
        timeline = {
            "schema": "content-studio.edit-timeline.v1",
            "clips": [
                {"order": 1, "timeline_start": 0.0, "timeline_end": 10.0},
                {"order": 2, "timeline_start": 10.0, "timeline_end": 20.0},
            ],
        }
        data = {"transitions": [{"at": 15.0, "id": "cross-blur", "duration": 0.6}]}
        result = transitions.annotate_timeline(timeline, data)
        self.assertEqual(result["clips"][0].get("point_transitions", []), [])
        self.assertEqual(result["clips"][1]["point_transitions"][0]["id"], "cross-blur")
        self.assertEqual(timeline["clips"][1].get("point_transitions", []), [])


class FixedScriptTests(unittest.TestCase):
    def test_every_catalog_entry_has_a_script(self):
        scripts = SOURCE.parent
        for item in transitions.load_catalog()["transitions"]:
            path = scripts / (item["id"].replace("-", "_") + ".py")
            self.assertTrue(path.is_file(), f"missing {path}")
            text = path.read_text(encoding="utf-8")
            self.assertIn(f'TRANSITION_ID = "{item["id"]}"', text)

    def test_fixed_cues_injects_id_without_mutating_source(self):
        data = {"transitions": [{"at": 5.0, "duration": 0.6}]}
        result = transitions.fixed_cues(data, "fade-through-black")
        self.assertEqual(result["transitions"][0]["id"], "fade-through-black")
        self.assertNotIn("id", data["transitions"][0])

    def test_fixed_cues_rejects_other_id(self):
        with self.assertRaises(ValueError):
            transitions.fixed_cues(
                {"transitions": [{"at": 5.0, "id": "glitch"}]},
                "fade-through-black",
            )

    def test_fixed_runner_accepts_custom_join_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            cues = Path(folder) / "cues.json"
            cues.write_text(json.dumps({"inputs": ["a.mp4", "b.mp4"],
                                        "transitions": [{"after": 0, "duration": 0.8}]}))
            with patch.object(transitions, "plan", return_value={
                "mode": "join", "issues": [], "transitions": ["collage"]
            }):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(transitions.run_fixed_transition(
                        "collage", [str(cues), "--plan"]), 0)

    def test_fixed_runner_plans_with_injected_id(self):
        with tempfile.TemporaryDirectory() as folder:
            cues = Path(folder) / "cues.json"
            cues.write_text(json.dumps({"transitions": [
                {"at": 5.0, "duration": 0.8}
            ]}), encoding="utf-8")
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = transitions.run_fixed_transition(
                    "fade-through-black", [str(cues), "--plan"]
                )
            self.assertEqual(code, 0)
            result = json.loads(buffer.getvalue())
            self.assertEqual(result["transitions"][0]["id"], "fade-through-black")

    def test_fixed_runner_rejects_wrong_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            cues = Path(folder) / "cues.json"
            cues.write_text(json.dumps({"transitions": [
                {"at": 5.0, "duration": 0.6}
            ]}), encoding="utf-8")
            buffer = io.StringIO()
            with contextlib.redirect_stderr(buffer):
                code = transitions.run_fixed_transition(
                    "push-left", [str(cues), "--plan"]
                )
            self.assertEqual(code, 1)
            self.assertIn("join mode", buffer.getvalue())

    def test_script_command_lists_all(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = transitions.main(["scripts"])
        self.assertEqual(code, 0)
        lines = [line for line in buffer.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(lines), 29)
        self.assertIn("fade-through-black", buffer.getvalue())
        self.assertIn("scripts/fade_through_black.py", buffer.getvalue())


class CliTests(unittest.TestCase):
    def test_list_json(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = transitions.main(["list", "--json"])
        self.assertEqual(code, 0)
        items = json.loads(buffer.getvalue())
        self.assertEqual(len(items), 29)

    def test_plan_point_sheet(self):
        with tempfile.TemporaryDirectory() as folder:
            cues = Path(folder) / "cues.json"
            cues.write_text(json.dumps({"transitions": [
                {"at": 5.0, "id": "fade-through-white", "duration": 0.8}
            ]}), encoding="utf-8")
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = transitions.main(["plan", str(cues)])
            self.assertEqual(code, 0)
            result = json.loads(buffer.getvalue())
            self.assertEqual(result["mode"], "point")
            self.assertEqual(result["duration_change_seconds"], 0.0)

    def test_validate_returns_nonzero_on_issue(self):
        with tempfile.TemporaryDirectory() as folder:
            cues = Path(folder) / "cues.json"
            cues.write_text(json.dumps({"transitions": [
                {"at": 5.0, "id": "page-turn"}
            ]}), encoding="utf-8")
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = transitions.main(["validate", str(cues)])
            self.assertEqual(code, 1)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required")
class CustomJoinRenderTests(unittest.TestCase):
    def test_all_eight_custom_joins_decode_and_crossfade_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inputs = []
            for index, (color, tone) in enumerate((("red", 440), ("blue", 660))):
                source = root / f"source-{index}.mp4"
                result = subprocess.run([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"color={color}:s=64x64:r=10:d=1.2",
                    "-f", "lavfi", "-i", f"sine=frequency={tone}:duration=1.2",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", str(source),
                ], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                inputs.append(source)
            originals = [source.read_bytes() for source in inputs]
            for effect in sorted(transitions.CUSTOM_JOIN_IDS):
                with self.subTest(effect=effect):
                    output = root / f"{effect}.mp4"
                    result = transitions.render_join({
                        "inputs": [str(source) for source in inputs],
                        "transitions": [{"after": 0, "id": effect,
                                         "duration": 0.4}],
                    }, output, size=(64, 64), fps=10)
                    self.assertEqual(result["audio"], "crossfade")
                    self.assertAlmostEqual(result["output_seconds"], 2.0)
                    delivered = transitions.probe_media(output)
                    self.assertTrue(delivered["has_audio"])
                    self.assertAlmostEqual(delivered["duration"], 2.0, delta=.15)
            self.assertEqual([source.read_bytes() for source in inputs], originals)


if __name__ == "__main__":
    unittest.main()
