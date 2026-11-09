# Clip editing capability matrix

Apply requested frame-accurate trims, cuts, or joins and review a supplied manual edit.
The committed GIF is a real trim of a synthetic clip; the join evidence is a labelled
command example.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

> This leaf has no `methods.json` manifest; the rows document the operations its `SKILL.md` exposes. The checker treats them as documented workflow capabilities, not manifest methods.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `trim` | Supported | Clip + start/end → new trimmed clip | Specialist only | [Trim preview](previews/trim-preview.gif) | Explicit requests only; keep output separate; review color tags and audio. |
| `cut` | Supported | Clip + remove range → new cut clip | Specialist only | [Trim preview](previews/trim-preview.gif) | Explicit requests only; never the raw-folder default. |
| `join` | Supported | Ordered clips + approved source order → joined clip | Specialist only | [Join example](previews/example-join.md) | Approved order required; review transitions, color, audio, and full export. |
| `review-supplied-render` | Supported | Supplied manual render → hashed review evidence and metadata | Specialist only | [Trim preview](previews/trim-preview.gif) | Analyze actual frames/audio; do not invent places, events, speech, or titles from filenames. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
