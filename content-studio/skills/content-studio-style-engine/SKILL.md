---
name: content-studio-style-engine
description: Plan scene-aware visual treatments inspired by educational, documentary, technical, and travel storytelling. Validate render capabilities and generate reviewable scene manifests without changing source footage.
---

# Content Studio Style Engine

Use this skill when the user asks for a recognizable visual storytelling treatment, hybrid style, or automatic style recommendation. This extends `content-studio-styles` (editorial registry) and `content-studio-motion-graphics` (vlog cue presets); it does not replace either.

## Workflow

1. Follow the human-reviewed precheck in `content-studio-workflow`. Read channel rules, project configuration, and source evidence.
2. Run `python scripts/style_engine.py list` to inspect supported treatments and renderer dependencies.
3. Prepare a JSON input containing `topic`, `format`, and `scenes` with `id`, `narration`, `duration_seconds`, optional `style`, `visual_intent`, and `evidence`.
4. Run `python scripts/style_engine.py plan input.json --output style-plan.json [--style auto]`. The plan selects treatments per scene, maps techniques to renderer requirements, and emits warnings for uninstalled renderers.
5. Review the plan with the user before generating assets. Do not claim a render was produced by this planning skill. Existing Remotion/Manim/Blender or motion-graphics pipelines must render the approved plan; unsupported effects are marked `needs_renderer`.
6. Produce short representative review clips, inspect first/middle/last frames and transitions, gather approvals, then create the editable timeline. Keep originals unchanged.

## Rules

- A creator name is shorthand for general techniques, not a request to copy proprietary character designs, distinctive branding, narration, or original artwork.
- Style and theme are separate: theme controls channel identity, style controls editorial treatment, renderer controls implementation.
- Avoid generic floating boxes when an actual spatial, mathematical, geographical, or physical visual can explain the concept.
- Match factual overlays to narration or visual evidence. Do not invent geographic locations, figures, or claims.
- Hybrid videos may vary style by scene but must preserve consistent typography, contrast, safe areas, and audio loudness.
- For Revise Labs, preserve existing channel character and 2.5D guidelines unless explicitly overridden.
- Missing tools must result in an explicit warning, not a fabricated rendered output.

## Commands

```bash
python content-studio/skills/content-studio-style-engine/scripts/style_engine.py list
python content-studio/skills/content-studio-style-engine/scripts/style_engine.py plan scenes.json --style auto --output style-plan.json
python -m unittest discover -s content-studio/skills/content-studio-style-engine/tests
```
