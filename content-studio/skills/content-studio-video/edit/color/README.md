# Color capability matrix

Choose and apply reviewed looks or shot matching to edited footage. The committed
before/after is a real 1:1 frame pair from a synthetic source graded with the
`warm-golden` preset.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `preset` | Supported | SDR clip + look-range JSON → graded clip | Specialist only | [Before/after preview](previews/before-after.png) | Built-in preset ranges only; HDR refused; no LUT import. |
| `shot-match` | Supported | Clip + reference clip → channel-matched clip | Specialist only | [Command example](previews/shot-match-report.md) | Mean channel balance only; not a creative grade; review temporal consistency. |
| `lut` | Unsupported | LUT + clip → not available | No | [Why there is no preview](previews/lut-command.md) | No script or backend; no renderer claim. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included. Rebuild instructions are in the linked evidence files where a renderer produced the preview.
