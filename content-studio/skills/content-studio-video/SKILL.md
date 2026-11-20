---
name: content-studio-video
description: Route Content Studio video work through source preparation, manual-edit continuation, animation, review, and delivery.
---

# content-studio-video

A raw video folder defaults to [source preprocessing](source/preprocess/SKILL.md) for ordering and analysis, then stops for manual editing. An explicit request to assemble all usable footage in order after reviewed technical removals routes to [long cut](edit/long-cut/SKILL.md). A supplied manual render can enter [understanding](review/understand/SKILL.md) and bounded picture, voice, sound, transition, or graphic previews when requested. Permanent decisions belong in the [delivery timeline](timeline/SKILL.md) before human approval and final render. Code-driven work routes to [animation](animation/SKILL.md); its delivery adapter is still pending. [AutoCut](edit/autocut/SKILL.md) is experimental and explicit-request-only.

For a configured channel, read [Video Insights](planning/video-insights/SKILL.md) from its published archive before planning a new video or improving an edit. Use the channel patterns and relevant per-video evidence as suggestions at outline, cut, narration, and package review. Keep the insight history outside drafts and retain the normal production approval gate.

For a narrated vlog, review and approve the picture video first. Prepare and obtain listening approval of the complete narration audio, place that voice on the picture, review the voiced video, then add requested motion graphics or ASS overlays and review the final render. For narrated animation, approve the full audio by listening before visual authoring; animate and score on that cue clock, review the full render, apply requested edits, and review the revised master. Keep the written narration as internal evidence unless the editor asks for it.

A request to make a hero-led portrait Reel or Short from one finished long-form passage routes to [clipping](edit/clipping/SKILL.md). It reviews the story range and crop, then hands pending edits to the timeline. Simple trims remain in [clip edit](edit/clip-edit/SKILL.md), finite speed/freeze/reverse/loop changes route to [retime](edit/retime/SKILL.md), and crop-only requests remain in [reframe](edit/reframe/SKILL.md).

Reusable authored clips, CTA variants, memes, GIFs, and stickers route to the [stock library](stock-library/SKILL.md). The [object blur skill](edit/object-blur/SKILL.md) finds a named target in a finished edit and requires full-frame coverage review before concealment export. The [SFX skill](audio/sfx/SKILL.md) supplies the pinned Earshot bank, creation, audition, and evidence-linked cue proposals for edited and code-driven video. Public Instagram Reel sound-effect sourcing routes to [reel SFX](audio/reel-sfx/SKILL.md), with unknown-rights audio kept reference-only in the stock catalogue. The [memes skill](memes/SKILL.md) remains the contextual reaction catalogue and insertion route.

Before production editing, run the top-level [workflow precheck](../content-studio-workflow/SKILL.md) and obtain approval of the current plan, including exact operation, method script, output, estimate, fallback, and review criterion. Every child skill can be invoked directly and must follow that gate. Preserve originals and verify the exact output.

## Timeline-first delivery pilot

The [delivery timeline](timeline/SKILL.md) is the new approved plan -> timeline
-> human approval -> final render route. It currently supports source cuts,
range-targeted FFmpeg denoise/deflicker, finite retiming, Lanczos scale, basic color/sharpening,
a subset of transitions, titles, source audio, timed voice/music/SFX, and basic
audio filters. It does not yet support every specialist method, AI upscale,
HDR/Dolby Vision picture processing, or every motion-graphics preset. An audio-only supplied HDR/Dolby Vision edit can copy verified picture packets while mixing approved audio. Validate a proposed timeline
before approval; an unsupported method must stop before export. The specialist
scripts remain available for diagnosis and bounded previews while their
delivery adapters are added. A revision repeats the same approval/render path.
