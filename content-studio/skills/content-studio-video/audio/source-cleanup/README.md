# Source cleanup capability matrix

Compare camera-source speech-cleanup methods before manual editing. The committed
MP3s are seven-second excerpts from the same synthetic speech plus pink noise.
The `afftdn` and `deepfilter` candidates were produced by their named skill
entrypoints. Compare the speech and residual noise by listening; neither candidate
is automatically approved for delivery.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Examples are illustrative evidence, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `deepfilter` | Supported | Camera clip with diagnosed speech noise → processed clip + candidate WAV + review report | Specialist only | [Before](previews/before.mp3) / [DeepFilter after](previews/after-deepfilter.mp3) | Requires local DeepFilter runtime; this candidate returned `audio_review_required`. |
| `afftdn` | Supported | Camera clip with diagnosed speech noise → processed clip + candidate WAV + review report | Specialist only | [Before](previews/before.mp3) / [after](previews/after-afftdn.mp3) | FFmpeg adaptive denoise; may introduce level drift; listening review required. |
| `keep-source` | Supported | Camera clip → unchanged source + report | Specialist only | [No-denoise result](previews/methods.md#keep-source-result) | Explicit no-denoise route when the source is already clean. |

## Listen to the same input

| Input | FFmpeg `afftdn` | DeepFilterNet |
| --- | --- | --- |
| [Noisy speech](previews/before.mp3) | [Denoised candidate](previews/after-afftdn.mp3) | [Denoised candidate](previews/after-deepfilter.mp3) |

The exact commands, local runtime requirement, and no-denoise result are in
[the method notes](previews/methods.md).

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
