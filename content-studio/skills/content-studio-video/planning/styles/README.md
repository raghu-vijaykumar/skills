# Styles capability matrix

List built-in and project-enabled styles, plan scene-aware treatments, validate
renderers, and generate reviewable style manifests. The committed plan and storyboard
are real outputs from the example scene input; no video frames are claimed.

**Status:** `Supported` means the skill manifest provides a runnable script. `Unsupported` means the manifest declares no script and this document makes no capability claim. **Delivery timeline:** `Yes` means the single-render delivery timeline consumes an equivalent operation; `Specialist only` means use this skill with a bounded preview and carry the approved result forward; `No` means unsupported or intentionally outside the one-render route. Previews are synthetic and illustrative, not delivery masters.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `list` | Supported | Installed bundle or videogen project → style and theme list | No | [Style list output](previews/list.json) | A project may enable only part of the built-in catalog; listing does not change presets. |
| `plan` | Supported | Topic/format/scenes JSON → style-plan.json with per-scene treatments | No | [Example plan](previews/example-style-plan.json) | Planning only; uninstalled renderers are warnings, not fabricated renders. |
| `storyboard` | Supported | style-plan.json → static storyboard.html | No | [Example storyboard](previews/example-storyboard.html) | Visualization of the plan, not video frames; review before generating assets. |

## Named styles and variants

The [style list output](previews/list.json) is the registry snapshot used for this
table. A project may enable only a subset; listing does not install a renderer.

| Variant | Formats | Use | Evidence |
| --- | --- | --- | --- |
| `core-explainer` | video, carousel, post | Mechanism-led technical explanations | [Treatment example](core-explainer/previews/treatment.md) |
| `evidence-lab` | video, carousel, post | Research-led investigations with firsthand captures | [Treatment example](evidence-lab/previews/treatment.md) |
| `hairline` | video | Narration-timed line-art animation | [Treatment example](hairline/previews/treatment.md) |
| `rapid-take` | video | Fast, evidence-led tech news | [Treatment example](rapid-take/previews/treatment.md) |
| `tech-dispatch` | carousel, post | Source-led technology posts | [Treatment example](tech-dispatch/previews/treatment.md) |

The seven selectable video-filter looks are `warm-golden`, `cool-cinematic`,
`vintage-fade`, `vibrant-travel`, `soft-portrait`, `mono-noir`, and `clean-natural`.
They are approximate FFmpeg grades, not copies of proprietary filters. Consistency
profiles are `travel-vlog`, `daily-vlog`, and `technical-explainer`.

**Integration limit:** `looks.py timeline` writes editable annotations, but the current
timeline renderer does not consume `creative_look` entries. Use `looks.py render` for
LUTs/feathered looks or `style_render.py` for post-export color, captions, and loudness.
Blender, FFmpeg, and native style adapters have not all been exercised end-to-end.

## Evidence note

All committed previews are generated from synthetic cards, tones, or text-to-speech, or are labelled command/output examples. No private footage, private voice, credentials, licensed music, or full masters are included.
