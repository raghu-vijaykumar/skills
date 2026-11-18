# Headless Blender gallery

The [video animation skill](../SKILL.md) indexes 94 upstream subject and style names for planning. `Catalogued` in the root README does not imply a tested renderer. The rendered gallery examples are original, explicitly authored Blender scenes. A project can replace their builders while retaining the same preview and full-shot contract.

| Showcase | Builder | Specification | Rendered GIF |
| --- | --- | --- | --- |
| Realistic clamp | [Source](examples/clamp.py) | [Inputs](examples/clamp.json) | [GIF](previews/clamp.gif) |
| Cel character | [Source](examples/character.py) | [Inputs](examples/character.json) | [GIF](previews/character.gif) |
| Atmospheric corridor | [Source](examples/corridor.py) | [Inputs](examples/corridor.json) | [GIF](previews/corridor.gif) |
| Measured desk lamp | [Source](examples/lamp.py) | [Inputs](examples/lamp.json) | [GIF](previews/lamp.gif) |
| Low-poly lamp treatment | [Source](examples/lowpoly_lamp.py) | [Inputs](examples/lowpoly_lamp.json) | [GIF](previews/lowpoly-lamp.gif) |
| Voxel lamp treatment | [Source](examples/voxel_lamp.py) | [Inputs](examples/voxel_lamp.json) | [GIF](previews/voxel-lamp.gif) |
| Isometric tile treatment | [Source](examples/isometric_lamp.py) | [Inputs](examples/isometric_lamp.json) | [GIF](previews/isometric-lamp.gif) |
| Realistic product visualization | [Source](examples/realistic_lamp.py) | [Inputs](examples/realistic_lamp.json) | [GIF](previews/realistic-lamp.gif) |
| Psychological horror corridor | [Source](examples/horror_corridor.py) | [Inputs](examples/horror_corridor.json) | [GIF](previews/horror-corridor.gif) |
| PSX horror CRT hall | [Source](examples/psx_horror.py) | [Inputs](examples/psx_horror.json) | [GIF](previews/psx-horror.gif) |
| Anime heroine pose | [Source](examples/anime_heroine.py) | [Inputs](examples/anime_heroine.json) | [GIF](previews/anime-heroine.gif) |
| Stylized windmill island | [Source](examples/stylized_windmill.py) | [Inputs](examples/stylized_windmill.json) | [GIF](previews/stylized-windmill.gif) |
| Cartoon bouncy mascot | [Source](examples/cartoon_bounce.py) | [Inputs](examples/cartoon_bounce.json) | [GIF](previews/cartoon-bounce.gif) |
| Comic rocket panel | [Source](examples/comic_rocket.py) | [Inputs](examples/comic_rocket.json) | [GIF](previews/comic-rocket.gif) |
| Manga eye close-up | [Source](examples/manga_gaze.py) | [Inputs](examples/manga_gaze.json) | [GIF](previews/manga-gaze.gif) |
| Pixel treasure chest | [Source](examples/pixel_chest.py) | [Inputs](examples/pixel_chest.json) | [GIF](previews/pixel-chest.gif) |
| Hand-painted wildflower teacup | [Source](examples/painted_teacup.py) | [Inputs](examples/painted_teacup.json) | [GIF](previews/painted-teacup.gif) |
| Painterly watercolor river | [Source](examples/watercolor_river.py) | [Inputs](examples/watercolor_river.json) | [GIF](previews/watercolor-river.gif) |
| Stop-motion paper butterfly | [Source](examples/paper_butterfly.py) | [Inputs](examples/paper_butterfly.json) | [GIF](previews/paper-butterfly.gif) |
| Chibi postal courier | [Source](examples/chibi_courier.py) | [Inputs](examples/chibi_courier.json) | [GIF](previews/chibi-courier.gif) |
| Noir rain detective | [Source](examples/noir_detective.py) | [Inputs](examples/noir_detective.json) | [GIF](previews/noir-detective.gif) |
| Minimalist kinetic pendulum | [Source](examples/minimal_pendulum.py) | [Inputs](examples/minimal_pendulum.json) | [GIF](previews/minimal-pendulum.gif) |
| Vector sprout and bloom | [Source](examples/vector_sprout.py) | [Inputs](examples/vector_sprout.json) | [GIF](previews/vector-sprout.gif) |
| Retro 8-bit arcade ship | [Source](examples/retro_8bit_ship.py) | [Inputs](examples/retro_8bit_ship.json) | [GIF](previews/retro8-ship.gif) |
| Retro 16-bit fox landscape | [Source](examples/retro_16bit_fox.py) | [Inputs](examples/retro_16bit_fox.json) | [GIF](previews/retro16-fox.gif) |
| HD-2D lantern bridge | [Source](examples/hd2d_bridge.py) | [Inputs](examples/hd2d_bridge.json) | [GIF](previews/hd2d-bridge.gif) |
| Frutiger Aero dashboard | [Source](examples/aero_dashboard.py) | [Inputs](examples/aero_dashboard.json) | [GIF](previews/aero-dashboard.gif) |
| Cosmic void aperture | [Source](examples/cosmic_aperture.py) | [Inputs](examples/cosmic_aperture.json) | [GIF](previews/cosmic-aperture.gif) |
| Mutating six-digit hand | [Source](examples/mutating_hand.py) | [Inputs](examples/mutating_hand.json) | [GIF](previews/mutating-hand.gif) |
| Analog training tape | [Source](examples/analog_training.py) | [Inputs](examples/analog_training.json) | [GIF](previews/analog-training.gif) |
| Empty liminal poolrooms | [Source](examples/liminal_pool.py) | [Inputs](examples/liminal_pool.json) | [GIF](previews/liminal-pool.gif) |
| Sunlit folk rite | [Source](examples/folk_ritual.py) | [Inputs](examples/folk_ritual.json) | [GIF](previews/folk-ritual.gif) |
| Uncanny puppet show | [Source](examples/puppet_stage.py) | [Inputs](examples/puppet_stage.json) | [GIF](previews/puppet-stage.gif) |

