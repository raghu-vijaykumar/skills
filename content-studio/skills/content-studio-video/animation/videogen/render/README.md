# Render capability matrix

Render bounded Remotion evidence and full delivery output. Evidence is a labelled
command example; no full master is committed.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `preview-range` | Supported | Project + explicit --from/--to → bounded evidence MP4 | Specialist only | [Render example](previews/example-render.md) | Range is mandatory; this is not a delivery render. |
| `delivery` | Supported | Approved project → full delivery render | Specialist only | [Render example](previews/example-render.md) | Only after review; project configuration defines output. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
