# Reflection capability matrix

Detect and classify reflection candidates, apply only conservative glare/veil
fixes, preview bounded candidates, and optionally run a pretrained DSRNet review
pass. The examples blend a short shot from the published Out of Office Mode
Tomato Bath video with a mirrored shot from its published Dubai Fountain video
to create a synthetic, content-rich reflection. The source videos are unchanged.
The detector returned `UNSUPPORTED`; the bounded preview and AI pass remain
review aids, not removal claims.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `detect` | Supported | Video or folder → analysis report + evidence JPGs + masks + manifest | No | [Detected reflection masks](previews/detected-reflection.jpg) | Candidate masks include false positives on the hand; this scene was `UNSUPPORTED`. |
| `fix` | Supported | Approved manifest → corrected clip for FIX scenes | No | [Bounded correction candidate](previews/bounded-preview.jpg) | This is a preview, not an approved `fix.py` render. Only minor glare/veil scenes with approval may be fixed. |
| `preview` | Supported | Manifest + REVIEW or UNSUPPORTED scene → bounded comparison MP4 | No | [Bounded before/after frame](previews/bounded-preview.jpg) | A comparison of a possible correction, always review_required; the reflection remains visible. |
| `benchmark` | Supported | Clip + external backend config → benchmarks.json + benchmark.html | No | [Decision example](previews/example-decisions.md) | Does not install or promote a backend; licence and checkpoint recorded by the operator. |
| `ai` | Supported | Clip + DSRNet checkpoint → review MP4 + report + keys + compare | No | [DSRNet before/after frame](previews/ai-review.jpg) | At strength 0.5 the report returned `REVIEW`: 8.9% relative candidate reduction, 0.027 mean-luma change; reflection still visible. |
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

These examples use bounded derived frames from two already published channel videos
and a synthetic reflection blend. No source or full master is committed. The
`fix` shows a bounded correction candidate but no approved delivered correction.
`benchmark` has command/decision documentation only; no licensed external backend
is bundled.
The [decision notes](previews/example-decisions.md) describe their boundaries.
