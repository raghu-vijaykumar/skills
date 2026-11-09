# Stabilization capability matrix

Apply reviewed two-pass camera stabilization to a diagnosed clip. The GIF is a real
before/after loop from a synthetic shaky source.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `vidstab` | Supported | Diagnosed unstable clip → two-pass stabilized clip | No | [Before/after loop](previews/stabilize.gif) | Crop risk must be reviewed; method fixed to two-pass vidstab; preserve source. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
