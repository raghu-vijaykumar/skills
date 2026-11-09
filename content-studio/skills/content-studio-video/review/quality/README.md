# Quality measurement capability matrix

Measure reference-based video quality when a comparable source exists. The
committed JSON is an actual measurement between synthetic source and denoised
preview; the low values demonstrate the metric, not a quality recommendation.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `measure` | Supported | Reference video + distorted video → SSIM/PSNR/VMAF JSON | No | [Measurement JSON](previews/example-quality.json) | Reference-based only; cannot prove a creative edit or enhancement looks better. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
