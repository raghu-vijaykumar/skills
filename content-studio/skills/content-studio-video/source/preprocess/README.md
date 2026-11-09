# Source preprocessing capability matrix

Order and diagnose camera originals for manual editing. The committed report is the
actual analysis output for a synthetic clip, with absolute scratch paths removed.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `prepare-clips` | Supported | Raw folder or channel draft → capture order + per-clip analysis reports + review.csv | No | [Analysis report](previews/report.json) and [review CSV](previews/review.csv) | Forced analysis-only; no processed clip, audio cleanup, or blur cut; originals preserved. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
