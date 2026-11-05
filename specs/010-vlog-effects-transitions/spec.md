# Vlog effects and transitions

**Created:** 2026-11-04  
**Status:** Complete  
**Input:** Reusable effects and transitions that work on finished vlogs and Remotion vlog compositions.

## User scenarios

1. **Finished vlog (P1):** An editor adds short graphic beats at chosen times in a completed video. A timed ASS sidecar plays over the original without changing its video or audio. A separate short combined preview can be rendered for review.
2. **Hard cut (P1):** An editor places a transition graphic around a known cut in a finished video. The midpoint of its cue conceals the cut; the original frames remain available underneath the sidecar.
3. **Remotion vlog (P2):** A scene author places the same named graphic effects over a composition and uses clip transitions to mix two authored scenes. Timing is frame deterministic and colors are configurable.

## Requirements

- Provide at least five visually distinct, named graphic presets: flash, swipe, shutter, speed lines, and frame pop. Include clear examples and safe defaults.
- Existing video effects are additive graphics. They must not silently grade, resize, or replace footage or audio. Combined previews follow the current HDR/Dolby Vision guard.
- Cut-concealing presets align their full-cover moment to the cue midpoint. If a finished video has no cut there, the graphic remains an effect rather than inventing a new shot.
- Remotion provides the five graphics and at least crossfade, slide, wipe, and flash transitions between two scene nodes.
- Cue validation rejects unsupported presets, invalid colors, and effects too brief to render meaningfully. Existing ingredient/title/CTA cues keep working.
- Document how to use a sidecar, make a short review render, and import the Remotion components. Keep the preset pack independent of a particular channel identity.

## Acceptance

- A short demo on sparse ranges of the veg palav video shows each graphic preset without altering the original master. Frames at the entrance, midpoint, and exit are inspected.
- Remotion source builds and a rendered pilot demonstrates a two-scene transition and a graphic effect.
- Tests cover cue validation, boundary timing, package export, and color-preserving render command. Docs and staged diff checks pass.

## Assumptions

- A finished single-file vlog has no source handles for a true overlap transition. Graphic wipes, shutters, and flashes can conceal an existing hard cut; Remotion owns actual two-scene blending.
- Defaults are neutral and can be recolored per cue or component. No new publishing behavior is included.
