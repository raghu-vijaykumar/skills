---
name: content-studio-video-styles
description: List built-in and project-enabled Content Studio styles, then plan scene-aware visual treatments, validate renderers, and generate reviewable style and look manifests.
---

# Content Studio Styles

Use this skill to inspect the editorial style registry and to plan a visual storytelling treatment. It combines the style catalog with the style engine; it extends `content-studio-motion-graphics` (vlog cue presets) and does not replace it.

## List built-in styles

Run `node <this-skill>/scripts/list.mjs` to list the built-in styles available in the installed bundle. The script reads the runtime registry; `--json` gives structured output. Run `--themes` separately to list built-in channel identities. A theme supplies brand, color, and typography; a style supplies the editorial treatment and supported formats.

For a specific videogen project, run `npx --no-install videogen styles` from its root and read `videogen.config.ts`. Show which built-in styles are enabled by that project and include any custom styles registered in its config. A project may enable only part of the built-in catalog. If it has not installed its pinned package yet, use that project's normal install workflow before listing its enabled styles.

Present the result as style ID, name, use, formats, and whether it is enabled in the selected project. Note that Evidence Lab requires firsthand evidence, Rapid Take is the video-only satirical news style, Hairline is a video-only line-art animation style, and Tech Dispatch is carousel/post only. Read [themes and styles](../../animation/videogen/references/themes.md) for registration, [Rapid Take](../../animation/videogen/references/rapid-take.md) for the satirical video treatment, and [Hairline](../../animation/videogen/references/hairline.md) when that style is being considered. Record a chosen theme and style in the draft's creative metadata; listing styles does not change shared presets.

## Plan a treatment

1. Follow the human-reviewed precheck in `content-studio-workflow`. Read channel rules, project configuration, and source evidence.
2. Run `python scripts/style_engine.py list` to inspect supported treatments and renderer dependencies.
3. Prepare a JSON input containing `topic`, `format`, and `scenes` with `id`, `narration`, `duration_seconds`, optional `style`, `visual_intent`, and `evidence`.
4. Run `python scripts/style_engine.py plan input.json --output style-plan.json [--style auto]`. The plan selects treatments per scene, maps techniques to renderer requirements, and emits warnings for uninstalled renderers.
5. Generate a static review storyboard with `python scripts/storyboard.py style-plan.json --output storyboard.html`. This is a visualization of the plan, not video frames. Review the plan with the user before generating assets. Do not claim a render was produced by this planning skill. Existing Remotion/Manim/Blender or motion-graphics pipelines must render the approved plan; unsupported effects are marked `needs_renderer`.
6. Produce short representative review clips, inspect first/middle/last frames and transitions, gather approvals, then create the editable timeline. Keep originals unchanged.

## Engineering cutaway preset

Use `branch-education` or `engineering-cutaway` for component-level 3D technical explanations. Plan Blender scenes with exploded assemblies, selective transparency, isolated components, cross sections, and camera dollies. Require a physically meaningful component hierarchy and approved source references or modeled assets. Preserve spatial relationships and scale; never imply that a generic box or invented interior is a faithful engineering model. The optional Blender 4 renderer can now animate explicitly authored cuboid assemblies (exploded or assembled), transparency, highlights, and a dolly camera. It does not automatically infer accurate hardware geometry or implement arbitrary mesh cross-sections. Example:

```bash
blender -b --python content-studio/skills/content-studio-video/animation/engineering-3d/scripts/engineering_blender.py -- content-studio/skills/content-studio-video/animation/engineering-3d/examples/illustrative-cpu-assembly.json preview.mp4
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
python content-studio/skills/content-studio-video/planning/styles/scripts/style_engine.py list
python content-studio/skills/content-studio-video/planning/styles/scripts/style_engine.py plan scenes.json --style auto --output style-plan.json
python content-studio/skills/content-studio-video/planning/styles/scripts/storyboard.py style-plan.json --output storyboard.html
python -m unittest discover -s content-studio/skills/content-studio-video/planning/styles/tests
```

### Timeline events

Supply a `timeline` array in the Blender scene JSON. Component events use `{"time_seconds":2,"component":"Logic die (illustrative)","highlight":true,"opacity":0.5}`; camera events use `{"type":"camera","time_seconds":3,"position":[6,-9,6],"target":[0,0,0.5],"scale":8}`. Times are seconds from the scene start. For narration alignment, use externally generated cue timestamps; automatic speech alignment is not implemented. The example CPU assembly demonstrates these events. Blender renders and visual fidelity still require local verification.

