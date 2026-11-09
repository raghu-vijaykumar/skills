# Narration timing capability matrix

Generate and verify narration cues for code-driven videos. Evidence is a labelled
cue and verification example, not a rendered scene.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `narration` | Supported | Script + project configuration → timed cue JSON + narration assets | Specialist only | [Cue example](previews/example-cues.json) | Automatic speech alignment is not implemented; changed script or voice invalidates the cue cache. |
| `verify-narration` | Supported | Authored phrases + recorded audio → pass/fail synchronization report | Specialist only | [Verification example](previews/example-verify-report.md) | Checks exact phrases and timing, not subjective delivery. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
