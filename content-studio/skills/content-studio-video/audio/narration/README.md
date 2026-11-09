# Narration placement capability matrix

Place approved recorded or generated narration on a supplied edited-video timeline.
The committed excerpt is a real mix of synthetic text-to-speech over a synthetic
clip; it is not a private voice.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `mix-into-video` | Supported | Edited master + approved narration WAV → separate voiced master | Specialist only | [Voiced excerpt](previews/voiced-preview.mp3) | Narration must fit the edit; script authoring and synthesis are separate skills; timing and mix require human listening. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
