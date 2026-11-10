# Color capability matrix

Choose and apply reviewed looks or shot matching to edited footage. The preset
GIF is a real `warm-golden` output from a bounded published shot. The shot-match
three-panel GIF is an actual bounded run on a short shot from the already published
Out of Office Mode Tomato Bath video; the original footage is untouched.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Examples are illustrative evidence, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `preset` | Supported | SDR clip + look-range JSON → graded clip | Specialist only | [Animated before/after preview](previews/before-after.gif) | Built-in preset ranges only; HDR refused; no LUT import. |
| `shot-match` | Supported | Folder of clips + reference clip → channel-matched clips | Specialist only | [Animated reference, shifted input, matched output](previews/shot-match-before-after.gif) | Mean channel balance only; this result shifts skin color and needs human review. |
| `lut` | Unsupported | LUT + clip → not available | No | [Why there is no preview](previews/lut-command.md) | No script or backend; no renderer claim. |

## Shot-match preview

![Reference, shifted input, and shot-match output](previews/shot-match-before-after.gif)

The input was deliberately shifted warmer; `shot_match.py` then applied bounded
channel gains of red 0.8932, green 1.0149, and blue 1.12 against the published
reference shot. The GIF compares the same 1.5-second time window across all
three clips; it is not proof of accurate color. [Rebuild notes](previews/shot-match-report.md)
include the accepted CLI form.

## Evidence note

Both previews use bounded clips from the [published Tomato Bath video](https://www.youtube.com/watch?v=Sfjk9lfdbP0).
The preset GIF runs `scripts/preset.py` on a two-second copy and is rebuilt by
`scripts/build_preset_gallery.py --source-video <published-video.mp4> --at 245`.
The shot-match GIF is built from the actual matched output. Neither clip's
original footage nor a full master is committed.
