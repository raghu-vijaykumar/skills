# Upscale capability matrix

Compare and, when justified, upscale one completed edited video before overlays.
The committed pair is a real Lanczos result from a synthetic source; panel scaling
is for display, so it is not a pixel-level quality claim.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `compare` | Supported | Finished edit ranges → comparison preview + diagnosis | Specialist only | [Lanczos before/after](previews/lanczos-before-after.png) | Diagnosis only; never replaces the source. |
| `lanczos` | Supported | Finished SDR edit → upscaled clip | Yes | [Lanczos before/after](previews/lanczos-before-after.png) | Resolution scaling only; cannot invent detail or fix motion blur. |
| `real-esrgan` | Supported | Finished edit + local weights → upscaled clip | Specialist only | [AI upscale commands](previews/example-ai-upscale.md) | Requires Real-ESRGAN weights/GPU; rejects draft-batch and timeline flags. |
| `pytorch` | Supported | Finished edit + local weights → upscaled clip | Specialist only | [AI upscale commands](previews/example-ai-upscale.md) | Requires a local PyTorch backend; rejects draft-batch and timeline flags. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included. Rebuild instructions are in the linked evidence files where a renderer produced the preview.
