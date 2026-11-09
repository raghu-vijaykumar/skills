# Publish capability matrix

Publish an approved video to YouTube now or schedule it, or publish an Instagram Reel
now. No credentials or uploads are committed; evidence is a labelled command example.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

> This leaf has no `methods.json` manifest; the rows document the operations its `SKILL.md` exposes. The checker treats them as documented workflow capabilities, not manifest methods.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `preview-package` | Supported | Approved draft package → validation report | No | [Publish example](previews/example-publish.md) | Preview is not authorization; checks master, title, description, thumbnail, creative record, credits, and hashes. |
| `publish-youtube` | Supported | Approved package → public YouTube upload | No | [Publish example](previews/example-publish.md) | Requires explicit human authorization and --confirm; retain receipts and platform IDs. |
| `schedule-youtube` | Supported | Approved package + future ISO time → scheduled YouTube upload | No | [Publish example](previews/example-publish.md) | Native scheduling only; scheduled uploads remain drafts until public backup is verified. |
| `publish-instagram` | Supported | Approved package → Instagram Reel | No | [Publish example](previews/example-publish.md) | No scheduling path; requires explicit authorization and --confirm. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
