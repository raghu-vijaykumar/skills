# Memes capability matrix

Maintain a private local meme catalogue and propose evidence-based, reviewable
insertions. No third-party media or database is committed; evidence is labelled
catalogue and proposal examples.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

> This leaf has no `methods.json` manifest; the rows document the operations its `SKILL.md` exposes. The checker treats them as documented workflow capabilities, not manifest methods.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `init` | Supported | Local catalogue path → initialized SQLite catalogue | No | [Catalogue example](previews/example-catalogue.md) | Private local library; never commit third-party media or the database. |
| `add` | Supported | User-authorized media + metadata → deduplicated catalogue entry | No | [Catalogue example](previews/example-catalogue.md) | User supplies authorized files; SHA-256 dedupe; unknown rights are not publishable. |
| `search` | Supported | Keyword/category/tags → matching catalogue entries | No | [Catalogue example](previews/example-catalogue.md) | Keyword search only; no semantic understanding. |
| `propose-insertion` | Supported | Approved timeline + observed scene evidence → pending review manifest | No | [Proposal example](previews/example-proposal.md) | Default 1-3 per 10 min; human approves rights and timing; no automatic render. |

## Named profiles and insertion modes

The [travel](presets/travel.json), [cooking](presets/cooking.json) and
[daily](presets/daily.json) profiles set the per-10-minute cap, triggers and
exclusions for each vlog category. Every profile enables the same three insertion
modes: `cutaway`, `pip` and `audio_stinger`. Profiles are review rules, not
rendered templates.

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