The [opening render review](review.md) records exact encoded assets, hashes, sampled frames, and limits for the first three GIFs. Each later treatment has its own linked review below.

New routes use the [version 2 shot contract](shot-contract.md) for object and beat IDs, rights, and exact render settings. The [desk lamp benchmark](lamp-review.md) adds a Blender structural audit for modeling and prop craft. The [low-poly variant](lowpoly-review.md) has a distinct recipe and polygon-budget audit. The [voxel variant](voxel-review.md) adds an occupancy-grid and stepped-motion audit. The [isometric variant](isometric-review.md) locks camera axes and tile footprint. The [realistic variant](realistic-review.md) checks real-world scale and PBR values while documenting its illustrative limits. The [horror variant](horror-review.md) checks narrow spatial proportions, one practical light, fog, and a sparse reveal. The [PSX horror variant](psx-horror-review.md) checks native low resolution, a tiny nearest atlas, and flat geometry. The [anime variant](anime-review.md) checks hard cel bands, contours, proportions, and independent pose controls. The [stylized variant](stylized-review.md) checks exaggerated shape language, a packed painted roof, matte materials, and readable windmill motion. The [cartoon variant](cartoon-review.md) checks squash/stretch, bold contours, and contact-shadow timing. The [comic variant](comic-review.md) checks packed halftone print, ink staging, and timed impact. The [manga variant](manga-review.md) checks a grayscale close-up, sparse screentone, and emphasis timing. The [pixel art variant](pixel-review.md) checks packed nearest texels, a fixed low-resolution camera, palette, and stepped treasure motion. The [hand-painted variant](painted-review.md) checks brush-authored albedo, a matte UV cup, backdrop wash, and readable steam. The [painterly variant](watercolor-review.md) checks a scene-wide pigment canvas, paper grain, washed sail, and boat motion. The [stop-motion craft variant](paper-review.md) checks packed paper fiber, physical layers and fasteners, a practical stage, and held wing poses. The original three gallery specs remain readable under the version 1 contract.

## Score and select output artifacts

