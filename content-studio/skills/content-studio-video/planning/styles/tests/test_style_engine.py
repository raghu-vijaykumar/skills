import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "scripts" / "style_engine.py"
spec = importlib.util.spec_from_file_location("style_engine", path)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

class StyleEngineTests(unittest.TestCase):
    def test_alias(self):
        self.assertEqual(engine.resolve("3blue1brown"), "math-visual")

    def test_branch_education(self):
        self.assertEqual(engine.resolve("branch-education"), "engineering-cutaway")
        self.assertEqual(engine.recommend("processor chip circuit"), "engineering-cutaway")
        result = engine.plan({"scenes": [{"id": "cpu", "duration_seconds": 10, "style": "branch-education"}]})
        self.assertEqual(result["scenes"][0]["renderer"], "blender")
        self.assertIn("cross-section", result["scenes"][0]["techniques"])

    def test_recommend(self):
        self.assertEqual(engine.recommend("gradient vector equation"), "math-visual")
        self.assertEqual(engine.resolve("core-explainer"), "core-explainer")
        self.assertEqual(engine.recommend("why browser cache stays stale after deploy"), "core-explainer")

    def test_hybrid_scene_plan(self):
        result = engine.plan({"topic": "Education", "scenes": [
            {"id": "intro", "duration_seconds": 5, "style": "kurzgesagt"},
            {"id": "proof", "duration_seconds": 12, "style": "3blue1brown"},
        ]})
        self.assertEqual([s["style"] for s in result["scenes"]], ["vector-science", "math-visual"])
        self.assertTrue(result["review_required"])

    def test_duplicate_scene_rejected(self):
        with self.assertRaises(ValueError):
            engine.plan({"scenes": [{"id": "a", "duration_seconds": 2}, {"id": "a", "duration_seconds": 3}]})

    def test_invalid_duration_rejected(self):
        with self.assertRaises(ValueError):
            engine.plan({"scenes": [{"id": "a", "duration_seconds": -1}]})

    def test_blender_scene_selects_only_matching_rendered_demo(self):
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            result = engine.plan({"scenes": [{"id": "clamp", "duration_seconds": 4,
                "visual_intent": "Animate a realistic mechanical clamp"}]})
        scene = result["scenes"][0]
        self.assertEqual(scene["style"], "cinematic-3d")
        self.assertEqual(scene["blender"]["builder"], "examples/clamp.py")
        self.assertEqual(scene["status"], "planned_not_rendered")

    def test_blender_style_override_and_unsupported_combination(self):
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            result = engine.plan({"scenes": [{"id": "unsupported", "duration_seconds": 4,
                "style": "anime-style", "visual_intent": "Realistic clamp"}]})
        scene = result["scenes"][0]
        self.assertEqual(scene["blender"]["style"], "anime-style")
        self.assertIsNone(scene["blender"]["builder"])
        self.assertEqual(scene["status"], "needs_builder")
        self.assertTrue(result["warnings"])
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            forced = engine.plan({"scenes": [{"id": "courier", "duration_seconds": 4,
                "visual_intent": "A courier waves", "blender_style": "cartoon-style"}]})
        self.assertEqual(forced["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(forced["scenes"][0]["blender"]["builder"],
                         "examples/character.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            lowpoly = engine.plan({"scenes": [{"id": "lamp", "duration_seconds": 4,
                "visual_intent": "A desk lamp switches on", "blender_style": "lowpoly-style"}]})
        self.assertEqual(lowpoly["scenes"][0]["blender"]["builder"],
                         "examples/lowpoly_lamp.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            voxel = engine.plan({"scenes": [{"id": "voxel-lamp", "duration_seconds": 3,
                "visual_intent": "A desk lamp switches on", "blender_style": "voxel-style"}]})
        self.assertEqual(voxel["scenes"][0]["blender"]["builder"],
                         "examples/voxel_lamp.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            isometric = engine.plan({"scenes": [{"id": "iso-lamp", "duration_seconds": 3,
                "visual_intent": "A desk lamp switches on", "blender_style": "isometric-style"}]})
        self.assertEqual(isometric["scenes"][0]["blender"]["builder"],
                         "examples/isometric_lamp.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            realistic = engine.plan({"scenes": [{"id": "real-lamp", "duration_seconds": 3,
                "visual_intent": "A desk lamp adjusts", "blender_style": "realistic-style"}]})
        self.assertEqual(realistic["scenes"][0]["blender"]["builder"],
                         "examples/realistic_lamp.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            horror = engine.plan({"scenes": [{"id": "horror-hall", "duration_seconds": 3,
                "visual_intent": "A horror corridor reveals a door"}]})
        self.assertEqual(horror["scenes"][0]["blender"]["builder"],
                         "examples/horror_corridor.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            psx = engine.plan({"scenes": [{"id": "psx-hall", "duration_seconds": 3,
                "visual_intent": "A PSX horror hall reveals a CRT"}]})
        self.assertEqual(psx["scenes"][0]["blender"]["builder"],
                         "examples/psx_horror.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            anime = engine.plan({"scenes": [{"id": "anime-heroine", "duration_seconds": 3,
                "visual_intent": "An anime heroine blinks and raises an arm"}]})
        self.assertEqual(anime["scenes"][0]["blender"]["builder"],
                         "examples/anime_heroine.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            unnamed = engine.plan({"scenes": [{"id": "heroine", "duration_seconds": 3,
                "visual_intent": "A heroine blinks and raises an arm"}]})
        self.assertEqual(unnamed["scenes"][0]["blender"]["builder"],
                         "examples/anime_heroine.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            windmill = engine.plan({"scenes": [{"id": "windmill", "duration_seconds": 3,
                "visual_intent": "A windmill cottage turns on an island"}]})
        self.assertEqual(windmill["scenes"][0]["blender"]["builder"],
                         "examples/stylized_windmill.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            cartoon = engine.plan({"scenes": [{"id": "cartoon-mascot", "duration_seconds": 3,
                "visual_intent": "A bouncy ball mascot jumps and squashes"}]})
        self.assertEqual(cartoon["scenes"][0]["blender"]["builder"],
                         "examples/cartoon_bounce.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            comic = engine.plan({"scenes": [{"id": "comic-rocket", "duration_seconds": 3,
                "visual_intent": "A rocket whooshes through a panel"}]})
        self.assertEqual(comic["scenes"][0]["blender"]["builder"],
                         "examples/comic_rocket.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            manga = engine.plan({"scenes": [{"id": "manga-gaze", "duration_seconds": 3,
                "visual_intent": "An eye shifts its gaze across a panel"}]})
        self.assertEqual(manga["scenes"][0]["blender"]["builder"],
                         "examples/manga_gaze.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            pixel = engine.plan({"scenes": [{"id": "pixel-chest", "duration_seconds": 4,
                "visual_intent": "A treasure chest opens and emits sparks"}]})
        self.assertEqual(pixel["scenes"][0]["blender"]["builder"],
                         "examples/pixel_chest.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            painted = engine.plan({"scenes": [{"id": "painted-teacup", "duration_seconds": 3,
                "visual_intent": "A wildflower teacup turns and steams"}]})
        self.assertEqual(painted["scenes"][0]["blender"]["builder"],
                         "examples/painted_teacup.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            river = engine.plan({"scenes": [{"id": "watercolor-river", "duration_seconds": 3,
                "visual_intent": "A sailboat drifts across a river"}]})
        self.assertEqual(river["scenes"][0]["blender"]["builder"],
                         "examples/watercolor_river.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            paper = engine.plan({"scenes": [{"id": "paper-butterfly", "duration_seconds": 3,
                "visual_intent": "A butterfly flaps across a craft table"}]})
        self.assertEqual(paper["scenes"][0]["blender"]["builder"],
                         "examples/paper_butterfly.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            chibi = engine.plan({"scenes": [{"id": "chibi-postal", "duration_seconds": 3,
                "visual_intent": "A tiny postal courier hops and offers a letter"}]})
        self.assertEqual(chibi["scenes"][0]["blender"]["builder"],
                         "examples/chibi_courier.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            noir = engine.plan({"scenes": [{"id": "noir-walk", "duration_seconds": 3,
                "visual_intent": "A fedora detective walks through rainy light"}]})
        self.assertEqual(noir["scenes"][0]["blender"]["builder"],
                         "examples/noir_detective.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            minimal = engine.plan({"scenes": [{"id": "minimal-swing", "duration_seconds": 3,
                "visual_intent": "A pendulum sculpture swings through empty space"}]})
        self.assertEqual(minimal["scenes"][0]["blender"]["builder"],
                         "examples/minimal_pendulum.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            vector = engine.plan({"scenes": [{"id": "sprout", "duration_seconds": 3,
                "visual_intent": "A sprout grows into a flower"}]})
        self.assertEqual(vector["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(vector["scenes"][0]["blender"]["builder"],
                         "examples/vector_sprout.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            retro = engine.plan({"scenes": [{"id": "arcade", "duration_seconds": 4,
                "visual_intent": "A spaceship fires at an asteroid"}]})
        self.assertEqual(retro["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(retro["scenes"][0]["blender"]["builder"],
                         "examples/retro_8bit_ship.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            retro16 = engine.plan({"scenes": [{"id": "fox", "duration_seconds": 4,
                "visual_intent": "A fox walks beside a waterfall"}]})
        self.assertEqual(retro16["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(retro16["scenes"][0]["blender"]["builder"],
                         "examples/retro_16bit_fox.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            hd2d = engine.plan({"scenes": [{"id": "bridge", "duration_seconds": 3,
                "visual_intent": "A traveler carries a lantern across a bridge"}]})
        self.assertEqual(hd2d["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(hd2d["scenes"][0]["blender"]["builder"],
                         "examples/hd2d_bridge.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            aero = engine.plan({"scenes": [{"id": "aero", "duration_seconds": 3,
                "visual_intent": "A glossy aqua dashboard grows a leaf"}]})
        self.assertEqual(aero["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(aero["scenes"][0]["blender"]["builder"],
                         "examples/aero_dashboard.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            cosmic = engine.plan({"scenes": [{"id": "cosmic", "duration_seconds": 3,
                "visual_intent": "An impossible aperture looms over a tiny witness"}]})
        self.assertEqual(cosmic["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(cosmic["scenes"][0]["blender"]["builder"],
                         "examples/cosmic_aperture.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            hand = engine.plan({"scenes": [{"id": "hand", "duration_seconds": 3,
                "visual_intent": "A hand unfolds a fused metal sixth digit"}]})
        self.assertEqual(hand["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(hand["scenes"][0]["blender"]["builder"],
                         "examples/mutating_hand.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            analog = engine.plan({"scenes": [{"id": "training", "duration_seconds": 3,
                "visual_intent": "A training room security camera records an empty chair"}]})
        self.assertEqual(analog["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(analog["scenes"][0]["blender"]["builder"],
                         "examples/analog_training.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            liminal = engine.plan({"scenes": [{"id": "pool", "duration_seconds": 3,
                "visual_intent": "An empty tiled pool hall repeats endlessly"}]})
        self.assertEqual(liminal["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(liminal["scenes"][0]["blender"]["builder"],
                         "examples/liminal_pool.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            folk = engine.plan({"scenes": [{"id": "rite", "duration_seconds": 3,
                "visual_intent": "A sunlit village field surrounds a wicker effigy"}]})
        self.assertEqual(folk["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(folk["scenes"][0]["blender"]["builder"],
                         "examples/folk_ritual.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            puppet = engine.plan({"scenes": [{"id": "pip", "duration_seconds": 3,
                "visual_intent": "A cheerful felt puppet on a children's show stage turns wrong"}]})
        self.assertEqual(puppet["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(puppet["scenes"][0]["blender"]["builder"],
                         "examples/puppet_stage.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            dream = engine.plan({"scenes": [{"id": "play", "duration_seconds": 3,
                "visual_intent": "An oversized alphabet block floats above an empty playground as a door opens"}]})
        self.assertEqual(dream["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(dream["scenes"][0]["blender"]["builder"],
                         "examples/dream_playground.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            indie = engine.plan({"scenes": [{"id": "cabin", "duration_seconds": 3,
                "visual_intent": "A first-person flashlight follows red markers to a forest cabin as its window goes dark"}]})
        self.assertEqual(indie["scenes"][0]["style"], "cinematic-3d")
        self.assertEqual(indie["scenes"][0]["blender"]["builder"],
                         "examples/indie_cabin.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            fantasy = engine.plan({"scenes": [{"id": "gate", "duration_seconds": 3,
                "visual_intent": "A stone castle lowers its oak drawbridge over a moat"}]})
        self.assertEqual(fantasy["scenes"][0]["blender"]["builder"],
                         "examples/fantasy_gate.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            explicit = engine.plan({"scenes": [{"id": "gate", "duration_seconds": 3,
                "style": "fantasy-worlds", "visual_intent": "A castle lowers a drawbridge"}]})
        self.assertEqual(explicit["scenes"][0]["blender"]["world"], "fantasy-worlds")
        self.assertEqual(explicit["scenes"][0]["blender"]["builder"],
                         "examples/fantasy_gate.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            cyberpunk = engine.plan({"scenes": [{"id": "alley", "duration_seconds": 3,
                "visual_intent": "A parcel drone crosses a cyberpunk alley"}]})
        self.assertEqual(cyberpunk["scenes"][0]["blender"]["builder"],
                         "examples/cyberpunk_alley.py")
        self.assertEqual(cyberpunk["scenes"][0]["blender"]["world"],
                         "sci-fi-punk-worlds")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            viking = engine.plan({"scenes": [{"id": "longship", "duration_seconds": 3,
                "visual_intent": "A Viking longship crosses a rocky fjord"}]})
        self.assertEqual(viking["scenes"][0]["blender"]["builder"],
                         "examples/viking_longship.py")
        self.assertEqual(viking["scenes"][0]["blender"]["world"],
                         "historical-worlds")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            wasteland = engine.plan({"scenes": [{"id": "fuel-stop", "duration_seconds": 3,
                "visual_intent": "A scavenger cart crosses a post-apocalyptic wasteland fuel station"}]})
        self.assertEqual(wasteland["scenes"][0]["blender"]["builder"],
                         "examples/wasteland_station.py")
        self.assertEqual(wasteland["scenes"][0]["blender"]["world"],
                         "apocalypse-worlds")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            kelp = engine.plan({"scenes": [{"id": "kelp", "duration_seconds": 3,
                "visual_intent": "An underwater kelp forest with fish and rising bubbles"}]})
        self.assertEqual(kelp["scenes"][0]["blender"]["builder"],
                         "examples/kelp_forest.py")
        self.assertEqual(kelp["scenes"][0]["blender"]["world"],
                         "biome-worlds")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            cozy = engine.plan({"scenes": [{"id": "nook", "duration_seconds": 3,
                "visual_intent": "A cozy reading nook with a rocking chair and warm lamp"}]})
        self.assertEqual(cozy["scenes"][0]["blender"]["builder"],
                         "examples/cozy_nook.py")
        self.assertEqual(cozy["scenes"][0]["blender"]["world"],
                         "cozy-wholesome-mood")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            gritty = engine.plan({"scenes": [{"id": "depot", "duration_seconds": 3,
                "visual_intent": "A dark gritty freight depot with a moving crane"}]})
        self.assertEqual(gritty["scenes"][0]["blender"]["builder"],
                         "examples/gritty_depot.py")
        self.assertEqual(gritty["scenes"][0]["blender"]["world"],
                         "dark-gritty-mood")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            dream = engine.plan({"scenes": [{"id": "threshold", "duration_seconds": 3,
                "visual_intent": "A dreamlike floating doorway over a mirror sea"}]})
        self.assertEqual(dream["scenes"][0]["blender"]["builder"],
                         "examples/dream_tide.py")
        self.assertEqual(dream["scenes"][0]["blender"]["world"],
                         "dream-surreal-mood")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            retrowave = engine.plan({"scenes": [{"id": "highway", "duration_seconds": 3,
                "visual_intent": "A synthwave grid highway with a chrome car"}]})
        self.assertEqual(retrowave["scenes"][0]["blender"]["builder"],
                         "examples/retrowave_highway.py")
        self.assertEqual(retrowave["scenes"][0]["blender"]["world"],
                         "neon-retrofuturism")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            brutalist = engine.plan({"scenes": [{"id": "archive", "duration_seconds": 3,
                "visual_intent": "A brutalist concrete archive gateway opens"}]})
        self.assertEqual(brutalist["scenes"][0]["blender"]["builder"],
                         "examples/brutalist_archive.py")
        self.assertEqual(brutalist["scenes"][0]["blender"]["world"],
                         "brutalist-mood")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            combat = engine.plan({"scenes": [{"id": "duel", "duration_seconds": 3,
                "visual_intent": "A sword duel in a combat arena"}]})
        self.assertEqual(combat["scenes"][0]["blender"]["builder"],
                         "examples/action_arena.py")
        self.assertEqual(combat["scenes"][0]["blender"]["genre"],
                         "genre-action-combat")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            explicit_combat = engine.plan({"scenes": [{"id": "duel", "duration_seconds": 3,
                "style": "genre-action-combat", "visual_intent": "A sparring arena"}]})
        self.assertEqual(explicit_combat["scenes"][0]["blender"]["builder"],
                         "examples/action_arena.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            genre_override = engine.plan({"scenes": [{"id": "duel", "duration_seconds": 3,
                "blender_genre": "genre-action-combat",
                "visual_intent": "A sparring arena"}]})
        self.assertEqual(genre_override["scenes"][0]["blender"]["genre"],
                         "genre-action-combat")
        self.assertEqual(genre_override["scenes"][0]["blender"]["builder"],
                         "examples/action_arena.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            shooter = engine.plan({"scenes": [{"id": "range", "duration_seconds": 3,
                "visual_intent": "An FPS shooter rooftop cover lane"}]})
        self.assertEqual(shooter["scenes"][0]["blender"]["genre"],
                         "genre-shooter")
        self.assertEqual(shooter["scenes"][0]["blender"]["builder"],
                         "examples/shooter_rooftop.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            rpg = engine.plan({"scenes": [{"id": "hub", "duration_seconds": 3,
                "visual_intent": "An RPG quest hub with loot rarity"}]})
        self.assertEqual(rpg["scenes"][0]["blender"]["genre"], "genre-rpg")
        self.assertEqual(rpg["scenes"][0]["blender"]["builder"],
                         "examples/rpg_quest_hub.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            survival = engine.plan({"scenes": [{"id": "refuge", "duration_seconds": 3,
                "visual_intent": "A survival shelter with a crafting bench"}]})
        self.assertEqual(survival["scenes"][0]["blender"]["genre"], "genre-survival")
        self.assertEqual(survival["scenes"][0]["blender"]["builder"],
                         "examples/survival_shelter.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            stealth = engine.plan({"scenes": [{"id": "patrol", "duration_seconds": 3,
                "visual_intent": "A stealth infiltration route with a shadow patrol"}]})
        self.assertEqual(stealth["scenes"][0]["blender"]["genre"], "genre-stealth")
        self.assertEqual(stealth["scenes"][0]["blender"]["builder"],
                         "examples/stealth_infiltration.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            puzzle = engine.plan({"scenes": [{"id": "jump", "duration_seconds": 3,
                "visual_intent": "A puzzle platformer with a pressure pad bridge"}]})
        self.assertEqual(puzzle["scenes"][0]["blender"]["genre"],
                         "genre-puzzle-platformer")
        self.assertEqual(puzzle["scenes"][0]["blender"]["builder"],
                         "examples/puzzle_platformer.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            modular = engine.plan({"scenes": [{"id": "gate", "duration_seconds": 3,
                "visual_intent": "A metroidvania ability gate between room modules"}]})
        self.assertEqual(modular["scenes"][0]["blender"]["genre"],
                         "genre-metroidvania-roguelike")
        self.assertEqual(modular["scenes"][0]["blender"]["builder"],
                         "examples/modular_gate.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            soulslike = engine.plan({"scenes": [{"id": "gate", "duration_seconds": 3,
                "visual_intent": "A soulslike fog gate beside a bonfire causeway"}]})
        self.assertEqual(soulslike["scenes"][0]["blender"]["genre"],
                         "genre-soulslike")
        self.assertEqual(soulslike["scenes"][0]["blender"]["builder"],
                         "examples/soulslike_causeway.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            strategy = engine.plan({"scenes": [{"id": "settlement", "duration_seconds": 3,
                "visual_intent": "An isometric colony sim with resource dispatch"}]})
        self.assertEqual(strategy["scenes"][0]["blender"]["genre"],
                         "genre-strategy-sim")
        self.assertEqual(strategy["scenes"][0]["blender"]["builder"],
                         "examples/strategy_settlement.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            circuit = engine.plan({"scenes": [{"id": "race", "duration_seconds": 3,
                "visual_intent": "A circuit sprint with two team color cars"}]})
        self.assertEqual(circuit["scenes"][0]["blender"]["genre"],
                         "genre-racing-sports")
        self.assertEqual(circuit["scenes"][0]["blender"]["builder"],
                         "examples/circuit_sprint.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            narrative = engine.plan({"scenes": [{"id": "choice", "duration_seconds": 3,
                "visual_intent": "A visual novel station letter choice"}]})
        self.assertEqual(narrative["scenes"][0]["blender"]["genre"],
                         "genre-narrative-vn")
        self.assertEqual(narrative["scenes"][0]["blender"]["builder"],
                         "examples/station_letter.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            card = engine.plan({"scenes": [{"id": "card", "duration_seconds": 3,
                "visual_intent": "A deck builder card table choice"}]})
        self.assertEqual(card["scenes"][0]["blender"]["genre"],
                         "genre-card-party-idle")
        self.assertEqual(card["scenes"][0]["blender"]["builder"],
                         "examples/card_table.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            crossing = engine.plan({"scenes": [{"id": "travel", "duration_seconds": 3,
                "visual_intent": "An open world biome crossing"}]})
        self.assertEqual(crossing["scenes"][0]["blender"]["genre"],
                         "genre-open-world-sandbox")
        self.assertEqual(crossing["scenes"][0]["blender"]["builder"],
                         "examples/open_world_crossing.py")
        with patch.object(engine, "renderer_executable", return_value=sys.executable):
            era = engine.plan({"scenes": [{"id": "era", "duration_seconds": 3,
                "visual_intent": "A PS1 PS5 spaceship comparison"}]})
        self.assertEqual(era["scenes"][0]["blender"]["era"],
                         "visual-console-eras")
        self.assertEqual(era["scenes"][0]["blender"]["builder"],
                         "examples/console_era_flight.py")
        for prompt, skill in (("A polished brushed ceramic material study", "materials"),
                              ("A material lookdev swatch lab", "lookdev"),
                              ("A three point light sweep over material swatches", "lighting")):
            with patch.object(engine, "renderer_executable", return_value=sys.executable):
                craft = engine.plan({"scenes": [{"id": "lab", "duration_seconds": 3,
                    "visual_intent": prompt}]})
            self.assertEqual(craft["scenes"][0]["blender"]["capability"], skill)
            self.assertEqual(craft["scenes"][0]["blender"]["builder"],
                             "examples/material_light_lab.py")
        for prompt, skill in (("An emotional camera push", "camera-cinematography"),
                              ("A headless Eevee narrative render", "rendering"),
                              ("A sealed letter keyframe rise", "animation")):
            with patch.object(engine, "renderer_executable", return_value=sys.executable):
                technical = engine.plan({"scenes": [{"id": "tech", "duration_seconds": 3,
                    "visual_intent": prompt}]})
            self.assertEqual(technical["scenes"][0]["blender"]["capability"], skill)
            self.assertEqual(technical["scenes"][0]["blender"]["builder"],
                             "examples/station_letter.py")

    def test_blender_overrides_require_compatible_editorial_style(self):
        with self.assertRaisesRegex(ValueError, "Blender overrides require"):
            engine.plan({"scenes": [{"id": "bad", "duration_seconds": 4,
                "style": "core-explainer", "blender_style": "cartoon-style"}]})

    def test_explicit_blender_executable_path(self):
        with patch.dict(os.environ, {"CONTENT_STUDIO_BLENDER_EXE": sys.executable}):
            self.assertEqual(engine.renderer_executable("blender"), sys.executable)

if __name__ == "__main__":
    unittest.main()
