# Final render verification capability matrix

Verify the exact delivered video and audio before package approval. This skill has an
hash-bound inspection method and review gates; it does not render media.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `inspect-exact-master` | Supported | Exact master + expected SHA-256 → format, loudness, timecoded candidates and safe-zone guide frames | Yes, called by timeline verify | [Verification example](previews/example-verification.md) | Black, freeze, flash and silence are candidates for human review; no automatic creative decision or publication approval. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