The [chibi courier review](chibi-review.md) records the full-body ratio, two scored outputs, and the selected GIF.
The [noir detective review](noir-review.md) records the hard light, wet ground, walk audit, and two scored outputs.
The [minimalist pendulum review](minimal-review.md) records the reduced three-color form, negative space, and two scored outputs.
The [vector sprout review](vector-review.md) records three scored outputs, flat-fill geometry, and staged growth.
The [retro 8-bit ship review](retro8-review.md) records two full scored outputs, four rejected GIF encoding probes, a four-color winner, and grid-aligned impact motion.
The [retro 16-bit fox review](retro16-review.md) records two scored outputs, packed dither, a richer palette, held fox poses, and moving water glints.
The [HD-2D bridge review](hd2d-review.md) records three scored outputs, an isolated pixel-actor preview, a painted 3D stage, and depth of field.
The [Frutiger Aero review](aero-review.md) records two scored outputs, an isolated glossy bubble preview, aqua UI craft, and leaf-opening motion.
The [cosmic aperture review](cosmic-review.md) records three scored outputs, an isolated aperture preview, the scale mismatch, and its moving impossible geometry.
The [mutating hand review](hand-review.md) records three scored renders, four scored GIF artifacts, an isolated hand preview, and the corrected sixth-digit anatomy.
The [analog tape review](analog-review.md) records three scored outputs, the isolated safety monitor, scanline and tracking audit, and timed signal-loss reveal.
The [liminal pool review](liminal-review.md) records two scored outputs, an isolated modular bay, an empty repetition audit, and the slow camera push.
The [folk rite review](folk-review.md) records two scored outputs, an isolated wicker hero, a repeated-symbol and village audit, and the stronger camera and ribbon motion.
The [puppet show review](puppet-review.md) records two scored outputs, an isolated felt figure, hard-plastic eye and set audit, and the sick-light gaze performance.

Treat every full MP4 intended for this gallery as a candidate. Inspect its first, action, and held frames and its complete motion; verify frame count, dimensions, required objects, source hashes, and GIF decode. Record **every candidate**, including rejected ones, in [scores.json](scores.json) with its MP4/GIF hashes, technical result, five 0–5 editorial scores, reviewer, and reason. The weighted score covers subject fidelity (25%), motion readability (25%), composition (20%), finish (20%), and evidence integrity (10%). These are editorial review scores, not audience metrics or production approval.

Select the highest-scoring candidate that passes technical review and scores at least 70/100. Commit only that candidate's optimized GIF in `previews/`; retain rejected candidates' scores and hashes. `catalog.py` rejects a `Rendered` claim if its selected GIF is missing, changed, unscored, or outranked. From the repository root, run `python content-studio/skills/content-studio-video/animation/blender/scripts/catalog.py scores` to inspect the current winners before updating the README.

## Rebuild the showcases

The same rebuild commands also accept `chibi_courier`.
They also accept `noir_detective`.
They also accept `minimal_pendulum`.
They also accept `vector_sprout`.
They also accept `retro_8bit_ship`.
They also accept `retro_16bit_fox`.
They also accept `hd2d_bridge`.
They also accept `aero_dashboard`.
They also accept `cosmic_aperture`.
They also accept `mutating_hand`.
They also accept `analog_training`.
They also accept `liminal_pool`.

From the repository root, replace `<name>` with `clamp`, `character`, `corridor`, `lamp`, `lowpoly_lamp`, `voxel_lamp`, `isometric_lamp`, `realistic_lamp`, `horror_corridor`, `psx_horror`, `anime_heroine`, `stylized_windmill`, `cartoon_bounce`, `comic_rocket`, `manga_gaze`, `pixel_chest`, `painted_teacup`, `watercolor_river`, or `paper_butterfly` and use a new output directory for each preview. The commands read each spec's own review frames and resolution:

