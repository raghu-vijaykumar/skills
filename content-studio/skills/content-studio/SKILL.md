---
name: content-studio
description: Route a Content Studio idea or supplied media through approved production, review, publication, and archive.
---

# Content Studio

For YouTube, LinkedIn or Instagram authoring, publishing or analytics, start with [Content Studio Social](../content-studio-social/SKILL.md). It separates platform operations while routing to the existing video and LinkedIn implementations. A personal LinkedIn idea goes to [Social LinkedIn Author](../content-studio-social/linkedin/author/SKILL.md).

For a standalone image or character illustration, use [Content Studio Image](../content-studio-image/SKILL.md). Its UI themes and character styles are listed in the skill README.

Start every production request, including a direct specialist request, with the mandatory [workflow precheck](../content-studio-workflow/SKILL.md). Inspect the channel, draft, source media, and system; present an editable plan with exact skill, method script, inputs, outputs, estimate, fallback, and review criterion. Obtain explicit approval of the current revision before editing, then record checklist evidence. Changed plans require reapproval.

For a raw camera folder, route to [video source preprocessing](../content-studio-video/source/preprocess/SKILL.md) and stop after handing off individual prepared clips and capture order for the user's manual edit. [AutoCut](../content-studio-video/edit/autocut/SKILL.md) is experimental and runs only on explicit request. Do not automatically join clips or remove blur spans.

When the user supplies a rendered manual edit, record its path and hash. Run only requested post-edit stages: [understand](../content-studio-video/review/understand/SKILL.md) for an evidence-linked voice script, [narration](../content-studio-video/audio/narration/SKILL.md) for approved voice and mix, [upscale](../content-studio-video/edit/upscale/SKILL.md) on the completed edit if justified, then [motion graphics](../content-studio-video/edit/motion-graphics/SKILL.md) on named scenes at delivery resolution. Review the exact master before a package can be approved.

For code-driven video, route through [styles](../content-studio-video/planning/styles/SKILL.md) and [videogen](../content-studio-video/animation/videogen/SKILL.md). [Ideagen](../content-studio-video/planning/ideagen/SKILL.md), [music](../content-studio-video/audio/music/SKILL.md), [memory](../content-studio-video/memory/SKILL.md), and other nested operation skills are independently callable when relevant.

When asked to judge a new cut against a creative reference, use [video critique](../content-studio-video/review/critique/SKILL.md). Map equivalent moments even when the cuts have different durations. Hand timecoded findings and rerender criteria to the relevant production skill.

Create or resume the lifecycle checklist with `python <this-skill>/scripts/checklist.py --channel <slug> --draft <id> --kind edited init` (use `remotion` for code-driven work). Record evidence per item, run `verify --phase pre_publish` before package approval and `verify --phase all` before closing. A direct specialist call follows the precheck but need not initialize the full lifecycle checklist. Read [the fixed lifecycle items](references/lifecycle-checklist.md).

[Social publication](../content-studio-social/SKILL.md) requires approved package hashes and a separate explicit user request. [Archive](../content-studio-video/delivery/archive/SKILL.md) is independent. Keep drafts, media, analytics, private voice assets, and credentials outside this skill bundle.
