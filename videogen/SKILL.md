---
name: videogen
description: Build, validate, review, and export code-driven Remotion videos and related carousel or post editions in a project configured with videogen.config.ts.
---

# Videogen

Read `videogen.config.ts`, the target content, and the project's own creative rules before editing. The package owns the generic render and validation commands; the project owns its scenes, media, and channel identity. Use `npx videogen init <directory>` for a fresh project and `npx videogen sync-skill` after installing a pinned package version.

For narrated videos, generate cues with `npx videogen narration <id>` and time visible changes from those cues. Give each video a `video.compositionId` in `content/video.yaml`. Run `npx videogen check <id>`; it verifies that cached audio and cues match the authored narration. Inspect the composition in Remotion Studio, and render short evidence with `npx videogen render <id> --from <seconds> --to <seconds>`. Record actual frame and motion observations before calling the video complete. A full render is a delivery action: use `--delivery` only when the user requests one.

For carousel or post work, use `npx videogen content-check <id>` and `npx videogen content-render <id> --format carousel|post|all`, then inspect every exported card at delivery size. Keep source attribution and evidence manifests with project content.

Read [video workflow](references/video.md) for video creation and review, [post workflow](references/posts.md) for multi-format packages, and [themes](references/themes.md) when registering or changing a theme or style. A passing automated gate does not replace rendered-frame review.