```powershell
$skill = 'content-studio/skills/content-studio-video/animation/blender'
$preview = 'content-studio/skills/content-studio-video/animation/engineering-3d/scripts/headless_preview.py'
$blender = (Get-Command blender -ErrorAction SilentlyContinue).Source
if (-not $blender) { $blender = 'C:\Program Files\Blender Foundation\Blender 5.3\blender.exe' }
$name = '<name>'
$spec = Get-Content "$skill/examples/$name.json" -Raw | ConvertFrom-Json
$reviewFrames = if ($spec.review_frames) { @($spec.review_frames) } else { @($spec.beats | ForEach-Object { $_.frame }) }
& $blender --background --factory-startup --python-exit-code 1 --python $preview -- --builder "$skill/examples/$name.py" --input "$skill/examples/$name.json" --dependency "$skill/examples/common.py" --out "tmp/$name-frames" --frame $reviewFrames[0] --frame $reviewFrames[1] --frame $reviewFrames[2] --size $spec.width $spec.height
& $blender --background --factory-startup --python-exit-code 1 --python "$skill/scripts/render_shot.py" -- --builder "$skill/examples/$name.py" --input "$skill/examples/$name.json" --dependency "$skill/examples/common.py" --out "tmp/$name.mp4"
ffmpeg -hide_banner -loglevel error -y -i "tmp/$name.mp4" -vf "fps=8,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3" -loop 0 "$skill/previews/$name.gif"
```

To rerun the voxel structural check after rendering its editable `.blend`:

```powershell
& $blender --background --factory-startup --python-exit-code 1 --python "$skill/scripts/audit_voxel.py" -- --blend tmp/voxel_lamp.blend --out tmp/voxel_lamp-audit.json
```

Use `scripts/audit_isometric.py` with the isometric `.blend` for its camera and tile check.
Use `scripts/audit_realistic.py` with the realistic `.blend` for its scale, fixture, and material check.
Use `scripts/audit_horror.py` with the horror `.blend` for its spatial, fog, and light-timing check.
Use `scripts/audit_psx.py` with the PSX `.blend` for its raster, atlas, geometry, fog, and CRT cue check. Replace the generic GIF command with `ffmpeg -hide_banner -loglevel error -y -i tmp/psx_horror.mp4 -vf "fps=8,scale=480:360:flags=neighbor,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=none" -loop 0 "$skill/previews/psx-horror.gif"` to retain blocky pixels.
Use `scripts/audit_anime.py` with the anime `.blend` for its cel bands, outline, eye proportions, blink, and separate pose controls.
Use `scripts/audit_stylized.py` with the windmill `.blend` for its exaggerated silhouettes, packed roof albedo, matte palette, and windmill/window motion.
Use `scripts/audit_cartoon.py` with the mascot `.blend` for its proportions, squash/stretch, jump height, and contact shadow.
Use `scripts/audit_comic.py` with the rocket `.blend` for its ink contour, packed halftone, panel frame, burst, lettering, and hero motion.
Use `scripts/audit_manga.py` with the eye `.blend` for its grayscale palette, packed screentone, cropped close-up, gaze shift, and emphasis cues.
Use `scripts/audit_pixel.py` with the chest `.blend` for its packed nearest 16×16 print, palette, locked orthographic raster, hinged lid, and stepped treasure reveal. For its GIF, downsample the 320×240 MP4 to 160×120 and scale to 480×360 with `neighbor`, then generate a 24-color palette without dithering as recorded in [pixel-review.md](pixel-review.md).
Use `scripts/audit_painted.py` with the teacup `.blend` for its 48-segment UV surface, packed 256×256 flower albedo, matte finish, fixed camera, cup turn, and three rim-anchored steam curls. The selected variant also has a packed 128×128 backdrop wash.
Use `scripts/audit_watercolor.py` with the river `.blend` for its packed 512×288 pigment and paper canvas, packed 128×128 sail wash, layered strokes, fixed camera, boat travel, and swaying reeds.
Use `scripts/audit_paper.py` with the butterfly `.blend` for its packed fiber stock, six physical paper layers, fold seams and fasteners, practical craft table, and held wing and travel poses.
Use `scripts/audit_chibi.py` with the courier `.blend` for its 59.5% head-height ratio, tiny limbs, letter, blink, hop, and offer. The selected variant adds a cap, satchel, and postal roundel.
Use `scripts/audit_noir.py` with the detective `.blend` for its fedora silhouette, two lights, six blind slats, 18 rain streaks, wet asphalt, haze, and walk. The selected variant adds three animated puddle ripples.
Use `scripts/audit_minimal.py` with the pendulum `.blend` for its three-color palette, negative-space framing, parented bob, and diminishing swing. The selected variant adds one pivot pin and one hairline arc.
Use `scripts/audit_vector.py` with the sprout `.blend` for its five flat fills, planar paths, fixed camera, stem and leaf growth, staggered bloom, and subpixel petal masking.
Use `scripts/audit_retro8.py` with the arcade ship `.blend` for its four emission colors, square-pixel meshes, fixed low raster, held location keys, and impact reveal. For its GIF, quantize from the full MP4 to the four render-sampled palette colors with no dithering.
Use `scripts/audit_retro16.py` with the fox `.blend` for its packed nearest dithered image, square-pixel sprites, fixed raster, held walk, and waterfall glints. Its GIF uses a 32-slot palette to preserve the richer authored colors through H.264 compression.
Use `scripts/audit_hd2d.py` with the lantern-bridge `.blend` for its pixel meshes, packed painted deck, 3D bridge span, warm keys, tilted orthographic camera with DOF, held walk, reeds, and ripples.
Use `scripts/audit_aero.py` with the dashboard `.blend` for its layered glossy materials, pill controls, clouds, bubble trail, leaf, moving highlight, and camera.

