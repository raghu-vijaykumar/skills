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
5. Generate a static review storyboard with `python scripts/storyboard.py style-plan.json --output storyboard.html`. This is a visualization of the plan, not video frames. Review the plan with the user before generating assets. Do not claim a render was produced by this planning skill. Existing Remotion/Manim/Blender or motion-graphics pipelines must render the approved plan; unsupported effects are marked `needs_renderer`.
6. Produce short representative review clips, inspect first/middle/last frames and transitions, gather approvals, then create the editable timeline. Keep originals unchanged.

## Engineering cutaway preset

Use `branch-education` or `engineering-cutaway` for component-level 3D technical explanations. Plan Blender scenes with exploded assemblies, selective transparency, isolated components, cross sections, and camera dollies. Require a physically meaningful component hierarchy and approved source references or modeled assets. Preserve spatial relationships and scale; never imply that a generic box or invented interior is a faithful engineering model. The optional Blender 4 renderer can now animate explicitly authored cuboid assemblies (exploded or assembled), transparency, highlights, and a dolly camera. It does not automatically infer accurate hardware geometry or implement arbitrary mesh cross-sections. Example:

```bash
blender -b --python content-studio/skills/content-studio-style-engine/scripts/engineering_blender.py -- content-studio/skills/content-studio-style-engine/examples/illustrative-cpu-assembly.json preview.mp4
```

For imported geometry, supply a component with `asset` (relative to the scene JSON), `name`, `position`, and `explode_offset`; GLB, glTF, and FBX are supported. Each imported asset is parented to a transform controller, enabling assembly/explosion while preserving the mesh hierarchy. Timeline-driven imported material opacity and highlighting are supported through `timeline` events (subject to the imported mesh's Principled BSDF materials). The imported asset's own scale and coordinate origin determine its appearance. Review the rendered video before publication. Do not describe the sample geometry as a real CPU interior.

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
python content-studio/skills/content-studio-style-engine/scripts/storyboard.py style-plan.json --output storyboard.html\npython -m unittest discover -s content-studio/skills/content-studio-style-engine/tests
```

### Timeline events

Supply a `timeline` array in the Blender scene JSON. Component events use `{"time_seconds":2,"component":"Logic die (illustrative)","highlight":true,"opacity":0.5}`; camera events use `{"type":"camera","time_seconds":3,"position":[6,-9,6],"target":[0,0,0.5],"scale":8}`. Times are seconds from the scene start. For narration alignment, use externally generated cue timestamps; automatic speech alignment is not implemented. The example CPU assembly demonstrates these events. Blender renders and visual fidelity still require local verification.

## Selective video filter presets

Use `scripts/video_filters.py` for optional creator-neutral, Instagram-like color looks on **only selected time ranges** of an existing SDR video. Available presets: `warm-golden`, `cool-cinematic`, `vintage-fade`, `vibrant-travel`, `soft-portrait`, `mono-noir`, `clean-natural`. These are approximate FFmpeg color grades, not copies of proprietary Instagram filters. Example:

```bash
python content-studio/skills/content-studio-style-engine/scripts/video_filters.py list
python content-studio/skills/content-studio-style-engine/scripts/video_filters.py render --input input.mp4 --ranges content-studio/skills/content-studio-style-engine/examples/video-filter-ranges.json --output filtered.mp4
```

The ranges file uses `{"ranges":[{"start":3.5,"end":8.2,"preset":"warm-golden"}]}` with seconds relative to the input video's timeline. Ranges cannot overlap. Unselected video portions retain their original color values through the filter graph, although the entire video is re-encoded to H.264 SDR and may have minor compression differences. Audio is stream-copied when compatible with MP4. No automatic HDR/Dolby Vision handling, color-space conversion, crossfade between looks, or LUT import yet. Preview before accepting a grade; don't automatically apply filters to all scenes. This filter step should run after correction/shot matching, not as a replacement for them.

### Review a short color-filter preview

Use `--preview-start 3 --preview-duration 5` with the `video_filters.py render` command to export only a 5-second segment. The filter ranges remain referenced to the original input timeline. The tool rejects detected PQ/HLG or BT.2020 sources rather than silently treating HDR as SDR. Compare the preview with the source before approving a full-length export. The filter stage currently operates on a finished MP4, not the editable Content Studio timeline.

## Editable looks, LUTs and before/after previews

The `scripts/looks.py` CLI supports three modes: `timeline` annotates a **copy** of an existing Content Studio timeline JSON with `creative_look` enhancements and source/timeline timestamps; `render` applies graded looks to a finished SDR video; `compare` renders a short side-by-side original-versus-graded MP4.

```bash
python content-studio/skills/content-studio-style-engine/scripts/looks.py --mode timeline --input edit-timeline.json --looks looks.json --output edit-timeline-with-looks.json
python content-studio/skills/content-studio-style-engine/scripts/looks.py --mode render --input master.mp4 --looks looks.json --output graded.mp4
python content-studio/skills/content-studio-style-engine/scripts/looks.py --mode compare --input master.mp4 --looks looks.json --output comparison.mp4 --start 4 --duration 5
```

The looks file uses `{"ranges":[{"start":3,"end":8,"preset":"warm-golden","fade":0.5},{"start":12,"end":18,"lut":"my-look.cube","fade":0.7}]}`. Times are in the final video timeline. LUT paths resolve relative to the looks JSON. Each range uses exactly one `preset` or `lut`, and non-overlapping ranges are required. Fade is applied at the beginning and end of each range. `compare` previews are limited to 30 seconds. Preserve the original input and require human review before using the output.

**Integration boundary:** The timeline command writes editable annotations but the existing Content Studio timeline renderer has **not yet been taught to consume** the new `creative_look` enhancement entries. For now, `render` is the supported path for applying looks to an exported master. Do not claim that editing the annotated timeline automatically changes the final render. Blender, FFmpeg and timeline integration have not been executed end-to-end.

## Style consistency engine

Use `scripts/style_consistency.py` to preserve channel identity across hybrid scenes while allowing purposeful per-scene editorial variations. Profiles: `travel-vlog`, `daily-vlog`, `technical-explainer`. Each specifies palette, font family, caption position, safe margins, transition, motion intensity, default look, loudness target, and maximum visual styles per video. Override only deliberate channel-level preferences with a JSON object.

```bash
python content-studio/skills/content-studio-style-engine/scripts/style_consistency.py --profile travel-vlog --kind scenes --input style-plan.json --output consistent-plan.json --report consistency-report.json
python content-studio/skills/content-studio-style-engine/scripts/style_consistency.py --profile travel-vlog --kind timeline --input edit-timeline.json --output styled-timeline.json
```

This stage audits explicit scene-level differences, adds `presentation` metadata to scenes and `style` metadata to video clips, and retains original files. The report flags identity drift and excessive style variety for review. **The existing video renderer does not yet consume these annotations automatically**; this is a planning and metadata consistency layer, not a claim of pixel-level or audio-level enforcement. Actual typography, grading, motion, and loudness still require downstream renderer integration and human review.
