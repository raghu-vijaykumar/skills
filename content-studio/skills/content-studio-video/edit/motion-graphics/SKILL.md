---
name: content-studio-video-motion-graphics
description: Add reusable timed motion graphics and transition effects to an edited video, or use matching components in a Remotion vlog. Supports cooking callouts, bilingual text, and review renders.
---

# Motion graphics and vlog effects

Before changing the draft, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist.

Read the channel rules and source draft before editing. Keep the source video untouched. Inspect sparse frames or short ranges to locate actions and cuts without decoding the entire master for analysis. Use speech as context, but only label ingredients actually supported by a frame or clear narration; do not invent quantities.

For a finished vlog, create a JSON cue sheet with timed `effect` events. Choose `flash`, `swipe`, or `shutter` to conceal a known hard cut, and place that cut at the cue midpoint. Use `speed-lines` or `frame-pop` as shorter accents around action beats. All five effects can use per-cue `color` and `accent` hex colors. They add graphics over footage; they do not change the underlying shots. For Remotion vlogs, import the matching `VlogEffect` and `VlogTransition` components. Read [effects and transitions](references/effects.md) for cue examples, Remotion usage, and review checks.

For a place arrival, use a `location` event with `start`, `end`, a short `label`,
and visual or reliable audio `evidence`. It draws a compact pin and place-name
card at the lower left. Confirm the exact destination against the footage,
preview the card for occlusion, and render its ASS sidecar as the
`motion-graphics-ass` operation in the approved delivery timeline. The sidecar
does not encode a separate full video.

For cooking videos, the same JSON cue sheet supports:

- `title`: a two-part label and optional Kannada subtitle. Stagger the words on separate beats. Preview the shot and place the panel in open space.
- `ingredient_list`: 1–12 chronological `items`, each with `at` and `label`, plus optional `kannada`. Use this accumulating lower third while ingredients are introduced. Each new item briefly enlarges, then joins the persistent list. Use the later `ingredient` cue when an ingredient is actually added or cooked.
- `ingredient_list.heading`: optional short heading; the default remains `INGREDIENTS / ONE BY ONE` for existing cue sheets. Set `INGREDIENTS` when the step-by-step wording is unwanted.
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
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/presets.py --category travel --preset travel-journal
```

Validate a proposed cue list using `--cues /path/to/cues.json`. Cue events need `type`, `at` (seconds) and visual/audio `evidence` for factual labels; the renderer must separately verify support for the selected type. Place graphics away from faces, food, hands, landmarks and other important actions. Use bilingual English/Kannada text when requested, but have the user review spelling and pronunciation. Show a short representative preview of each motion type before final render. Avoid repetitive CTAs and do not add unsupported prices, locations, quantities or timestamps.

In a user-facing prompt, `motion_graphics: {"category":"travel","preset":"travel-cinematic","intensity":"subtle"}` is sufficient. The agent owns selection, cue timing, evidence checks, review and renderer compatibility.

## Reusable transparent 4K CTA

`scripts/cta_stock.py` draws an original Like, Share, Subscribe-to-Subscribed, and bell sequence as a five-second, transparent UHD ProRes 4444 clip. The reference video is only visual inspiration; no frames or sound are copied. Generate the asset in the content project's assets folder, not this source repository:

The generator requires Python Pillow plus FFmpeg and FFprobe on `PATH`.

```powershell
python content-studio/skills/content-studio-video/edit/motion-graphics/scripts/cta_stock.py render --output <content-assets>/like-share-subscribe-uhd-alpha.mov --width 3840 --height 2160 --fps 30 --duration 5.0 --position top-right
```

The output has no sound so the vlog soundtrack stays intact. `top-left`, `bottom-right`, `bottom-left`, and `center` are also available. Check alpha and every button state in a short composite preview before reusing it. Place it near an ending beat, away from faces and essential action. Other formats or frame rates require a fresh asset render and review. See [CTA and HLG composition](references/cta-stock-hlg.md).

For an HLG edit needing this CTA and a five-second SDR intro, `scripts/hdr_compose.py` reads an exact, versioned manifest. It checks source, intro, cue sheet, ASS sidecar, CTA, and approved preflight plan hashes; rejects unsupported settings; makes bounded previews; requires separate human approval of its fingerprint; and encodes one HEVC Main10 HLG-base master. This narrow route supports only 3840×2160/30, 48 kHz input audio, a five-second intro and CTA, and the named operations. The generic delivery timeline remains SDR-only. Compositing cannot preserve the source Dolby Vision RPU. Preserve the source and inspect the exact HLG-base output before package approval.
