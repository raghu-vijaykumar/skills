# Audio mastering capability matrix

Master spoken-word audio in a folder of videos. The committed before/after MP3s are
real 7-second excerpts from synthetic text-to-speech; they demonstrate loudness
normalization, not a private recording or a subjective quality judgment.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `master` | Supported | Video folder or draft ID → mastered WAV/MP4 + manifest + 10-second before/after WAVs | Specialist only | [Before](previews/before.mp3) / [after](previews/after.mp3) and [manifest excerpt](previews/manifest.json) | Targets -16 LUFS and -1.5 dBTP; cleanup remains REVIEW; never trims or joins; inputs never overwritten. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
