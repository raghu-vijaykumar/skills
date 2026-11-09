# Hairline Animation capability matrix

Use the Hairline Animation treatment for supported work. The registry lists formats
**video only**; the capability here is choosing and reviewing the treatment, not a
renderer owned by this leaf.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

> This leaf has no `methods.json` manifest; the rows document the operations its `SKILL.md` exposes. The checker treats them as documented workflow capabilities, not manifest methods.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `treatment` | Supported | Approved topic/scenes + evidence → Hairline Animation treatment plan and render handoff (video only) | No | [Treatment example](previews/treatment.md) | Narration-timed, frame-deterministic line-art animation. The planning skill does not render video; the selected renderer and format must be validated before export. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
