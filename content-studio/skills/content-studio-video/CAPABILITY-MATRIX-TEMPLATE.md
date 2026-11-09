# Capability matrix template

Copy this structure into a leaf skill's `README.md`. Keep the six-column table so
the checker and readers see the same contract for every video capability.

## Required sections

1. A short description of the skill and what the committed evidence demonstrates.
2. The shared **Status** and **Delivery timeline** legend.
3. `## Capability matrix` with exactly the columns below.
4. Any named presets, variants, or profiles, checked against their registry.
5. `## Evidence note` stating that previews are synthetic or labelled examples.

## Status and timeline legend

Use these labels verbatim:

| Label | Meaning |
| --- | --- |
| `Supported` | The skill manifest provides a runnable script for the capability. |
| `Unsupported` | The manifest declares no script; the document makes no capability claim. |
| `Yes` | The single-render delivery timeline consumes an equivalent operation. |
| `Specialist only` | Use the skill for a bounded preview and carry the approved result forward. |
| `No` | Unsupported, or intentionally outside the one-render route. |

## Matrix skeleton

```markdown
## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `method-id` | Supported | Source + parameters → reviewed output | Yes | [Preview](previews/example.gif) | Known boundary; what this does not prove. |
| `unsupported-id` | Unsupported | Input → not available | No | [Why there is no preview](previews/unsupported-id.md) | No script or backend. |
```

Rules:

- Use the manifest `id` exactly, in backticks, once per row.
- Add one row for every declared method. Do not merge methods or invent IDs.
- Mark unsupported methods `Unsupported` and link an explanation instead of media.
- Use `Specialist only` when the delivery timeline has no equivalent operation.
- Link at least one local evidence file per row; anchors are allowed when the
  evidence is a section of the same README.
- Name presets and variants in a separate section and keep them aligned with the
  preset registry or script that defines them.
- For a leaf with no `methods.json`, add:
  `> This leaf has no `methods.json` manifest; the rows document the operations its `SKILL.md` exposes.`
- For a leaf with an empty `methods.json`, add:
  `> This leaf has an empty `methods.json` manifest; the row documents the operation its `SKILL.md` exposes.`

## Evidence rules

- GIFs for motion; before/after stills for picture methods; short MP3s only when
  audio is safe and meaningful; reports or command output for planning/workflow.
- Generate from synthetic cards, tones, or text-to-speech. Never commit private
  footage, private voice, credentials, licensed music, or delivery masters.
- Label the source and the rebuild command in the evidence file or README.
- Keep previews small and illustrative; they are not quality claims.

Run `npm run check:capabilities` after editing a matrix.
