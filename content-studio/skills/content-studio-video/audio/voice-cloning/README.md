# Voice cloning capability matrix

Enroll a consented voice profile and synthesize Kannada/English narration locally.
The gallery includes a synthetic-voice inference sample that failed the
round-trip text gate. Bundled consented profiles are already tracked in Git;
new workspace profiles and model weights are not gallery assets.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Examples are illustrative evidence, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `enroll-and-synthesize` | Supported | Consented samples + approved script + IndicF5 model → segment WAVs + manifest + assembled narration | Specialist only | [Actual inference sample and commands](previews/example-synthesis.md) | A Kannada/Latin mixed cue needs phonetic Kannada TTS text or a bounded reviewed override; the gallery sample failed transcription and is not approved narration. `assemble --duration` accepts a planned timeline length without an intermediate picture; consent, tempo cap 1.12 and listening review remain required. |
| `compare-indic-mio-emotion` | Supported preview | Consented Rakshitha profile + cached Indic-Mio LiteRT bundle → paired neutral/emotion WAVs + manifest | Specialist only | `scripts/indic_mio_compare.py` writes to `%LOCALAPPDATA%/ContentStudio/voice-tests/indic-mio-rakshitha/` by default | Script-only local sidecar; short utterances, fixed seed, no production mux. Check wording and speaker resemblance by listening before selecting this backend. |

## Evidence note

The sample uses a synthetic system TTS reference. This gallery does not add
private voice recordings, weights, credentials, licensed music, or a full master.
