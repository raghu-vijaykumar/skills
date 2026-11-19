---
name: content-studio-video-edit
description: Route optional edited-video operations, including AutoCut, clip editing, transitions, color, restoration, upscale, and motion graphics.
---

# content-studio-video-edit

The reusable [rising text behind subject preset](motion-graphics/references/text-behind-subject.md) is a native timeline graphic for one or several reviewed shots. Route a request for the linked travel-title edit directly there after precheck.

For explicitly requested captions, route to the canonical [captions skill](captions/SKILL.md). It prepares a reviewed ASS sidecar and pending timeline operation; ordinary vlogs have no caption step.

The default story edit is performed by the user. [Long cut](long-cut/SKILL.md) handles an explicit request to preserve source order and assemble all usable footage after reviewed blur, pan, and tilt removals; [AutoCut](autocut/SKILL.md) handles explicit story selection and is experimental. Use [fast pan cuts](fastpan-cuts/SKILL.md) to find and review rapid camera sweeps for removal, [tilt cuts](tilt-cuts/SKILL.md) for confirmed slanted-camera intervals, [clip edit](clip-edit/SKILL.md) for requested manual trims, [retime](retime/SKILL.md) for finite speed, freeze, reverse, and loop proposals, [object blur](object-blur/SKILL.md) for named-object concealment in a finished edit, and [transitions](transitions/SKILL.md), [reframe](reframe/SKILL.md), [color](color/SKILL.md), [restoration](restoration/SKILL.md), [upscale](upscale/SKILL.md), [reflection](reflection/SKILL.md), and [motion graphics](motion-graphics/SKILL.md) for diagnosis and bounded review candidates after the mandatory precheck. Permanent decisions enter the [delivery timeline](../timeline/SKILL.md) before separate human approval and one final render. Check its method registry before promising an effect; an unsupported adapter blocks final export. Each leaf skill is directly callable after its own approved precheck.

Use [clipping](clipping/SKILL.md) when one hero-led moment from a finished long-form video needs an editorial range, portrait framing, and source-audio handoff. Its source discovery and bounded crop proposals can inform precheck; emitting delivery changes requires the approved plan.
