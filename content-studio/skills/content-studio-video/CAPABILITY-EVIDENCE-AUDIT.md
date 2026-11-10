# Capability evidence audit — 2026-11-10

This reviews the committed examples for the Content Studio video skill tree.
Run `npm run check:capabilities` for the manifest/table contract and
`npm run check:docs` for links. The current checker reports **42 matrices,
111 declared methods, 6 unsupported methods, 29 named transitions, and 9
presets**. The matrices contain 137 rows including documented workflow rows.
A mechanical scan found 81 rows with a direct image/audio/video link and 56
without one. That count is only a link inventory: some rows link to a page or
section containing media, and a linked GIF does not prove a different renderer
used it.

## What the catalogue now demonstrates

| Area | Evidence | What it establishes |
| --- | --- | --- |
| Transitions | [29 named GIFs](edit/transitions/README.md) | The specialist catalogue has a distinct motion preview per named effect. |
| Timeline picture and audio | [15 method examples](timeline/previews/methods.md) | Actual bounded `model.validate` + `compiler.preview` output, with separate source/after media. |
| Restoration and upscale | [Restoration](edit/restoration/README.md), [upscale](edit/upscale/README.md) | Bounded specialist examples, including separate Lanczos and AI routes. |
| Color, reframe, and reflection | [Color](edit/color/README.md), [reframe](edit/reframe/README.md), [reflection](edit/reflection/README.md) | Actual method outputs with review limits; the saliency and reflection examples expose failure cases. |
| Clip editing and motion graphics | [Clip editing](edit/clip-edit/README.md), [motion graphics](edit/motion-graphics/README.md) | Distinct cut/join/trim and timed overlay examples. |
| Audio | [Source cleanup](audio/source-cleanup/README.md), [voice cloning](audio/voice-cloning/README.md) | Before/after cleanup samples; an actual IndicF5 sample explicitly failed its text gate. |
| Blur review | [Unapproved candidate](source/blur-review/README.md) | Actual scanner result and frame comparison, with no cut or simulated human approval. |
| Engineering 3D | [Blender GIF](animation/engineering-3d/README.md) | Actual Blender 4.5.15 render of synthetic authored components and camera events. |

All committed visual/audio previews are bounded. Published-source excerpts are
attributed in their evidence pages; synthetic inputs and deliberate defects
are labelled. A specialist preview is not proof of single-export timeline
equivalence or of an approved delivery master.

## Remaining evidence work

| Priority | Capability | Next evidence | Boundary |
| --- | --- | --- | --- |
| High | [Timeline transitions](timeline/README.md) | Render each point/join ID through the **timeline** adapter and compare 1.5-second windows, resolved duration, and audio overlap with the specialist preview. | Current transition GIFs show the specialist renderer; the timeline tests exercise every advertised ID, but no per-ID timeline GIF is committed. |
| High | [Remotion scene authoring](animation/videogen/scene-authoring/README.md) and [bounded render](animation/videogen/render/README.md) | Use an isolated synthetic project to render a hero frame, a moving detail beat, and a short narrated preview. | The current evidence is a scene specification and command contract, not rendered pixels. |
| Medium | [Carousel/post output](animation/videogen/content-output/README.md) | Render a registered synthetic carousel card and post GIF, then inspect every output at final size. | Needs a small installed project with a registered edition. |
| Medium | [Voice cloning](audio/voice-cloning/README.md) | Produce a synthetic-reference sample that passes transcription and human listening review before marking it approved. | The current actual sample fails the text gate; bundled human profiles are not new gallery inputs. |
| Medium | [HLG composition](edit/motion-graphics/README.md) | Show a short genuine HLG input and output with transfer metadata and visible overlay evidence. | Requires a reviewed HLG manifest and exact-output inspection. |
| Low | [Music selection](audio/music/README.md) | Show the local review player and a licensed, approved track selection when a production draft calls for it. | Do not commit third-party music or make a selection without human review. |

Rows for planning, validation, backup, publication, memory, or unsupported
methods appropriately use reports or command examples. `refine` selects and
records settings rather than producing a unique picture effect, so its report
contract remains the useful evidence. The one-render delivery claim remains
limited to methods the timeline validator and compiler actually consume.
