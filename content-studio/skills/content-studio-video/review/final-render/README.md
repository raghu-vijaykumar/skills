# Final render verification capability matrix

Verify the exact delivered video and audio before package approval. This skill has an
empty method manifest: it owns review gates, not a media renderer.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

> This leaf has an empty `methods.json` manifest; the row documents the operation its `SKILL.md` exposes. The checker treats it as a documented workflow capability, not a manifest method.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `verify-delivered-master` | Supported | Exact rendered master + approved plan checklist → verification evidence and human decision record | Specialist only | [Verification example](previews/example-verification.md) | Does not auto-approve publication; subjective issues need a recorded human decision; objective metrics only with a valid reference. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
