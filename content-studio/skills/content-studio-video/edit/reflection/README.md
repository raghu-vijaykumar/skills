# Reflection capability matrix

Detect and classify reflection candidates, apply only conservative glare/veil
fixes, preview bounded candidates, and optionally run a pretrained DSRNet review
pass. The committed contact sheet is a real detector output from a synthetic clip
where both scenes correctly returned `SKIP`.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `detect` | Supported | Video or folder → analysis report + evidence JPGs + masks + manifest | No | [Detector contact sheet](previews/contact-sheet.jpg) | Candidate mask is evidence, not a reflection layer; analysis cached by source hash. |
| `fix` | Supported | Approved manifest → corrected clip for FIX scenes | No | [Decision example](previews/example-decisions.md) | Masked highlight compression only; safety gates reject luma/clipping drift. |
| `preview` | Supported | Manifest + REVIEW scene → bounded comparison MP4 | No | [Decision example](previews/example-decisions.md) | Always review_required; never removes content-rich reflections. |
| `benchmark` | Supported | Clip + external backend config → benchmarks.json + benchmark.html | No | [Decision example](previews/example-decisions.md) | Does not install or promote a backend; licence and checkpoint recorded by the operator. |
| `ai` | Supported | Clip + DSRNet checkpoint → review MP4 + report + keys + compare | No | [Decision example](previews/example-decisions.md) | 1.54 GB weights; attenuation not reconstruction; returns REVIEW, SKIP, or REJECTED. |
| `generative-removal` | Unsupported | Clip → not available | No | [Decision example](previews/example-decisions.md) | No generative backend bundled; unsupported. |

## Decisions

| Decision | Meaning |
| --- | --- |
| `SKIP` | No candidate above threshold, or no measurable AI reduction |
| `FIX` | Small persistent glare/veil; masked highlight compression only |
| `REVIEW` | Content-rich or transient candidate; inspect evidence and a bounded preview |
| `UNSUPPORTED` | Beyond the available backend's reliable range; preserve the source |
| `REJECTED` | An AI safety gate failed |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included. Rebuild instructions are in the linked evidence files where a renderer produced the preview.
