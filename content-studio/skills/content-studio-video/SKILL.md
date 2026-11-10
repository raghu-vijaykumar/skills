---
name: content-studio-video
description: Route Content Studio video work through source preparation, manual-edit continuation, animation, review, and delivery.
---

# content-studio-video

A raw video folder defaults to [source preprocessing](source/preprocess/SKILL.md) for ordering and analysis, then stops for manual editing. A supplied manual render can enter [understanding](review/understand/SKILL.md) and bounded picture, voice, sound, transition, or graphic previews when requested. Permanent decisions belong in the [delivery timeline](timeline/SKILL.md) before human approval and final render. Code-driven work routes to [animation](animation/SKILL.md); its delivery adapter is still pending. [AutoCut](edit/autocut/SKILL.md) is experimental and explicit-request-only.

Reusable authored clips, CTA variants, memes, GIFs, and stickers route to the [stock library](stock-library/SKILL.md). The [memes skill](memes/SKILL.md) remains the contextual reaction catalogue and insertion route.

Before production editing, run the top-level [workflow precheck](../content-studio-workflow/SKILL.md) and obtain approval of the current plan, including exact operation, method script, output, estimate, fallback, and review criterion. Every child skill can be invoked directly and must follow that gate. Preserve originals and verify the exact output.

## Timeline-first delivery pilot

The [delivery timeline](timeline/SKILL.md) is the new approved plan -> timeline
-> human approval -> final render route. It currently supports source cuts,
range-targeted FFmpeg denoise/deflicker, Lanczos scale, basic color/sharpening,
a subset of transitions, titles, source audio, timed voice/music/SFX, and basic
audio filters. It does not yet support every specialist method, AI upscale,
HDR/Dolby Vision, or every motion-graphics preset. Validate a proposed timeline
before approval; an unsupported method must stop before export. The specialist
scripts remain available for diagnosis and bounded previews while their
delivery adapters are added. A revision repeats the same approval/render path.
