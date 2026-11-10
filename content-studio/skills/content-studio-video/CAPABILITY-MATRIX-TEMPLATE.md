# Capability matrix template

Copy this structure into a leaf skill's `README.md`. Keep the six-column table so
the checker and readers see the same contract for every video capability.

## Required sections

1. A short description of the skill and what the committed evidence demonstrates.
2. The shared **Status** and **Delivery timeline** legend.
3. `## Capability matrix` with exactly the columns below.
4. Any named presets, variants, or profiles, checked against their registry.
5. `## Evidence note` naming the source of each example and its review status.

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

- Use an actual method output for each meaningful visual or audio capability:
  GIFs for every video before/after comparison (including picture changes),
  and short MP3s for audio. Stills may illustrate static diagnostics such as masks.
  A single example can cover two methods only if it visibly or audibly
  demonstrates both. Use reports or command output for planning/workflow.
- Synthetic cards, tones, and text-to-speech are suitable inputs. A bounded
  excerpt from an already published video may be used when its source is named.
  Never add private draft footage, new private voice recordings, credentials,
  licensed music, model weights, or full delivery masters to a gallery.
- Label the source, exact script/arguments, and rebuild route in the evidence
  file or README. Distinguish specialist output from delivery-timeline output.
- Mark failed, no-op, unsupported, and review-only examples explicitly; a
  successful encode does not prove the visual or audio result passed review.
- Keep previews small and illustrative; they are not final quality claims.

Run `npm run check:capabilities` after editing a matrix.