The generated report records the exact Blender version, input and output hashes, resolution, and encoded frame count. Inspect action timing and detail in the full MP4. The GIFs in the root README are compressed review copies of those renders; they do not replace the full motion and structural checks.

## Reviewed videogen handoff

The `blender-handoff` method packages a reported Blender MP4 with a narration WAV into a synthetic or approved videogen project. It verifies the MP4 hash, exact frame count, dimensions, and narration duration before copying either asset. The generated `asset-manifest.json` pins both hashes and rights notes; `scene-plan.json` records `visual.videoId`, its exact `videoStartFrame`, and the narration cue ID. The existing videogen validator rejects changed media, an unlisted shot, or an invalid cue. The generated `entry.tsx` and `video.tsx` are editable Remotion source, so a real project can adopt the reviewed shot at its approved cue.

From the repository root, this reproduces the tested handoff using the ignored Blender gallery MP4 and a rights-cleared narration WAV:

```powershell
$skill = 'content-studio/skills/content-studio-video/animation/blender'
python "$skill/scripts/handoff.py" --report tmp/gallery-clamp-v1.json --video tmp/gallery-clamp-v1.mp4 --narration '<reviewed-narration.wav>' --out tmp/clamp-handoff --title 'Clamp closing force' --cue-id cue-clamp --cue-start-frame 0 --video-license 'Original Content Studio procedural scene' --narration-license 'Owned or licensed narration'
node --input-type=module -e "import {validateScenePlan} from './content-studio/skills/content-studio-video/animation/videogen/scripts/scene-plan.mjs'; validateScenePlan('./tmp/clamp-handoff')"
npx remotion render tmp/clamp-handoff/entry.tsx BlenderHandoff tmp/clamp-handoff/handoff.mp4
```

On this Windows host, Remotion needed a writable `TEMP`/`TMP` outside the Codex sandbox path and permission to connect to its local Chrome DevTools port. The [exact handoff review](handoff-review.md) records the two scored candidates, encoded audio and picture checks, and selected GIF. This is a code-driven video handoff; edited-video timeline integration remains pending. Real drafts still require the workflow precheck and approved production plan before editing.

For a long shot, add `--resumable --batch-frames 48` to the full-shot command. It records hashed PNGs and a durable log beside the output, checks free space before each batch, and writes `complete.json` only after probing the encoded MP4. Repeat the same command and output path after an interruption; changed inputs or cached frames fail closed. `--stop-after 1` is available for a bounded pause and resume test. The [resumable render review](resume-review.md) records a real stop, resume, and uninterrupted comparison.

For a Content Studio video, copy the approved MP4 into the project asset folder, record its project-relative path and SHA-256 in `asset-manifest.json` with `origin: "procedural"`, and place it in the storyboard or Remotion scene at the intended narration cue. Use the [videogen asset contract](../videogen/references/idea-to-explainer.md) and review the hero alone, in the narrated composition, and in the exact final render. Real drafts must complete the [workflow precheck](../../../content-studio-workflow/SKILL.md) and obtain approval of the current production plan before editing. The edited-video delivery timeline does not yet consume Blender shot operations directly.
