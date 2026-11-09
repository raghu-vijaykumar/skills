# Reframe capability matrix

Create reviewed portrait crops from finished or approved video ranges. The
committed preview pairs a synthetic landscape frame with the actual center-crop
output; it shows framing behavior, not a delivery render.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `subjects` | Supported | Landscape video + subject boxes → stable crop preview + reframe.json | Specialist only | [Subject-box example](previews/example-subjects.json) | Needs supplied boxes; one stable crop per range. |
| `saliency` | Supported | Landscape video → crop preview + reframe.json | Specialist only | [Crop preview](previews/center-crop.png) | Edge/saliency heuristic; not object or identity understanding. |
| `center` | Supported | Landscape video → crop preview + reframe.json | Specialist only | [Crop preview](previews/center-crop.png) | Deliberate center crop; may cut the subject. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included. Rebuild instructions are in the linked evidence files where a renderer produced the preview.
