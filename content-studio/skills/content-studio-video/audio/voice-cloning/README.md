# Voice cloning capability matrix

Enroll a consented voice profile and synthesize Kannada/English narration locally.
No voice audio, profile, or model is committed; the evidence is a labelled command
example.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `enroll-and-synthesize` | Supported | Consented samples + approved script + IndicF5 model → segment WAVs + manifest + assembled narration | Specialist only | [Command example](previews/example-synthesis.md) | Consent mandatory; weights/profiles outside Git; tempo cap 1.12; round-trip transcription and listening review. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
