# Content Studio

Editable source for the Content Studio skill bundle and `@raghu-vijaykumar/videogen` Remotion runtime. The installed skills live in [content-studio/skills](content-studio/skills/); [the proposed folder structure](content-studio/PROPOSED_FOLDER_STRUCTURE.md) is a design document, not the current implementation.

## Production rules

- Start every production edit, including direct specialist calls, with the [workflow precheck](content-studio/skills/content-studio-workflow/SKILL.md). Inspect the source and machine, name the exact methods, estimate time, show an editable plan, and obtain approval of that revision. Record evidence against its checklist; plan changes require fresh approval.
- Preserve camera originals and project edits. Diagnose each issue, compare a bounded fix with leaving it alone, and verify the delivered result. Blur is for review, not automatic deletion. Dolby Vision needs a reviewed preservation or tone-map route.
- Approve scripts, voice, subjective visual changes, the final package, and publication at their respective gates. Publishing requires a separate explicit request.

## Proposed camera-footage path

These are the intended defaults in [the proposal](content-studio/PROPOSED_FOLDER_STRUCTURE.md#default-camera-footage-workflow-and-paths). They are **not yet wired together in the current skills**.

| Trigger | Route | Handoff |
| --- | --- | --- |
| Raw video folder | Precheck, inspect, order, deduplicate, and apply only approved source cleanup. | Individual clips in `drafts/<id>/.content-studio/processed-clips/`; user edits them. |
| User supplies manual render | Record its path and hash; review the actual edit. | `drafts/<id>/<id>-manual-edit.mp4` or the supplied path. |
| User requests narration | Draft an evidence-linked, timed script from the render; review it, then generate and mix approved voice. Cloning requires consent and a listening check. | `.content-studio/understanding/`, then `.content-studio/voice/`. |
| Higher resolution is justified | Compare untouched, Lanczos, and AI ranges on the completed edit after voice; upscale only that edit when approved. | `.content-studio/upscale/` or an unchanged master. |
| User requests scene graphics | Cue only named scenes; render code-generated overlays at delivery resolution **after** any upscale. | `.content-studio/motion-graphics/`, then reviewed `<id>-final.mp4`. |
| User requests publication | Review the full master, metadata, thumbnail, rights, and package; obtain separate publication authorization. | Platform receipt; archive runs separately. |

AutoCut is an **experimental, explicit-request-only** alternative in this proposal. It is not part of a raw-folder handoff. The current [lifecycle router](content-studio/skills/content-studio/SKILL.md), [preprocessor](content-studio/skills/content-studio-videopreprocess/SKILL.md), and [upscale guidance](content-studio/skills/content-studio-videoedit/references/upscale.md) still describe older automatic rough-cut, joined-clip, or per-clip upscale routes. Current [voice](content-studio/skills/content-studio-voice/SKILL.md) synthesizes narration but does not yet provide the proposed integrated video mix.

## Other routes and current tools

| Need | Current entrypoint |
| --- | --- |
| Full lifecycle and precheck | [Router](content-studio/skills/content-studio/SKILL.md), [workflow](content-studio/skills/content-studio-workflow/SKILL.md) |
| Research and visual treatment | [Idea research](content-studio/skills/content-studio-ideagen/SKILL.md), [styles](content-studio/skills/content-studio-styles/SKILL.md) |
| Code-driven video, carousel, or post | [Videogen](content-studio/skills/content-studio-videogen/SKILL.md): author scenes, render bounded evidence, review, then render delivery |
| Camera source and manual edit support | [Preprocess](content-studio/skills/content-studio-videopreprocess/SKILL.md), [video edit](content-studio/skills/content-studio-videoedit/SKILL.md) |
| Edited-render analysis, narration, graphics | [Understand](content-studio/skills/content-studio-understand/SKILL.md), [voice](content-studio/skills/content-studio-voice/SKILL.md), [motion graphics](content-studio/skills/content-studio-motion-graphics/SKILL.md) |
| Optional production aids | [AutoCut](content-studio/skills/content-studio-autocut/SKILL.md), [audio](content-studio/skills/content-studio-audio/SKILL.md), [music](content-studio/skills/content-studio-music/SKILL.md), [benchmark](content-studio/skills/content-studio-benchmark/SKILL.md), [memes](content-studio/skills/content-studio-memes/SKILL.md), [memory](content-studio/skills/content-studio-memory/SKILL.md) |
| Release | [Publish](content-studio/skills/content-studio-publish/SKILL.md), [archive](content-studio/skills/content-studio-archive/SKILL.md) |

The [prompt templates](content-studio/prompts/) are examples, not executable workflow contracts. Review their switches and the approved precheck plan before using one. In particular, [full-vlog.md](content-studio/prompts/full-vlog.md) still enables AutoCut and several later stages by default, so it does not express the proposed manual-edit path.

## Draft and installation

A camera draft lives at `<workspace>/<channel>/drafts/<id>/`: `original/` retains footage, `.content-studio/` holds working evidence, and root `<id>-final.mp4` is the reviewed master. Vlog transcripts and captions are not generated by default. Derive metadata from sampled frames and audio context. The [lifecycle checklist](content-studio/skills/content-studio/references/lifecycle-checklist.md) records gate evidence.

Install the current bundle with `node content-studio/scripts/cli.mjs install-skills --global`. Projects can pin a tested Git tag and run `npx videogen sync-skill`; start a Remotion project with `npx videogen init <directory>`. Validate documentation with `npm run check:docs`. Content drafts, media, analytics, voice samples, and secrets belong outside this skill repository.
