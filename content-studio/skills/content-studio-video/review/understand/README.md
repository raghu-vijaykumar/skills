# Understand capability matrix

Analyze sparse frames from an approved edit, combine verified visual evidence with
human context, and draft timestamped voiceover. The committed contact sheet is a real
extraction from a synthetic clip.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `inspect` | Supported | Approved edit or review candidate → sampled frames + contact sheets + evidence.json | No | [Contact sheet](previews/contact-sheet.jpg) | Sparse frames only; timestamps approximate; never infer landmarks, identities, or events from filenames. |
| `voiceover` | Supported | voiceover.json + evidence.json → voiceover.md + teleprompter + CSV + report | No | [Draft example](previews/example-voiceover.md) | Fails on overlap, out-of-range times, unknown frames, or pace; human approval before synthesis. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
