# Ingest capability matrix

Order camera clips by capture time before manual editing. The evidence is a labelled
dry-run report, not a mutation of a real draft.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `capture-order` | Supported | Draft camera folder with capture metadata → capture order + renames + _timeline.csv | No | [Order report example](previews/example-order-report.md) | Ordering only; exact/near-duplicate handling belongs to source preprocessing. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
