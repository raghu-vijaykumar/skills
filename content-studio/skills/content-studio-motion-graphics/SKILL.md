---
name: content-studio-motion-graphics
description: Add kinetic titles, ingredient lists, bilingual callouts, and like/share/subscribe graphics to an already edited Out of Office Mode cooking video, then render a separate review copy.
---

# Out of Office Mode motion graphics

Read the channel rules, this skill, and the source draft before editing. Keep the source video untouched. Extract audio and inspect sparse frames or short ranges to identify actions without decoding the entire master for analysis. Use speech as context, but only label ingredients actually supported by the frame or clear narration; do not invent quantities.

Create a JSON cue sheet with the source path and timed events:

- `title`: a two-part label and optional Kannada subtitle. Stagger the words on separate beats. Preview the shot and place the panel in open space.
- `ingredient_list`: 1–12 chronological `items`, each with `at` and `label`, plus optional `kannada`. Use this accumulating lower third while ingredients are introduced. Each new item briefly enlarges, then joins the persistent list. Use the later `ingredient` cue when an ingredient is actually added or cooked.
- `leaves`: exactly three English/Kannada `pairs` that rotate in the same place. Verify spelling with the speaker or another reliable source.
- `ingredient`: label, action, and brief visual or audio evidence for a cooking beat.
- `cta`: 1–3 labeled emoji `beats`; the default is 👍 LIKE, 📤 SHARE, 🔔 SUBSCRIBE. Keep this reusable in the cue data and place it near a natural ending beat.

Keep overlays away from hands, food, faces, and existing text. Use short, staggered entrances and a brief scale bounce for kinetic typography. The renderer uses cream recipe cards, teal type, coral details, and yellow accents from the Out of Office Mode intro. Sample frames around each cue and review the moving overlays, not just their end states.

Use `python scripts/overlay.py validate <cues.json>` to check timing and source color metadata. `python scripts/overlay.py sidecar <cues.json> --output <source-basename.ass>` creates the motion graphics without touching the source video. Prefer the sidecar for a Dolby Vision source so the original bitstream and its RPU remain intact. Load it over the original in a player or editor that supports ASS.

`python scripts/overlay.py render <cues.json> --output <review.mp4> [--start seconds --duration seconds]` makes a separate combined review copy at the source resolution, with copied audio and native HLG base-layer tags. NVENC is tried first for 10-bit footage, with x265 as fallback. A Dolby Vision source requires `--allow-dv-preview`: re-encoding loses its RPU, so this preview is not color-equivalent to the original on Dolby Vision playback. Compare unaffected footage with the original, inspect the overlay at every cue, and check output metadata and audio. Preserve the cue sheet, sidecar, and any preview together; publication remains a separate request.


## Reusable vlog style presets (travel, cooking, daily)

The original cooking overlay renderer and its cue types remain supported. For new vlogs, first select a style from `presets/presets.json`; this is a **style specification and cue validation layer**, not a claim that every preset animation is already rendered by `overlay.py`.

| Category | Presets | Default |
| --- | --- | --- |
| travel | `travel-cinematic`, `travel-playful`, `travel-journal` | `travel-cinematic` |
| cooking | `cooking-recipe`, `cooking-minimal`, `cooking-playful` | `cooking-recipe` |
| daily | `daily-clean`, `daily-playful`, `daily-cozy` | `daily-clean` |

Select a preset without exposing commands in the user's creative prompt:

```bash
python content-studio/skills/content-studio-motion-graphics/scripts/presets.py --category travel --preset travel-journal
```

Validate a proposed cue list using `--cues /path/to/cues.json`. Cue events need `type`, `at` (seconds) and visual/audio `evidence` for factual labels; the renderer must separately verify support for the selected type. Place graphics away from faces, food, hands, landmarks and other important actions. Use bilingual English/Kannada text when requested, but have the user review spelling and pronunciation. Show a short representative preview of each motion type before final render. Avoid repetitive CTAs and do not add unsupported prices, locations, quantities or timestamps.

In a user-facing prompt, `motion_graphics: {"category":"travel","preset":"travel-cinematic","intensity":"subtle"}` is sufficient. The agent owns selection, cue timing, evidence checks, review and renderer compatibility.
