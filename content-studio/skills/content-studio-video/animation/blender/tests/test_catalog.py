"""Keep the full roadmap honest about which examples have rendered evidence."""

import copy
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "catalog.py"
SPEC = importlib.util.spec_from_file_location("blender_catalog", SCRIPT)
catalog_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog_module)


class CatalogTests(unittest.TestCase):
    def test_all_named_skills_have_one_category_dependencies_and_immutable_source(self):
        entries = catalog_module.catalog()
        self.assertEqual(len(entries), 94)
        self.assertEqual(len({entry["id"] for entry in entries}), 94)
        self.assertEqual(sum(entry["status"] == "Rendered" for entry in entries), 69)
        for entry in entries:
            self.assertTrue(entry["source"].startswith(catalog_module.UPSTREAM + "/"))
            self.assertEqual(entry["route"], "content-studio-video-animation")
            self.assertTrue(all(name in {item["id"] for item in entries}
                                for name in entry["dependencies"]))

    def test_known_demo_route_is_reviewable_and_generic_object_stays_catalogued(self):
        result = catalog_module.route("Animate a realistic mechanical clamp")
        self.assertEqual((result["subject"], result["style"]),
                         ("hard-surface", "realistic-style"))
        self.assertEqual(result["render_method"], "blender-shot")
        self.assertEqual(result["builder"], "examples/clamp.py")
        self.assertTrue(result["review_required"])
        generic = catalog_module.route("Animate an industrial machine")
        self.assertIsNone(generic["render_method"])
        self.assertEqual(generic["status"], "Catalogued")
        self.assertEqual(catalog_module.route("A cel-shaded courier waves")["builder"],
                         "examples/character.py")
        self.assertEqual(catalog_module.route("An atmospheric corridor push")["builder"],
                         "examples/corridor.py")
        self.assertEqual(catalog_module.route("An adjustable desk lamp lights a notebook")["builder"],
                         "examples/lamp.py")
        self.assertEqual(catalog_module.route("Model a desk lamp", subject="blender-modeler")["builder"],
                         "examples/lamp.py")
        lowpoly = catalog_module.route("Animate a low-poly desk lamp switching on")
        self.assertEqual((lowpoly["subject"], lowpoly["style"]),
                         ("prop-artist", "lowpoly-style"))
        self.assertEqual(lowpoly["builder"], "examples/lowpoly_lamp.py")
        self.assertIsNone(catalog_module.route("Animate a low-poly car")["builder"])
        voxel = catalog_module.route("Animate a voxel desk lamp switching on")
        self.assertEqual((voxel["subject"], voxel["style"]),
                         ("prop-artist", "voxel-style"))
        self.assertEqual(voxel["builder"], "examples/voxel_lamp.py")
        self.assertIsNone(catalog_module.route("Animate a voxel car")["builder"])
        isometric = catalog_module.route("Animate an isometric desk lamp switching on")
        self.assertEqual((isometric["subject"], isometric["style"]),
                         ("prop-artist", "isometric-style"))
        self.assertEqual(isometric["builder"], "examples/isometric_lamp.py")
        self.assertIsNone(catalog_module.route("Animate an isometric city")["builder"])
        realistic = catalog_module.route("Animate a realistic desk lamp")
        self.assertEqual((realistic["subject"], realistic["style"]),
                         ("prop-artist", "realistic-style"))
        self.assertEqual(realistic["builder"], "examples/realistic_lamp.py")
        self.assertIsNone(catalog_module.route("Animate a realistic car")["builder"])
        horror = catalog_module.route("A psychological horror corridor with a door reveal")
        self.assertEqual((horror["subject"], horror["style"]),
                         ("environment-artist", "horror-style"))
        self.assertEqual(horror["builder"], "examples/horror_corridor.py")
        self.assertIsNone(catalog_module.route("A horror desk lamp")["builder"])
        psx = catalog_module.route("A PSX horror hall with one CRT")
        self.assertEqual((psx["subject"], psx["style"]),
                         ("environment-artist", "psx-horror-style"))
        self.assertEqual(psx["builder"], "examples/psx_horror.py")
        self.assertIsNone(catalog_module.route("A PSX horror creature")["builder"])
        anime = catalog_module.route("An anime heroine blinks and raises her arm")
        self.assertEqual((anime["subject"], anime["style"]),
                         ("character-artist", "anime-style"))
        self.assertEqual(anime["builder"], "examples/anime_heroine.py")
        unnamed = catalog_module.route("A heroine blinks and raises her arm")
        self.assertEqual(unnamed["style"], "anime-style")
        self.assertEqual(unnamed["builder"], "examples/anime_heroine.py")
        self.assertIsNone(catalog_module.route("An anime creature waves")["builder"])
        stylized = catalog_module.route("A windmill cottage turns on an island")
        self.assertEqual((stylized["subject"], stylized["style"]),
                         ("environment-artist", "stylized-style"))
        self.assertEqual(stylized["builder"], "examples/stylized_windmill.py")
        self.assertIsNone(catalog_module.route("A stylized cityscape")["builder"])
        cartoon = catalog_module.route("A bouncy ball mascot jumps and squashes")
        self.assertEqual((cartoon["subject"], cartoon["style"]),
                         ("character-artist", "cartoon-style"))
        self.assertEqual(cartoon["builder"], "examples/cartoon_bounce.py")
        self.assertIsNone(catalog_module.route("A cartoon dragon jumps")["builder"])
        comic = catalog_module.route("A rocket whooshes through a panel")
        self.assertEqual((comic["subject"], comic["style"]),
                         ("vehicle-artist", "comic-book-style"))
        self.assertEqual(comic["builder"], "examples/comic_rocket.py")
        self.assertIsNone(catalog_module.route("A comic car accelerates")["builder"])
        manga = catalog_module.route("An eye shifts its gaze across a panel")
        self.assertEqual((manga["subject"], manga["style"]),
                         ("character-artist", "manga-style"))
        self.assertEqual(manga["builder"], "examples/manga_gaze.py")
        self.assertIsNone(catalog_module.route("A manga creature growls")["builder"])
        pixel = catalog_module.route("A treasure chest opens and emits sparks")
        self.assertEqual((pixel["subject"], pixel["style"]),
                         ("prop-artist", "pixel-art-style"))
        self.assertEqual(pixel["builder"], "examples/pixel_chest.py")
        self.assertIsNone(catalog_module.route("A pixel-art bottle spins")["builder"])
        painted = catalog_module.route("A wildflower teacup turns and steams")
        self.assertEqual((painted["subject"], painted["style"]),
                         ("prop-artist", "hand-painted-style"))
        self.assertEqual(painted["builder"], "examples/painted_teacup.py")
        self.assertIsNone(catalog_module.route("A hand-painted car drives")["builder"])
        river = catalog_module.route("A sailboat drifts across a river")
        self.assertEqual((river["subject"], river["style"]),
                         ("vehicle-artist", "painterly-style"))
        self.assertEqual(river["builder"], "examples/watercolor_river.py")
        self.assertIsNone(catalog_module.route("A watercolor airplane flies")["builder"])
        paper = catalog_module.route("A butterfly flaps across a craft table")
        self.assertEqual((paper["subject"], paper["style"]),
                         ("creature-artist", "stop-motion-craft-style"))
        self.assertEqual(paper["builder"], "examples/paper_butterfly.py")
        self.assertIsNone(catalog_module.route("A stop-motion clay dragon walks")["builder"])
        chibi = catalog_module.route("A tiny postal courier hops and offers a letter")
        self.assertEqual((chibi["subject"], chibi["style"]),
                         ("character-artist", "chibi-style"))
        self.assertEqual(chibi["builder"], "examples/chibi_courier.py")
        self.assertIsNone(catalog_module.route("A chibi dragon carries mail")["builder"])
        noir = catalog_module.route("A fedora detective walks through rainy light")
        self.assertEqual((noir["subject"], noir["style"]),
                         ("character-artist", "noir-style"))
        self.assertEqual(noir["builder"], "examples/noir_detective.py")
        self.assertIsNone(catalog_module.route("A noir bicycle turns")["builder"])
        minimal = catalog_module.route("A pendulum sculpture swings through empty space")
        self.assertEqual((minimal["subject"], minimal["style"]),
                         ("blender-modeler", "minimalist-style"))
        self.assertEqual(minimal["builder"], "examples/minimal_pendulum.py")
        self.assertIsNone(catalog_module.route("A minimalist car drives")["builder"])
        vector = catalog_module.route("A sprout grows into a flower")
        self.assertEqual(vector["subject"], "vegetation-artist")
        self.assertEqual(vector["style"], "vector-style")
        self.assertEqual(vector["builder"], "examples/vector_sprout.py")
        self.assertIsNone(catalog_module.route("A vector forest grows")["builder"])
        retro = catalog_module.route("A spaceship fires at an asteroid")
        self.assertEqual(retro["subject"], "vehicle-artist")
        self.assertEqual(retro["style"], "retro-8bit-style")
        self.assertEqual(retro["builder"], "examples/retro_8bit_ship.py")
        self.assertIsNone(catalog_module.route("An 8-bit car races")["builder"])
        retro16 = catalog_module.route("A fox walks beside a waterfall")
        self.assertEqual(retro16["subject"], "creature-artist")
        self.assertEqual(retro16["style"], "retro-16bit-style")
        self.assertEqual(retro16["builder"], "examples/retro_16bit_fox.py")
        self.assertIsNone(catalog_module.route("A 16-bit fox in a city")["builder"])
        hd2d = catalog_module.route("A traveler carries a lantern across a bridge")
        self.assertEqual(hd2d["subject"], "character-artist")
        self.assertEqual(hd2d["style"], "hd-2d-style")
        self.assertEqual(hd2d["builder"], "examples/hd2d_bridge.py")
        self.assertIsNone(catalog_module.route("An HD-2D car crosses a bridge")["builder"])
        aero = catalog_module.route("A glossy aqua dashboard grows a leaf")
        self.assertEqual(aero["subject"], "prop-artist")
        self.assertEqual(aero["style"], "frutiger-aero-style")
        self.assertEqual(aero["builder"], "examples/aero_dashboard.py")
        self.assertIsNone(catalog_module.route("A Frutiger Aero car drives")["builder"])
        cosmic = catalog_module.route("An impossible aperture looms over a tiny witness")
        self.assertEqual((cosmic["subject"], cosmic["style"]),
                         ("environment-artist", "cosmic-eldritch-horror"))
        self.assertEqual(cosmic["builder"], "examples/cosmic_aperture.py")
        self.assertIsNone(catalog_module.route("An eldritch car drives")["builder"])
        hand = catalog_module.route("A hand unfolds a fused metal sixth digit")
        self.assertEqual((hand["subject"], hand["style"]),
                         ("character-artist", "body-horror-style"))
        self.assertEqual(hand["builder"], "examples/mutating_hand.py")
        self.assertIsNone(catalog_module.route("A mutating car drives")["builder"])
        analog = catalog_module.route("A training room security camera records an empty chair")
        self.assertEqual((analog["subject"], analog["style"]),
                         ("environment-artist", "analog-found-footage-horror"))
        self.assertEqual(analog["builder"], "examples/analog_training.py")
        self.assertIsNone(catalog_module.route("A VHS car drives")["builder"])
        liminal = catalog_module.route("An empty tiled pool hall repeats endlessly")
        self.assertEqual((liminal["subject"], liminal["style"]),
                         ("environment-artist", "liminal-space-style"))
        self.assertEqual(liminal["builder"], "examples/liminal_pool.py")
        self.assertIsNone(catalog_module.route("A liminal car drives")["builder"])
        folk = catalog_module.route("A sunlit village field surrounds a wicker effigy")
        self.assertEqual((folk["subject"], folk["style"]),
                         ("environment-artist", "folk-horror-style"))
        self.assertEqual(folk["builder"], "examples/folk_ritual.py")
        self.assertIsNone(catalog_module.route("A folk horror car drives")["builder"])
        puppet = catalog_module.route("A cheerful felt puppet on a children's show stage turns wrong")
        self.assertEqual((puppet["subject"], puppet["style"]),
                         ("character-artist", "mascot-puppet-horror"))
        self.assertEqual(puppet["builder"], "examples/puppet_stage.py")
        self.assertIsNone(catalog_module.route("A puppet horror car drives")["builder"])
        dream = catalog_module.route("An oversized alphabet block floats above an empty playground as a door opens")
        self.assertEqual((dream["subject"], dream["style"]),
                         ("environment-artist", "dream-weirdcore-style"))
        self.assertEqual(dream["builder"], "examples/dream_playground.py")
        self.assertIsNone(catalog_module.route("A dreamcore car drives")["builder"])
        indie = catalog_module.route("A first-person flashlight follows red markers to a forest cabin as its window goes dark")
        self.assertEqual((indie["subject"], indie["style"]),
                         ("environment-artist", "indie-horror-aesthetics"))
        self.assertEqual(indie["builder"], "examples/indie_cabin.py")
        self.assertIsNone(catalog_module.route("An indie horror car drives")["builder"])
        self.assertEqual(catalog_module.route("A person walks through a room")["subject"],
                         "character-artist")
        fantasy = catalog_module.route("A stone castle lowers its oak drawbridge over a moat")
        self.assertEqual((fantasy["subject"], fantasy["style"], fantasy["world"]),
                         ("environment-artist", "stylized-style", "fantasy-worlds"))
        self.assertEqual(fantasy["builder"], "examples/fantasy_gate.py")
        self.assertIsNone(catalog_module.route("A castle lowers a drawbridge",
                                                style="anime-style")["builder"])
        with self.assertRaisesRegex(ValueError, "Unknown Blender world"):
            catalog_module.route("A castle lowers a drawbridge", world="unknown-world")
        cyberpunk = catalog_module.route("A parcel drone crosses a cyberpunk alley")
        self.assertEqual((cyberpunk["subject"], cyberpunk["style"], cyberpunk["world"]),
                         ("environment-artist", "stylized-style", "sci-fi-punk-worlds"))
        self.assertEqual(cyberpunk["builder"], "examples/cyberpunk_alley.py")
        self.assertIsNone(catalog_module.route("A cyberpunk alley with a drone",
                                                style="voxel-style")["builder"])
        viking = catalog_module.route("A Viking longship crosses a rocky fjord")
        self.assertEqual((viking["subject"], viking["style"], viking["world"]),
                         ("vehicle-artist", "stylized-style", "historical-worlds"))
        self.assertEqual(viking["builder"], "examples/viking_longship.py")
        self.assertIsNone(catalog_module.route("A Viking longship crosses a fjord",
                                                style="anime-style")["builder"])
        wasteland = catalog_module.route(
            "A scavenger cart crosses a post-apocalyptic wasteland fuel station")
        self.assertEqual((wasteland["subject"], wasteland["style"], wasteland["world"]),
                         ("environment-artist", "stylized-style", "apocalypse-worlds"))
        self.assertEqual(wasteland["builder"], "examples/wasteland_station.py")
        self.assertIsNone(catalog_module.route("A post-apocalyptic wasteland fuel station",
                                                style="anime-style")["builder"])
        kelp = catalog_module.route("An underwater kelp forest with fish and rising bubbles")
        self.assertEqual((kelp["subject"], kelp["style"], kelp["world"]),
                         ("environment-artist", "stylized-style", "biome-worlds"))
        self.assertEqual(kelp["builder"], "examples/kelp_forest.py")
        self.assertIsNone(catalog_module.route("An underwater kelp forest",
                                                style="voxel-style")["builder"])
        cozy = catalog_module.route("A cozy reading nook with a rocking chair")
        self.assertEqual((cozy["subject"], cozy["style"], cozy["world"]),
                         ("environment-artist", "stylized-style", "cozy-wholesome-mood"))
        self.assertEqual(cozy["builder"], "examples/cozy_nook.py")
        self.assertIsNone(catalog_module.route("A cozy reading nook",
                                                style="anime-style")["builder"])
        gritty = catalog_module.route("A dark gritty freight depot with a moving crane")
        self.assertEqual((gritty["subject"], gritty["style"], gritty["world"]),
                         ("environment-artist", "stylized-style", "dark-gritty-mood"))
        self.assertEqual(gritty["builder"], "examples/gritty_depot.py")
        self.assertIsNone(catalog_module.route("A dark gritty freight depot",
                                                style="voxel-style")["builder"])
        dream = catalog_module.route("A dreamlike floating doorway over a mirror sea")
        self.assertEqual((dream["subject"], dream["style"], dream["world"]),
                         ("environment-artist", "stylized-style", "dream-surreal-mood"))
        self.assertEqual(dream["builder"], "examples/dream_tide.py")
        self.assertIsNone(catalog_module.route("A surreal floating doorway",
                                                style="anime-style")["builder"])
        retrowave = catalog_module.route("A synthwave grid highway with a chrome car")
        self.assertEqual((retrowave["subject"], retrowave["style"], retrowave["world"]),
                         ("vehicle-artist", "stylized-style", "neon-retrofuturism"))
        self.assertEqual(retrowave["builder"], "examples/retrowave_highway.py")
        self.assertEqual(catalog_module.route("An outrun grid highway")["subject"],
                         "environment-artist")
        self.assertIsNone(catalog_module.route("A synthwave grid highway with a car",
                                                style="anime-style")["builder"])
        brutalist = catalog_module.route("A brutalist concrete archive gateway")
        self.assertEqual((brutalist["subject"], brutalist["style"], brutalist["world"]),
                         ("environment-artist", "stylized-style", "brutalist-mood"))
        self.assertEqual(brutalist["builder"], "examples/brutalist_archive.py")
        self.assertIsNone(catalog_module.route("A monumental concrete archive",
                                                style="anime-style")["builder"])
        combat = catalog_module.route("A sword duel in a combat arena")
        self.assertEqual((combat["subject"], combat["style"], combat["genre"]),
                         ("environment-artist", "stylized-style", "genre-action-combat"))
        self.assertEqual(combat["builder"], "examples/action_arena.py")
        self.assertIsNone(catalog_module.route("A combat arena with swords",
                                                style="anime-style")["builder"])
        with self.assertRaisesRegex(ValueError, "Unknown Blender genre"):
            catalog_module.route("An arena", genre="unlisted-genre")
        shooter = catalog_module.route("An FPS shooter rooftop cover lane")
        self.assertEqual((shooter["subject"], shooter["style"], shooter["genre"]),
                         ("environment-artist", "stylized-style", "genre-shooter"))
        self.assertEqual(shooter["builder"], "examples/shooter_rooftop.py")
        self.assertIsNone(catalog_module.route("An FPS shooter rooftop cover lane",
                                                style="anime-style")["builder"])
        rpg = catalog_module.route("An RPG quest hub with loot rarity")
        self.assertEqual((rpg["subject"], rpg["style"], rpg["genre"]),
                         ("environment-artist", "stylized-style", "genre-rpg"))
        self.assertEqual(rpg["builder"], "examples/rpg_quest_hub.py")
        self.assertIsNone(catalog_module.route("An RPG quest hub",
                                                style="anime-style")["builder"])
        self.assertIsNone(catalog_module.route("An RPG character portrait")["builder"])
        survival = catalog_module.route("A survival shelter with a crafting bench")
        self.assertEqual((survival["subject"], survival["style"], survival["genre"]),
                         ("environment-artist", "stylized-style", "genre-survival"))
        self.assertEqual(survival["builder"], "examples/survival_shelter.py")
        self.assertIsNone(catalog_module.route("A survival shelter with a crafting bench",
                                                style="anime-style")["builder"])
        stealth = catalog_module.route("A stealth infiltration route with a shadow patrol")
        self.assertEqual((stealth["subject"], stealth["style"], stealth["genre"]),
                         ("environment-artist", "stylized-style", "genre-stealth"))
        self.assertEqual(stealth["builder"], "examples/stealth_infiltration.py")
        self.assertIsNone(catalog_module.route("A stealth infiltration route",
                                                style="anime-style")["builder"])
        puzzle = catalog_module.route("A puzzle platformer with a pressure pad bridge")
        self.assertEqual((puzzle["subject"], puzzle["style"], puzzle["genre"]),
                         ("environment-artist", "stylized-style", "genre-puzzle-platformer"))
        self.assertEqual(puzzle["builder"], "examples/puzzle_platformer.py")
        self.assertIsNone(catalog_module.route("A puzzle platformer with a pressure pad bridge",
                                                style="anime-style")["builder"])
        modular = catalog_module.route("A metroidvania ability gate between room modules")
        self.assertEqual((modular["subject"], modular["style"], modular["genre"]),
                         ("environment-artist", "stylized-style",
                          "genre-metroidvania-roguelike"))
        self.assertEqual(modular["builder"], "examples/modular_gate.py")
        self.assertIsNone(catalog_module.route("A metroidvania ability gate",
                                                style="anime-style")["builder"])
        soulslike = catalog_module.route("A soulslike fog gate beside a bonfire causeway")
        self.assertEqual((soulslike["subject"], soulslike["style"], soulslike["genre"]),
                         ("environment-artist", "stylized-style", "genre-soulslike"))
        self.assertEqual(soulslike["builder"], "examples/soulslike_causeway.py")
        self.assertIsNone(catalog_module.route("A soulslike fog gate",
                                                style="anime-style")["builder"])
        strategy = catalog_module.route("An isometric colony sim with resource dispatch")
        self.assertEqual((strategy["subject"], strategy["style"], strategy["genre"]),
                         ("environment-artist", "isometric-style", "genre-strategy-sim"))
        self.assertEqual(strategy["builder"], "examples/strategy_settlement.py")
        self.assertIsNone(catalog_module.route("A strategy tile settlement",
                                                style="anime-style")["builder"])
        circuit = catalog_module.route("A circuit sprint with two team color cars")
        self.assertEqual((circuit["subject"], circuit["style"], circuit["genre"]),
                         ("vehicle-artist", "stylized-style", "genre-racing-sports"))
        self.assertEqual(circuit["builder"], "examples/circuit_sprint.py")
        self.assertIsNone(catalog_module.route("A circuit sprint",
                                                style="anime-style")["builder"])
        narrative = catalog_module.route("A visual novel station letter choice")
        self.assertEqual((narrative["subject"], narrative["style"], narrative["genre"]),
                         ("environment-artist", "stylized-style", "genre-narrative-vn"))
        self.assertEqual(narrative["builder"], "examples/station_letter.py")
        self.assertIsNone(catalog_module.route("A visual novel station letter",
                                                style="anime-style")["builder"])
        card = catalog_module.route("A deck builder card table choice")
        self.assertEqual((card["subject"], card["style"], card["genre"]),
                         ("prop-artist", "stylized-style", "genre-card-party-idle"))
        self.assertEqual(card["builder"], "examples/card_table.py")
        self.assertIsNone(catalog_module.route("A deck builder card table choice",
                                                style="anime-style")["builder"])
        crossing = catalog_module.route("An open world biome crossing")
        self.assertEqual((crossing["subject"], crossing["style"], crossing["genre"]),
                         ("environment-artist", "stylized-style",
                          "genre-open-world-sandbox"))
        self.assertEqual(crossing["builder"], "examples/open_world_crossing.py")
        self.assertIsNone(catalog_module.route("An open world biome crossing",
                                                style="anime-style")["builder"])
        era = catalog_module.route("A PS1 PS5 spaceship comparison")
        self.assertEqual((era["subject"], era["style"], era["era"]),
                         ("vehicle-artist", "stylized-style", "visual-console-eras"))
        self.assertEqual(era["builder"], "examples/console_era_flight.py")
        self.assertIsNone(catalog_module.route("A PS1 PS5 spaceship comparison",
                                                style="anime-style")["builder"])
        with self.assertRaisesRegex(ValueError, "Unknown Blender era"):
            catalog_module.route("A spaceship", era="unknown-era")
        for prompt, skill in (("A polished brushed ceramic material study", "materials"),
                              ("A material lookdev swatch lab", "lookdev"),
                              ("A three point light sweep", "lighting")):
            result = catalog_module.route(prompt)
            self.assertEqual((result["subject"], result["style"],
                              result["capability"]),
                             ("blender-modeler", "realistic-style", skill))
            self.assertEqual(result["builder"], "examples/material_light_lab.py")
            self.assertIsNone(catalog_module.route(prompt,
                                                    style="anime-style")["builder"])
        with self.assertRaisesRegex(ValueError, "Unknown Blender capability"):
            catalog_module.route("A swatch", capability="unknown-craft")
        for prompt, skill in (("An emotional camera push", "camera-cinematography"),
                              ("A headless Eevee narrative render", "rendering"),
                              ("A sealed letter keyframe rise", "animation")):
            result = catalog_module.route(prompt)
            self.assertEqual((result["subject"], result["style"],
                              result["capability"]),
                             ("environment-artist", "stylized-style", skill))
            self.assertEqual(result["builder"], "examples/station_letter.py")
            self.assertIsNone(catalog_module.route(prompt,
                                                    style="anime-style")["builder"])
        for prompt, skill in (("A geometry nodes post kit", "geometry-nodes"),
                              ("A parametric post walkway", "procedural-modeling"),
                              ("A modular walkway assembly", "scene-assembly")):
            result = catalog_module.route(prompt)
            self.assertEqual((result["subject"], result["style"],
                              result["capability"]),
                             ("environment-artist", "stylized-style", skill))
            self.assertEqual(result["builder"], "examples/geometry_node_walkway.py")
            self.assertIsNone(catalog_module.route(prompt,
                                                    style="anime-style")["builder"])

    def test_explicit_style_wins_and_unsupported_combination_has_no_builder(self):
        result = catalog_module.route("A character waves", "stop-motion-craft-style")
        self.assertEqual(result["style"], "stop-motion-craft-style")
        self.assertIsNone(result["render_method"])
        overridden = catalog_module.route("A realistic mechanical clamp", "anime-style")
        self.assertEqual(overridden["style"], "anime-style")
        self.assertIsNone(overridden["render_method"])
        with self.assertRaisesRegex(ValueError, "Unknown Blender style"):
            catalog_module.route("A character waves", "unbuilt-style")

    def test_false_rendered_claim_and_broken_dependency_are_rejected(self):
        original = catalog_module.MANIFEST
        try:
            candidate = copy.deepcopy(original)
            candidate["entries"][0]["status"] = "Rendered"
            catalog_module.MANIFEST = candidate
            with self.assertRaisesRegex(ValueError, "lacks a supported method"):
                catalog_module.catalog()
            candidate["entries"][0]["status"] = "Catalogued"
            candidate["entries"][0]["dependencies"] = ["missing-skill"]
            with self.assertRaisesRegex(ValueError, "Invalid dependencies"):
                catalog_module.catalog()
            candidate["entries"][0]["dependencies"] = ["blender-modeler"]
            candidate["entries"][1]["dependencies"] = ["blender-director"]
            with self.assertRaisesRegex(ValueError, "Dependency cycle"):
                catalog_module.catalog()
        finally:
            catalog_module.MANIFEST = original

    def test_explicit_subject_uses_catalog_id(self):
        result = catalog_module.route("A realistic clamp", subject="hard-surface")
        self.assertEqual(result["subject"], "hard-surface")
        with self.assertRaisesRegex(ValueError, "Unknown Blender subject"):
            catalog_module.route("A clamp", subject="unlisted-subject")

    def test_gallery_requires_scores_for_every_candidate_and_selects_best(self):
        book = json.loads((catalog_module.BLENDER / "scores.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog_module.scorebook(book)), 63)
        fantasy = book["routes"]["fantasy-worlds"]
        self.assertEqual(fantasy["selected"], "fantasy-gate-v2")
        self.assertEqual([candidate["score_total"] for candidate in fantasy["candidates"]],
                         [68, 78])
        cyberpunk = book["routes"]["sci-fi-punk-worlds"]
        self.assertEqual(cyberpunk["selected"], "cyberpunk-alley-v2")
        self.assertEqual([candidate["score_total"] for candidate in cyberpunk["candidates"]],
                         [64, 74])
        viking = book["routes"]["historical-worlds"]
        self.assertEqual(viking["selected"], "viking-longship-v2")
        self.assertEqual([candidate["score_total"] for candidate in viking["candidates"]],
                         [64, 73])
        wasteland = book["routes"]["apocalypse-worlds"]
        self.assertEqual(wasteland["selected"], "wasteland-station-v2")
        self.assertEqual([candidate["score_total"] for candidate in wasteland["candidates"]],
                         [68, 78])
        kelp = book["routes"]["biome-worlds"]
        self.assertEqual(kelp["selected"], "kelp-forest-v2")
        self.assertEqual([candidate["score_total"] for candidate in kelp["candidates"]],
                         [68, 78])
        cozy = book["routes"]["cozy-wholesome-mood"]
        self.assertEqual(cozy["selected"], "cozy-nook-v2")
        self.assertEqual([candidate["score_total"] for candidate in cozy["candidates"]],
                         [68, 78])
        gritty = book["routes"]["dark-gritty-mood"]
        self.assertEqual(gritty["selected"], "gritty-depot-v2")
        self.assertEqual([candidate["score_total"] for candidate in gritty["candidates"]],
                         [63, 78])
        dream = book["routes"]["dream-surreal-mood"]
        self.assertEqual(dream["selected"], "dream-tide-v2")
        self.assertEqual([candidate["score_total"] for candidate in dream["candidates"]],
                         [63, 78])
        retrowave = book["routes"]["neon-retrofuturism"]
        self.assertEqual(retrowave["selected"], "retrowave-highway-v2")
        self.assertEqual([candidate["score_total"] for candidate in retrowave["candidates"]],
                         [67, 82])
        brutalist = book["routes"]["brutalist-mood"]
        self.assertEqual(brutalist["selected"], "brutalist-archive-v2")
        self.assertEqual([candidate["score_total"] for candidate in brutalist["candidates"]],
                         [63, 78])
        combat = book["routes"]["genre-action-combat"]
        self.assertEqual(combat["selected"], "action-arena-v2")
        self.assertEqual([candidate["score_total"] for candidate in combat["candidates"]],
                         [63, 78])
        shooter = book["routes"]["genre-shooter"]
        self.assertEqual(shooter["selected"], "shooter-rooftop-v2")
        self.assertEqual([candidate["score_total"] for candidate in shooter["candidates"]],
                         [63, 78])
        rpg = book["routes"]["genre-rpg"]
        self.assertEqual(rpg["selected"], "rpg-quest-hub-v2")
        self.assertEqual([candidate["score_total"] for candidate in rpg["candidates"]],
                         [63, 78])
        survival = book["routes"]["genre-survival"]
        self.assertEqual(survival["selected"], "survival-shelter-v2")
        self.assertEqual([candidate["score_total"] for candidate in survival["candidates"]],
                         [63, 78])
        stealth = book["routes"]["genre-stealth"]
        self.assertEqual(stealth["selected"], "stealth-infiltration-v2")
        self.assertEqual([candidate["score_total"] for candidate in stealth["candidates"]],
                         [63, 78])
        puzzle = book["routes"]["genre-puzzle-platformer"]
        self.assertEqual(puzzle["selected"], "puzzle-platformer-v2")
        self.assertEqual([candidate["score_total"] for candidate in puzzle["candidates"]],
                         [63, 78])
        modular = book["routes"]["genre-metroidvania-roguelike"]
        self.assertEqual(modular["selected"], "modular-gate-v2")
        self.assertEqual([candidate["score_total"] for candidate in modular["candidates"]],
                         [59, 74])
        soulslike = book["routes"]["genre-soulslike"]
        self.assertEqual(soulslike["selected"], "soulslike-causeway-v2")
        self.assertEqual([candidate["score_total"] for candidate in soulslike["candidates"]],
                         [58, 78])
        strategy = book["routes"]["genre-strategy-sim"]
        self.assertEqual(strategy["selected"], "strategy-settlement-v2")
        self.assertEqual([candidate["score_total"] for candidate in strategy["candidates"]],
                         [58, 73])
        circuit = book["routes"]["genre-racing-sports"]
        self.assertEqual(circuit["selected"], "circuit-sprint-v2")
        self.assertEqual([candidate["score_total"] for candidate in circuit["candidates"]],
                         [58, 73])
        narrative = book["routes"]["genre-narrative-vn"]
        self.assertEqual(narrative["selected"], "station-letter-v3")
        self.assertEqual([candidate["score_total"] for candidate in narrative["candidates"]],
                         [58, 68, 73])
        card = book["routes"]["genre-card-party-idle"]
        self.assertEqual(card["selected"], "card-table-v2")
        self.assertEqual([candidate["score_total"] for candidate in card["candidates"]],
                         [58, 78])
        crossing = book["routes"]["genre-open-world-sandbox"]
        self.assertEqual(crossing["selected"], "open-world-crossing-v2")
        self.assertEqual([candidate["score_total"] for candidate in crossing["candidates"]],
                         [58, 78])
        era = book["routes"]["visual-console-eras"]
        self.assertEqual(era["selected"], "console-era-flight-v2")
        self.assertEqual([candidate["score_total"] for candidate in era["candidates"]],
                         [62, 77])
        material = book["routes"]["material-light-lab"]
        self.assertEqual(material["selected"], "material-light-v2")
        self.assertEqual([candidate["score_total"] for candidate in material["candidates"]],
                         [58, 77])
        geometry = book["routes"]["geometry-node-walkway"]
        self.assertEqual(geometry["selected"], "geometry-node-walkway-v2")
        self.assertEqual([candidate["score_total"] for candidate in geometry["candidates"]],
                         [58, 73])
        handoff = book["routes"]["video-handoff"]
        self.assertEqual(len(handoff["candidates"]), 2)
        self.assertEqual(handoff["selected"], "clamp-handoff-full-resolution")
        pixel = book["routes"]["pixel-art-style"]
        self.assertEqual(len(pixel["candidates"]), 3)
        self.assertEqual(pixel["selected"], "pixel-chest-v2-coarse")
        self.assertEqual([candidate["technical_pass"] for candidate in pixel["candidates"]],
                         [False, False, True])
        painted = book["routes"]["hand-painted-style"]
        self.assertEqual(len(painted["candidates"]), 2)
        self.assertEqual(painted["selected"], "painted-teacup-v2")
        self.assertEqual([candidate["score_total"] for candidate in painted["candidates"]],
                         [78, 82])
        watercolor = book["routes"]["painterly-style"]
        self.assertEqual(len(watercolor["candidates"]), 3)
        self.assertEqual(watercolor["selected"], "watercolor-river-v3")
        self.assertEqual([candidate["score_total"] for candidate in watercolor["candidates"]],
                         [74, 78, 82])
        paper = book["routes"]["stop-motion-craft-style"]
        self.assertEqual(len(paper["candidates"]), 2)
        self.assertEqual(paper["selected"], "paper-butterfly-v2")
        self.assertEqual([candidate["score_total"] for candidate in paper["candidates"]],
                         [74, 82])
        chibi = book["routes"]["chibi-style"]
        self.assertEqual(len(chibi["candidates"]), 2)
        self.assertEqual(chibi["selected"], "chibi-courier-v2")
        self.assertEqual([candidate["score_total"] for candidate in chibi["candidates"]],
                         [70, 78])
        noir = book["routes"]["noir-style"]
        self.assertEqual(len(noir["candidates"]), 2)
        self.assertEqual(noir["selected"], "noir-detective-v2")
        self.assertEqual([candidate["score_total"] for candidate in noir["candidates"]],
                         [69, 77])
        minimal = book["routes"]["minimalist-style"]
        self.assertEqual(len(minimal["candidates"]), 2)
        self.assertEqual(minimal["selected"], "minimal-pendulum-v2")
        self.assertEqual([candidate["score_total"] for candidate in minimal["candidates"]],
                         [74, 82])
        vector = book["routes"]["vector-style"]
        self.assertEqual(vector["selected"], "vector-sprout-v3")
        self.assertEqual([candidate["score_total"] for candidate in vector["candidates"]],
                         [74, 78, 82])
        retro = book["routes"]["retro-8bit-style"]
        self.assertEqual(retro["selected"], "retro8-ship-v2")
        self.assertEqual([candidate["score_total"] for candidate in retro["candidates"]],
                         [51, 60, 73, 78, 73, 82])
        self.assertEqual([candidate["technical_pass"] for candidate in retro["candidates"]],
                         [False, False, False, False, True, True])
        retro16 = book["routes"]["retro-16bit-style"]
        self.assertEqual(retro16["selected"], "retro16-fox-v2")
        self.assertEqual([candidate["score_total"] for candidate in retro16["candidates"]],
                         [73, 82])
        hd2d = book["routes"]["hd-2d-style"]
        self.assertEqual(hd2d["selected"], "hd2d-bridge-v3")
        self.assertEqual([candidate["score_total"] for candidate in hd2d["candidates"]],
                         [73, 78, 82])
        aero = book["routes"]["frutiger-aero-style"]
        self.assertEqual(aero["selected"], "aero-dashboard-v2")
        self.assertEqual([candidate["score_total"] for candidate in aero["candidates"]],
                         [73, 82])
        cosmic = book["routes"]["cosmic-eldritch-horror"]
        self.assertEqual(cosmic["selected"], "cosmic-aperture-v3")
        self.assertEqual([candidate["score_total"] for candidate in cosmic["candidates"]],
                         [63, 73, 78])
        hand = book["routes"]["body-horror-style"]
        self.assertEqual(hand["selected"], "mutating-hand-v3-diffusion")
        self.assertEqual([candidate["score_total"] for candidate in hand["candidates"]],
                         [64, 73, 74, 78])
        analog = book["routes"]["analog-found-footage-horror"]
        self.assertEqual(analog["selected"], "analog-training-v3")
        self.assertEqual([candidate["score_total"] for candidate in analog["candidates"]],
                         [73, 78, 82])
        liminal = book["routes"]["liminal-space-style"]
        self.assertEqual(liminal["selected"], "liminal-pool-v2")
        self.assertEqual([candidate["score_total"] for candidate in liminal["candidates"]],
                         [68, 82])
        folk = book["routes"]["folk-horror-style"]
        self.assertEqual(folk["selected"], "folk-ritual-v2")
        self.assertEqual([candidate["score_total"] for candidate in folk["candidates"]],
                         [68, 78])
        puppet = book["routes"]["mascot-puppet-horror"]
        self.assertEqual(puppet["selected"], "puppet-stage-v2")
        self.assertEqual([candidate["score_total"] for candidate in puppet["candidates"]],
                         [72, 82])
        dream = book["routes"]["dream-weirdcore-style"]
        self.assertEqual(dream["selected"], "dream-playground-v2")
        self.assertEqual([candidate["score_total"] for candidate in dream["candidates"]],
                         [68, 78])
        indie = book["routes"]["indie-horror-aesthetics"]
        self.assertEqual(indie["selected"], "indie-cabin-v2")
        self.assertEqual([candidate["score_total"] for candidate in indie["candidates"]],
                         [68, 78])
        unscored = copy.deepcopy(book)
        unscored["routes"]["hard-surface"]["candidates"][0]["scores"].pop("finish")
        with self.assertRaisesRegex(ValueError, "five 0–5 scores"):
            catalog_module.scorebook(unscored)
        worse_winner = copy.deepcopy(book)
        competitor = copy.deepcopy(worse_winner["routes"]["hard-surface"]["candidates"][0])
        competitor["id"] = "clamp-better"
        competitor["scores"] = {name: 5 for name in catalog_module.SCORE_FIELDS}
        competitor["score_total"] = 100
        worse_winner["routes"]["hard-surface"]["candidates"].append(competitor)
        with self.assertRaisesRegex(ValueError, "not the best passing result"):
            catalog_module.scorebook(worse_winner)

    def test_readme_catalog_and_rendered_gallery_stay_in_sync(self):
        readme = (catalog_module.REPO / "README.md").read_text(encoding="utf-8")
        generated = readme.split("<!-- blender-catalog:start -->", 1)[1].split(
            "<!-- blender-catalog:end -->", 1)[0].strip()
        self.assertEqual(generated, catalog_module.markdown_table(catalog_module.catalog()))
        gallery = readme.split("<!-- blender-catalog:start -->", 1)[0]
        # Every selected rendered artifact must play inline in the showcase table.
        for evidence in {entry["evidence"] for entry in catalog_module.catalog()
                         if entry["status"] == "Rendered"}:
            path = "content-studio/skills/content-studio-video/animation/blender/" + evidence
            self.assertRegex(gallery, r"!\[[^]]+\]\(" + re.escape(path) + r"\)")
        for name in ("clamp", "character", "corridor", "lamp", "handoff",
                     "lowpoly-lamp", "voxel-lamp", "isometric-lamp", "realistic-lamp",
                     "horror-corridor", "psx-horror", "anime-heroine", "stylized-windmill",
                     "cartoon-bounce", "comic-rocket", "manga-gaze", "pixel-chest",
                     "painted-teacup", "watercolor-river", "paper-butterfly",
                     "chibi-courier", "noir-detective", "minimal-pendulum",
                     "vector-sprout", "retro8-ship", "retro16-fox", "hd2d-bridge",
                     "aero-dashboard", "cosmic-aperture", "mutating-hand",
                     "analog-training", "liminal-pool", "folk-ritual", "puppet-stage",
                     "dream-playground", "indie-cabin", "fantasy-gate",
                     "cyberpunk-alley", "viking-longship", "wasteland-station",
                     "kelp-forest"):
            path = catalog_module.BLENDER / "previews" / f"{name}.gif"
            self.assertTrue(path.is_file(), path)
            self.assertIn(f"animation/blender/previews/{name}.gif", readme)
        self.assertIn("![Best scored vector sprout animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/vector-sprout.gif)", readme)
        self.assertIn("![Best scored retro 8-bit ship animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/retro8-ship.gif)", readme)
        self.assertIn("![Best scored retro 16-bit fox animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/retro16-fox.gif)", readme)
        self.assertIn("![Best scored HD-2D lantern bridge animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/hd2d-bridge.gif)", readme)
        self.assertIn("![Best scored Frutiger Aero dashboard animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/aero-dashboard.gif)", readme)
        self.assertIn("![Best scored cosmic eldritch aperture animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/cosmic-aperture.gif)", readme)
        self.assertIn("![Best scored body horror mutating hand animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/mutating-hand.gif)", readme)
        self.assertIn("![Best scored analog found footage training animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/analog-training.gif)", readme)
        self.assertIn("![Best scored liminal poolrooms animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/liminal-pool.gif)", readme)
        self.assertIn("![Best scored folk horror rite animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/folk-ritual.gif)", readme)
        self.assertIn("![Best scored mascot puppet horror animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/puppet-stage.gif)", readme)
        self.assertIn("![Best scored dream weirdcore playground animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/dream-playground.gif)", readme)
        self.assertIn("![Best scored indie forest cabin horror animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/indie-cabin.gif)", readme)
        self.assertIn("![Best scored fantasy drawbridge animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/fantasy-gate.gif)", readme)
        self.assertIn("![Best scored cyberpunk alley animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/cyberpunk-alley.gif)", readme)
        self.assertIn("![Best scored Viking longship animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/viking-longship.gif)", readme)
        self.assertIn("![Best scored post-apocalyptic wasteland animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/wasteland-station.gif)", readme)
        self.assertIn("![Best scored underwater kelp biome animation](content-studio/skills/"
                      "content-studio-video/animation/blender/previews/kelp-forest.gif)", readme)

    def test_visual_style_gifs_must_be_distinct(self):
        original = catalog_module.MANIFEST
        candidate = copy.deepcopy(original)
        anime = next(entry for entry in candidate["entries"] if entry["id"] == "anime-style")
        anime.update({"status": "Rendered", "method": "blender-shot",
                      "evidence": "previews/lowpoly-lamp.gif", "review": "lowpoly-review.md",
                      "builder": "examples/lowpoly_lamp.py", "spec": "examples/lowpoly_lamp.json",
                      "score_record": "scores.json"})
        winners = catalog_module.scorebook()
        winners["anime-style"] = winners["lowpoly-style"]
        try:
            catalog_module.MANIFEST = candidate
            with patch.object(catalog_module, "scorebook", return_value=winners):
                with self.assertRaisesRegex(ValueError, "distinct GIFs"):
                    catalog_module.catalog()
        finally:
            catalog_module.MANIFEST = original


if __name__ == "__main__":
    unittest.main()
