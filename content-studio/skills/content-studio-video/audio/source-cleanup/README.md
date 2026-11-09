# Source cleanup capability matrix

Compare camera-source speech-cleanup methods before manual editing. The committed
MP3s are real 7-second before/after excerpts from synthetic speech plus pink noise
through `afftdn.py`.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `deepfilter` | Supported | Camera clip with diagnosed speech noise → processed clip + candidate WAV + review report | Specialist only | [Method comparison](previews/methods.md) | Requires local DeepFilter runtime; compare candidate WAVs before selecting. |
| `afftdn` | Supported | Camera clip with diagnosed speech noise → processed clip + candidate WAV + review report | Specialist only | [Before](previews/before.mp3) / [after](previews/after-afftdn.mp3) | FFmpeg adaptive denoise; may introduce level drift; listening review required. |
| `keep-source` | Supported | Camera clip → unchanged source + report | Specialist only | [Method comparison](previews/methods.md) | Explicit no-denoise route when the source is already clean. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
