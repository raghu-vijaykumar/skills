---
name: content-studio-motion-graphics
description: Add timed ingredient callouts and like/share/subscribe graphics to an already edited Out of Office Mode cooking video, then render a separate review copy.
---

# Out of Office Mode motion graphics

Read the channel rules, this skill, and the source draft before editing. Keep the source video untouched. Extract audio and inspect sparse frames or short ranges to identify actions without decoding the entire master for analysis. Use speech as context, but only label ingredients actually supported by the frame or clear narration; do not invent quantities.

Create a JSON cue sheet with source path and timed `ingredient` or `cta` events. Each ingredient cue includes the ingredient name, action, and a brief evidence note. Place the callout when the ingredient is used, not merely when it appears on a prep board. Keep overlays away from hands, food, faces, and existing text. The renderer uses cream recipe cards, teal type, coral icons, and yellow accents from the Out of Office Mode intro. Put like/share/subscribe near a natural ending beat instead of interrupting instruction.

Use `python scripts/overlay.py validate <cues.json>` to check timing and source color metadata. `python scripts/overlay.py sidecar <cues.json> --output <source-basename.ass>` creates the motion graphics without touching the source video. Prefer the sidecar for a Dolby Vision source so the original bitstream and its RPU remain intact. Load it over the original in a player or editor that supports ASS.

`python scripts/overlay.py render <cues.json> --output <review.mp4> [--start seconds --duration seconds]` makes a separate combined review copy at the source resolution, with copied audio and native HLG base-layer tags. NVENC is tried first for 10-bit footage, with x265 as fallback. A Dolby Vision source requires `--allow-dv-preview`: re-encoding loses its RPU, so this preview is not color-equivalent to the original on Dolby Vision playback. Compare unaffected footage with the original, inspect the overlay at every cue, and check output metadata and audio. Preserve the cue sheet, sidecar, and any preview together; publication remains a separate request.
