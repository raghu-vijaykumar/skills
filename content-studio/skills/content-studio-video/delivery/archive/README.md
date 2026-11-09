# Archive capability matrix

Back up public YouTube uploads and their exact metadata to Git, and sync durable media
through rclone to Drive. No channel data or media is committed; evidence is a labelled
report example.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

> This leaf has no `methods.json` manifest; the rows document the operations its `SKILL.md` exposes. The checker treats them as documented workflow capabilities, not manifest methods.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `backup` | Supported | Public channel uploads → Git metadata + reconciled sources | No | [Backup example](previews/example-backup.md) | Public videos only; unpublished/scheduled stay in drafts; verified backup and Drive copy before moving. |
| `sync` | Supported | Draft and shared media → Drive via rclone | No | [Backup example](previews/example-backup.md) | Verify with rclone check before pruning; never delete remote data. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
