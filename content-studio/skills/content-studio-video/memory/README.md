# Editing memory capability matrix

Store confirmed editing preferences and review decisions in a private SQLite database.
The committed report is real command output from an isolated temporary database; no
private memory database is included.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

> This leaf has no `methods.json` manifest; the rows document the operations its `SKILL.md` exposes. The checker treats them as documented workflow capabilities, not manifest methods.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `retrieve` | Supported | Scope/project → merged applicable preferences | No | [Command output](previews/memory-report.txt) | Specific layers win; current explicit instructions outrank saved preferences; chat history is not memory. |
| `set` | Supported | Confirmed preference key/value/scope → stored preference | No | [Command output](previews/memory-report.txt) | Only after explicit user confirmation; never approves an edit or publication. |
| `record` | Supported | Human decision + context → review event | No | [Command output](previews/memory-report.txt) | Logs history, not an automatically reusable preference; actor must be human. |
| `events` | Supported | Scope/project → review event history | No | [Command output](previews/memory-report.txt) | Read-only audit view. |
| `forget` | Supported | Preference key/scope → removed preference | No | [Command output](previews/memory-report.txt) | Does not remove unrelated event history; use purge-events deliberately. |

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