## Selective video filter presets

This skill owns the look **choice**: the profile `look` value and the range files that decide which preset or LUT applies to which time. The preset catalog and all filter **application** — graph construction, HDR safety, and the FFmpeg render — live in `content-studio-videoedit` (`scripts/filters.py`). Available presets: `warm-golden`, `cool-cinematic`, `vintage-fade`, `vibrant-travel`, `soft-portrait`, `mono-noir`, `clean-natural`. These are approximate FFmpeg color grades, not copies of proprietary Instagram filters. Example:

```bash
python content-studio/skills/content-studio-video/edit/clip-edit/scripts/content.py filters list
python content-studio/skills/content-studio-video/edit/clip-edit/scripts/content.py filters render --input input.mp4 --ranges content-studio/skills/content-studio-video/planning/styles/examples/video-filter-ranges.json --output filtered.mp4
```

The ranges file uses `{"ranges":[{"start":3.5,"end":8.2,"preset":"warm-golden"}]}` with seconds relative to the input video's timeline. Ranges cannot overlap. Unselected video portions retain their original color values through the filter graph, although the entire video is re-encoded to H.264 SDR and may have minor compression differences. Audio is stream-copied when compatible with MP4. No automatic HDR/Dolby Vision handling, color-space conversion, crossfade between looks, or LUT import yet. Preview before accepting a grade; don't automatically apply filters to all scenes. This filter step should run after correction/shot matching, not as a replacement for them.

### Review a short color-filter preview

Use `--preview-start 3 --preview-duration 5` with `content.py filters render` to export only a 5-second segment. The filter ranges remain referenced to the original input timeline. The renderer rejects detected PQ/HLG or BT.2020 sources rather than silently treating HDR as SDR. Compare the preview with the source before approving a full-length export. The filter stage currently operates on a finished MP4, not the editable Content Studio timeline.

## Editable looks, LUTs and before/after previews

The `scripts/looks.py` CLI supports three modes: `timeline` annotates a **copy** of an existing Content Studio timeline JSON with `creative_look` enhancements and source/timeline timestamps; `render` applies graded looks to a finished SDR video; `compare` renders a short side-by-side original-versus-graded MP4.

```bash
python content-studio/skills/content-studio-video/planning/styles/scripts/looks.py --mode timeline --input edit-timeline.json --looks looks.json --output edit-timeline-with-looks.json
python content-studio/skills/content-studio-video/planning/styles/scripts/looks.py --mode render --input master.mp4 --looks looks.json --output graded.mp4
python content-studio/skills/content-studio-video/planning/styles/scripts/looks.py --mode compare --input master.mp4 --looks looks.json --output comparison.mp4 --start 4 --duration 5
```

The looks file uses `{"ranges":[{"start":3,"end":8,"preset":"warm-golden","fade":0.5},{"start":12,"end":18,"lut":"my-look.cube","fade":0.7}]}`. Times are in the final video timeline. LUT paths resolve relative to the looks JSON. Each range uses exactly one `preset` or `lut`, and non-overlapping ranges are required. Fade is applied at the beginning and end of each range. `compare` previews are limited to 30 seconds. Preserve the original input and require human review before using the output. The `timeline` mode stays in this skill; `render` and `compare` delegate graph construction and encoding to `content-studio-videoedit/scripts/filters.py`.

**Integration boundary:** The timeline command writes editable annotations but the existing Content Studio timeline renderer has **not yet been taught to consume** the new `creative_look` enhancement entries. For now, `render` is the supported path for applying looks to an exported master. Do not claim that editing the annotated timeline automatically changes the final render. Blender, FFmpeg and timeline integration have not been executed end-to-end.

## Style consistency engine

Use `scripts/style_consistency.py` to preserve channel identity across hybrid scenes while allowing purposeful per-scene editorial variations. Profiles: `travel-vlog`, `daily-vlog`, `technical-explainer`. Each specifies palette, font family, caption position, safe margins, transition, motion intensity, default look, loudness target, and maximum visual styles per video. Override only deliberate channel-level preferences with a JSON object.

