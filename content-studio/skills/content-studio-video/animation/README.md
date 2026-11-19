# Animation

Code-driven video uses [videogen](videogen/SKILL.md); original Blender shots use the shared [headless route](references/blender-art.md). The [rendered gallery scenes](blender/README.md) are authored examples. The [upstream Blender Skills snapshot](https://github.com/arjun988/blender-skills/tree/904f095d8f36a6e72adaebb08d07f884a074743d) informs the catalog and craft instructions, but does not supply executable Blender methods.

`Supported` here means a callable method exists for its specified input; it does not make every catalogued skill an automatic renderer. `Specialist only` means the result is reviewed as a separate asset before composition.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `blender-catalog` | Supported | Maintained 94-ID capability manifest → classified catalog | No | [Catalog tests](blender/tests/test_catalog.py) | Rendered status requires local proof; most entries are still guidance. |
| `blender-plan` | Supported | Visual request and optional style → suggested subject, style, and narrowly matching gallery builder | No | [Routing tests](blender/tests/test_catalog.py) | Requires creative review; unsupported combinations have no builder. |
| `blender-shot` | Supported | Trusted `make_scene` builder and JSON spec → editable `.blend`, MP4, hash report; optional resumable frame cache | Specialist only | [Three opening examples](blender/review.md) · [Desk lamp craft audit](blender/lamp-review.md) · [Low-poly treatment](blender/lowpoly-review.md) · [Voxel treatment](blender/voxel-review.md) · [Isometric treatment](blender/isometric-review.md) · [Realistic product treatment](blender/realistic-review.md) · [Psychological horror treatment](blender/horror-review.md) · [PSX horror treatment](blender/psx-horror-review.md) · [Anime heroine treatment](blender/anime-review.md) · [Stylized windmill treatment](blender/stylized-review.md) · [Cartoon mascot treatment](blender/cartoon-review.md) · [Comic rocket treatment](blender/comic-review.md) · [Manga close-up treatment](blender/manga-review.md) · [Pixel art chest treatment](blender/pixel-review.md) · [Painted teacup treatment](blender/painted-review.md) · [Watercolor river treatment](blender/watercolor-review.md) · [Paper craft butterfly treatment](blender/paper-review.md) · [Version 2 contract](blender/shot-contract.md) · [Resume comparison](blender/resume-review.md) | Blender 5.3 tested; project owns geometry and animation. |
| `blender-handoff` | Supported | Reviewed Blender report and MP4, narration WAV, cue → hashed videogen project and Remotion source | No | [Scored composed render](blender/handoff-review.md) · [Handoff tests](blender/tests/test_handoff.py) | Code-driven video path only; production drafts need approved precheck. |

The [`chibi-style` courier](blender/chibi-review.md) is another scored `blender-shot` treatment with a distinct full-body proportion and motion audit.
The [`noir-style` detective](blender/noir-review.md) adds scored hard-light, silhouette, and wet-street evidence.
The [`minimalist-style` pendulum](blender/minimal-review.md) adds a scored three-color, negative-space, and swing audit.
The [`vector-style` sprout](blender/vector-review.md) adds a scored flat-fill, staged-growth, and polygon-path audit.
The [`retro-8bit-style` ship](blender/retro8-review.md) adds a scored four-color sprite, held-motion, and impact audit.
The [`retro-16bit-style` fox](blender/retro16-review.md) adds a scored packed-dither landscape, held walk, and waterfall audit.
The [`hd-2d-style` lantern bridge](blender/hd2d-review.md) adds a scored pixel actor, painted 3D stage, and depth-of-field audit.
The [`frutiger-aero-style` dashboard](blender/aero-review.md) adds a scored glossy aqua UI, floating bubble, and leaf-opening audit.
The [`cosmic-eldritch-horror` aperture](blender/cosmic-review.md) adds a scored vast-void scene, tiny witness, and shifting-geometry audit.
The [`body-horror-style` hand](blender/hand-review.md) adds a scored six-digit mutation, skin-to-metal fusion, and articulated-finger audit.
The [`analog-found-footage-horror` tape](blender/analog-review.md) adds a scored security-room recording, tracking-line, monitor-signal, and implied-figure audit.
The [`liminal-space-style` poolrooms](blender/liminal-review.md) add a scored empty modular hall, fluorescent flicker, and long inspection-push audit.
The [`folk-horror-style` rite](blender/folk-review.md) adds a scored sunlit village, handmade wicker symbol, repeated offerings, and camera and ribbon motion audit.
The [`mascot-puppet-horror` show](blender/puppet-review.md) adds a scored felt character, children's set, plastic gaze, fixed smile, and sick-light performance audit.
The [`dream-weirdcore-style` playground](blender/dream-review.md) adds a scored pastel play space, oversized alphabet block, empty chair, and impossible opening audit.
The [`indie-horror-aesthetics` cabin](blender/indie-review.md) adds a scored first-person forest lane with red trail markers, a practical window blackout, and exact frame review.
The [`fantasy-worlds` gate](blender/fantasy-review.md) adds a scored medieval low-magic castle lane, a lowering drawbridge, heraldry, and a structural fit audit. World direction is selected separately from visual style.
The [`sci-fi-punk-worlds` alley](blender/cyberpunk-review.md) adds a scored cyberpunk lane with neon tower facades and a traversing parcel drone.
The [`historical-worlds` longship](blender/viking-review.md) adds a scored Viking period lane with a wool sail, shields, and camera-follow crossing.
The [`apocalypse-worlds` outpost](blender/wasteland-review.md) adds a scored roadside collapse lane with improvised repairs, a salvaged hauler, and a dust sweep.
The [`biome-worlds` kelp forest](blender/kelp-review.md) adds a scored underwater lane with swaying plants, fish, bubbles, and a camera glide.
The [`cozy-wholesome-mood` nook](blender/cozy-review.md) adds a scored reading-room lane with rounded furniture, gentle chair rocking, and a warming practical lamp.
The [`dark-gritty-mood` depot](blender/gritty-review.md) adds a scored industrial lane with oxidized structure, patched metal, low-key light, and a crossing crane load.
The [`dream-surreal-mood` tide](blender/dream-tide-review.md) adds a scored pastel threshold lane with unsupported stairs, an oversized key, a tiny boat, and an opening door.
The [`neon-retrofuturism` highway](blender/retrowave-review.md) adds a scored outrun lane with a perspective grid, striped sun, chrome coupe, and magenta light.
The [`brutalist-mood` archive](blender/brutalist-review.md) adds a scored monumental concrete gateway with a tiny witness and a sliding shutter reveal.
The [`genre-action-combat` arena](blender/action-review.md) adds a scored sword-and-shield clash with readable fight space and a breaking prop.
The [`genre-shooter` rooftop](blender/shooter-review.md) adds a scored first-person cover peek with a target, navigation landmark, and readable loot case.
The [`genre-rpg` hub](blender/rpg-review.md) adds a scored two-region quest scene with class-readable gear and an opening rarity chest.
The [`genre-survival` shelter](blender/survival-review.md) adds a scored safe and unsafe zone scene with resources, a returning cart, and a campfire reveal.
The [`genre-stealth` lane](blender/stealth-review.md) adds a scored concealment and patrol scene with noisy plates, a ladder, and an upper objective.
The [`genre-puzzle-platformer` puzzle](blender/puzzle-review.md) adds a scored jump, pressure pad, hazard, bridge, and goal sequence with measured gaps.
The [`genre-metroidvania-roguelike` run](blender/modular-run-review.md) adds scored modular rooms, a collected ability, an opening biome gate, and two modifier symbols.
The [`genre-soulslike` causeway](blender/soulslike-review.md) adds a scored ruined route with a bonfire landmark, opening pale gate, and revealed enemy silhouette.
The [`genre-strategy-sim` settlement](blender/strategy-review.md) adds a scored tile grid with distinct resource sites, dispatched workers, and a growing watchtower.
The [`genre-racing-sports` sprint](blender/circuit-review.md) adds scored team-color cars, clear track boundaries, a modular grandstand, and a verified finish order.
The [`genre-narrative-vn` station](blender/narrative-review.md) adds a scored quiet background plate, emotional camera push, and one letter interaction cue.
The [`genre-card-party-idle` table](blender/card-table-review.md) adds a scored three-icon card hand, selected-card lift, and growing idle reward stack.
The [`genre-open-world-sandbox` crossing](blender/open-world-review.md) adds a scored two-biome traversal with a bridge, tower landmark, and sparse discovery cues.
The [`visual-console-eras` comparison](blender/console-era-review.md) adds scored PS1-like and modern-console ship motion with distinct geometry, filtering, and material constraints.
The [material and lighting lab](blender/material-light-review.md) adds a clay-to-beauty review loop with three PBR masters and a moving three-point key.
The [narrative technical evidence](blender/narrative-technical-review.md) connects the scored station shot to bounded camera, animation, and headless-rendering routes.
The [Geometry Nodes walkway](blender/geometry-node-review.md) adds an audited parametric kit and organized set assembly with a scored traversal GIF.
The [reading-nook set-dressing evidence](blender/set-dressing-review.md) reuses a scored interior GIF for its prop-cluster and clutter audit.
The [vehicle and vegetation modeling evidence](blender/modeling-reuse-review.md) connects scored car and kelp shots to bounded asset craft routes.
The [detective archetype evidence](blender/archetype-review.md) connects one scored noir shot to an audited character role.
The [Blender QA evidence](blender/qa-review.md) records exact-output hash, mesh, budget, angle, and beauty checks with an explicit verdict.
The [measured studio archviz evidence](blender/archviz-review.md) compares a greybox and furnished walkthrough with audited dimensions and camera motion.
The [game asset pipeline evidence](blender/game-asset-review.md) scores two complete animations and checks UVs, textures, LODs, collision, and GLB/FBX round trips. Engine editor imports remain pending.
The [reed beetle evidence](blender/beetle-rig-review.md) scores a static and animated insectoid and checks its named FK hierarchy, rigid weights, wing reveal, and leg poses.
The [guardian craft evidence](blender/guardian-craft-review.md) scores a static blockout and a finished bust, then audits multires surface detail, a shrinkwrapped quad cage, and packed animated hair cards.
The [banner impact evidence](blender/banner-impact-review.md) scores a static baseline and simulated shot, then checks pinned cloth, rigid-body collision and baked playback, and a bounded mesh FX burst.
The [neon beauty compositor evidence](blender/cyberpunk-composite-review.md) scores raw and treated alley renders and audits a reversible Blender 5 exposure, saturation, and fog-glow graph.
