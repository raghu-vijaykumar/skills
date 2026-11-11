---
name: content-studio-video-stock-library
description: Select transparent video CTA variants and catalogue owned visuals or local-only reviewed sound effects in the Content Studio Git library.
---

# Stock library

Use this skill when an editor wants reusable authored visual assets across videos. Browse the [stock catalogue](README.md) for available CTA designs and their animated examples, then use `scripts/cta.py list` and `render --variant` to select one. The default `classic-bar` preserves the existing approved Like / Share / Subscribe animation; other variants use the same timed state sequence. Generated footage is silent with an alpha channel, so compositing does not alter the source picture outside the graphic or replace its audio. Full-resolution owned CTA assets are in this skill's Git-backed `assets/media/cta/` folder.

Before a **full asset render or video insertion**, run the mandatory `content-studio-workflow` precheck for the target project, present the exact method, command, destination, estimate, fallback, and review criteria, and obtain human approval of that plan revision. Review a bounded comparison first. For video placement, approve the cue/timeline or supported specialist manifest separately and inspect the exact delivered picture and sound. A stock clip is never automatically placed on every video; choose placement and timing against each shot. Catalogue import of media already approved for reuse can be done independently; confirm ownership and rights before indexing.

Run from the source repository root after approval:

```powershell
python content-studio/skills/content-studio-video/stock-library/scripts/cta.py list
python content-studio/skills/content-studio-video/stock-library/scripts/cta.py render --variant minimal-pills --output content-studio/skills/content-studio-video/stock-library/assets/media/cta/my-new-cta.mov --width 3840 --height 2160 --fps 30 --duration 5.0 --position top-right
```

The renderer needs Pillow, FFmpeg, FFprobe, and a bold Arial or DejaVu Sans font. It refuses to overwrite an existing asset. Confirm the output pixel format has an alpha channel, dimensions, no audio, and the Like, Share, Subscribe, Subscribed, and bell states over representative footage. For HDR/HLG work, the existing narrow [motion-graphics composer](../edit/motion-graphics/SKILL.md) may consume a reviewed stock clip. The generic delivery timeline does not yet support this alpha overlay operation.

For **self-created** memes, GIFs, stickers, and stock clips, use `scripts/library.py` with this skill's `assets/` folder as `--library`. Supply true rights and creator metadata. The importer copies and SHA-256 deduplicates files, preserves the original, and regenerates `assets/README.md`. Owned assets and catalogue metadata are tracked in Git. For sourced sound effects, use [reel SFX](../audio/reel-sfx/SKILL.md) and catalogue only reviewed candidates with source provenance; unknown-rights WAVs stay under `assets/media/sfx/`, ignored by Git, and remain `reference-only`. Do not force-add those WAVs to a public repository without redistribution rights. See the [catalogue guide](README.md) for commands and ownership boundaries. The [memes skill](../memes/SKILL.md) continues to handle contextual reaction suggestions and rights/timing review.

For shot-aware SFX proposals, use `shot-sfx-select` after an editor identifies each sound by listening and assigns shot situation tags. `library.py describe-sfx` records the audible label, matching shot tags, and identification evidence without changing rights or source media; descriptions default to `pending` until confirmed. `library.py suggest-sfx` reads a shot manifest and ranks exact tag and duration matches only for passed identities. Default `delivery` mode only proposes effects cleared for reuse; `reference` mode may show unknown-rights clips but marks them unavailable for placement. Dialogue and natural sound shots are skipped. The output is a review proposal, never an automatic timeline edit. Use the workflow precheck and an approved plan before changing catalogue metadata or placing a cue; timeline approval and exact-master listening remain separate. See the [shot selection guide](README.md#shot-aware-sound-effect-selection).
