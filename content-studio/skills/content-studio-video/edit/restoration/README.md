# Restoration capability matrix

Diagnosis-first picture denoise, deflicker, lens correction, sharpening, and
refinement. The committed crop pair is a real `denoise-light` output from synthetic
noisy media; it is not a quality claim.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `denoise-light` | Supported | Noisy clip → denoised clip | Yes | [1:1 before/after](previews/denoise-before-after.png) | Light spatial/temporal filter; not detail reconstruction. |
| `denoise-medium` | Supported | Noisy clip → denoised clip | Yes | [Command examples](previews/example-commands.md) | Stronger smoothing; check texture loss. |
| `denoise-nlmeans` | Supported | Noisy clip → denoised clip | Specialist only | [Command examples](previews/example-commands.md) | Slower NLMeans estimate; timeline has light/medium adapters only. |
| `deflicker` | Supported | Flickering clip → deflickered clip | Yes | [Command examples](previews/example-commands.md) | Temporal flicker only; cannot fix exposure changes without visible pumping. |
| `lens` | Supported | Clipped video + lens parameters → lens-corrected clip | Yes | [Command examples](previews/example-commands.md) | Needs explicit lens/perspective values; no automatic camera profile. |
| `sharpen-light` | Supported | Clip → sharpened clip | Yes | [Command examples](previews/example-commands.md) | Conservative sharpening; cannot recover missed focus. |
| `sharpen-medium` | Supported | Clip → sharpened clip | Yes | [Command examples](previews/example-commands.md) | Stronger halo/noise risk; inspect at delivery size. |
| `refine` | Supported | Clip + bounded settings search → selected polish settings | Specialist only | [Command examples](previews/example-commands.md) | Iterative per-clip selection; not a single timeline operation. |
| `deblur` | Unsupported | Blurred clip → not available | No | [Command examples](previews/example-commands.md) | No deblur model; conservative sharpening is not deblurring. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included. Rebuild instructions are in the linked evidence files where a renderer produced the preview.
