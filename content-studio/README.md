# Content Studio bundle

Current skill entrypoints live in [skills](skills/); [PROPOSED_FOLDER_STRUCTURE.md](PROPOSED_FOLDER_STRUCTURE.md) describes a future layout and workflow. The proposed folders and scripts do not exist yet.

## Gates

Before any production edit, use [content-studio-workflow](skills/content-studio-workflow/SKILL.md) to inspect the source and system, name methods and outputs, estimate time, and obtain approval of an editable plan. Record evidence against its checklist. Changed plans require fresh approval; publishing needs separate authorization. Preserve originals and review the exact delivered master.

## Proposed camera-footage default

1. Raw video folder → approved ordering, deduplication, and source cleanup → hand off individual prepared clips for **manual editing**.
2. User supplies the rendered edit → optional evidence-linked [voice script](skills/content-studio-understand/SKILL.md), approved [voice](skills/content-studio-voice/SKILL.md), and mix.
3. If warranted, compare and upscale the **completed edit after voice**. Then render requested [code-generated overlays](skills/content-studio-motion-graphics/SKILL.md) on named scenes at delivery resolution.
4. Review final picture and audio, approve the package, then [publish](skills/content-studio-publish/SKILL.md) only on explicit request. [Archive](skills/content-studio-archive/SKILL.md) is independent.

[AutoCut](skills/content-studio-autocut/SKILL.md) is experimental and runs only on explicit request in the proposal. The current [router](skills/content-studio/SKILL.md), [preprocessor](skills/content-studio-videopreprocess/SKILL.md), and [upscale tool](skills/content-studio-videoedit/SKILL.md) still contain older routes; the proposed default and integrated voice mix are not yet implemented. [Prompt templates](prompts/) are examples and need review against the approved plan; `full-vlog.md` currently enables AutoCut by default.

## Other production

For code-driven video, use [styles](skills/content-studio-styles/SKILL.md) and [videogen](skills/content-studio-videogen/SKILL.md) to plan scenes, render bounded evidence, review, and render the full delivery. [Music](skills/content-studio-music/SKILL.md), [audio](skills/content-studio-audio/SKILL.md), [benchmark](skills/content-studio-benchmark/SKILL.md), [memes](skills/content-studio-memes/SKILL.md), and [memory](skills/content-studio-memory/SKILL.md) are specialist tools, not automatic steps.

Edit this repository as the source of truth, tag a tested version, and install that version in content projects. Keep drafts, media, analytics, voice samples, and secrets outside the bundle.
