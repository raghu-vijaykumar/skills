# Blur review capability matrix

Inspect blur candidates and apply only human-approved camera-clip cuts. The
committed CSV is a labelled example of the review columns, not a real footage
decision.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `approved-cuts` | Supported | review.csv with human-approved remove=yes spans → cut clip | No | [Example review rows](previews/example-review.csv) | Human approval mandatory; low sharpness is not permission to delete; preserve source. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