```bash
python content-studio/skills/content-studio-video/planning/styles/scripts/style_consistency.py --profile travel-vlog --kind scenes --input style-plan.json --output consistent-plan.json --report consistency-report.json
python content-studio/skills/content-studio-video/planning/styles/scripts/style_consistency.py --profile travel-vlog --kind timeline --input edit-timeline.json --output styled-timeline.json
```

This stage audits explicit scene-level differences, adds `presentation` metadata to scenes and `style` metadata to video clips, and retains original files. The report flags identity drift and excessive style variety for review. **The existing video renderer does not yet consume these annotations automatically**; this is a planning and metadata consistency layer, not a claim of pixel-level or audio-level enforcement. Actual typography, grading, motion, and loudness still require downstream renderer integration and human review.

## Applying an approved profile to the exported video

`scripts/style_render.py` applies the profile's built-in color look to an SDR master; optionally burns in SRT/ASS captions with the profile's font, placement, and safe margin, and performs one-pass EBU R128 loudness normalization. The input master is never overwritten. The color graph and HDR safety check come from `content-studio-videoedit/scripts/filters.py`; caption styling and audio normalization stay here because they come from the style profile.

```bash
python content-studio/skills/content-studio-video/planning/styles/scripts/style_render.py --input master.mp4 --output styled.mp4 --profile travel-vlog
python content-studio/skills/content-studio-video/planning/styles/scripts/style_render.py --input master.mp4 --output styled-captioned.mp4 --profile technical-explainer --captions captions.srt --master-audio
```

The profile's **color, caption placement/font and loudness** now have a concrete post-export FFmpeg rendering path. Transition and motion intensity preferences still require native timeline/motion-graphics renderer adapters, and this does not yet integrate into the default `edit join` command. This is a single-pass color look, not per-shot color matching. Captions are optional and should not be generated for vlogs unless requested. The audio target is a one-pass approximation and requires listening/measurement review. Runtime testing is deferred.

## Native timeline rendering adapter

The canonical `content-studio-autocut/scripts/timeline.py` renderer now reads `timeline.style_profile.look` and optional `clip.style.look` to apply a built-in grade during per-clip FFmpeg rendering. Approved `clip.enhancements[]` entries with `stage: "creative_look"`, `preset`, `source_start`, and `source_end` are also consumed; unapproved looks are ignored. Explicit approved looks take precedence over the clip's default profile grade. The renderer includes style data in its cache hash.

**Scope:** Native renderer currently supports built-in EQ looks only. Imported LUTs, feathered per-section transitions, profile-based typography, transition effects, and motion graphics are not yet consumed by this native renderer. Use `looks.py render` for LUTs and feathered looks, or `style_render.py` for post-export subtitle styling and optional audio normalization. Rendering behavior and timestamp alignment are untested and require local validation before production use.

## Native creative-look adapter (additional support)

`content-studio-autocut/scripts/native_looks.py` is now imported by the canonical timeline renderer. Approved `creative_look` enhancements can specify either `preset` or a root-relative `.cube` LUT path plus `fade` in seconds; the renderer constructs per-clip FFmpeg blend graphs with fade-in/fade-out. Original footage is unchanged. The renderer keeps existing non-look enhancements in the graph.

This integration has **not been run against real media**. The native timeline still does not apply profile-based transitions, motion graphics, or caption styling. For caption placement and loudness, use the separate `style_render.py` post-export command. Review the final video and source-time alignment before production use.

## Native title motion and transitions

The canonical `content-studio-autocut/scripts/timeline.py` renderer now imports `style_motion.py`. The `style_profile` and optional per-clip `style` select `motion_intensity`, `font_family`, `palette`, `caption_position`, `safe_margin_percent`, and `transition`.

An explicit, approved clip-relative motion cue can be attached to a video clip:

```json
{"motion_graphics":[{"type":"title","text":"Dubai Day 3","start":1,"end":4,"review_status":"approved"}]}
```

The renderer draws a fading title overlay with the profile typography and placement. It does not invent titles or auto-generate overlays. `soft-cut` uses a brief fade-to-black at clip boundaries; `straight-cut` and `match-cut` remain hard cuts. This is **not** optical match-cut detection or a cross-dissolve between neighboring clips. The title renderer uses FFmpeg's `drawtext` filter and requires a build with drawtext/font support. Source audio is unaffected by video fades. Real-media tests and visual review are deferred.
