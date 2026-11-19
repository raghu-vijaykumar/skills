---
name: content-studio-video-videogen
description: Create and review code-driven Remotion videos, including the Hairline animation style, in a videogen project. Use for scene authoring, narration timing, render checks, and visual review.
---

# Content Studio Animate

Before authoring or rendering a draft, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist.

For a narrated animation, fact-check and generate or record the complete narration before scene authoring. Listen to the whole track at normal speed and obtain human audio approval; written script review is optional for the editor. Lock the approved cue clock, then storyboard and animate to it. Iterate on bounded narrated previews with recorded scores, render and review the full video, apply requested edits, and rerender and rescore affected scenes before exact-master review. Regenerate audio approval and retime visuals if the voice changes.

For one draft at a time, use `npx videogen scaffold <id> --title "Working title"` to add a new video to an existing project, then `npx videogen studio <id>`. For an authored 16:9 long video, pass `--width 1920 --height 1080 --duration 300` (adjust the duration after narration). Scaffolding preserves an existing idea brief and refuses to replace authored scenes.

For an original motion-led explanation from an idea, read [idea to Core Explainer](references/idea-to-explainer.md). Use `--style core-explainer` to scaffold a frame-indexed scene and asset contract, then replace the starter with researched teaching beats. `videogen check` and `render` reject unsupported scenes, coverage gaps, missing media and changed asset hashes. When each scene owns one generated phrase, `videogen align-narration <id>` can lock speech to scene boundaries; listen to and reapprove any audibly changed full track before previewing scenes on its cues. A reference video remains research only; imported source frames or audio are not part of an authored reconstruction.

Read `videogen.config.ts`, the target content, and the project's own creative rules before editing. The package owns the generic render and validation commands; the project owns its scenes, media, and channel identity. Use `npx videogen init <directory>` for a fresh project and `npx videogen sync-skill` after installing a pinned package version.

For narrated videos, generate cues with `npx videogen narration <id>` and present the assembled full audio for listening approval before visual authoring. Time visible changes from the approved cues. Give each video a `video.compositionId` in `content/video.yaml`. Run `npx videogen check <id>`; it verifies that cached audio and cues match the authored narration. Inspect the composition in Remotion Studio, and render short evidence with `npx videogen render <id> --from <seconds> --to <seconds>`. Record actual frame and motion observations before calling the video complete. A full render is a delivery action: use `--delivery` only when the user requests one. Review that render before applying requested edits, then rerender and review the exact revision.

For carousel or post work, use `npx videogen content-check <id>` and `npx videogen content-render <id> --format carousel|post|all`, then inspect every exported card at delivery size. Keep source attribution and evidence manifests with project content.

Use `npx videogen source fetch <url> --slug <name>` to cache external article media under the configured `sourceCacheDir`. Use `npx videogen probe <render.mp4> <seconds> --design 1080x1920` for objective frame measurements, then inspect the actual frame visually. These tools take their paths and palette from the project config.

Use `content-studio-video-styles` to list built-in and project-enabled treatments. Read [video workflow](references/video.md) for video creation and review, [post workflow](references/posts.md) for multi-format packages, and [themes](references/themes.md) when registering or changing a theme or style. Read [Rapid Take](references/rapid-take.md) before authoring vivid, word-timed visuals or a fast satirical video. Core Explainer uses the shared assets, rigs and cue clock for deliberate mechanism walkthroughs. Verify the exact rendered frames after automated validation.

For a vlog composition, the package provides `VlogEffect` and `VlogTransition` at `@raghu-vijaykumar/videogen/runtime/vlogEffects`. Read the [motion-graphics effects guide](../../edit/motion-graphics/references/effects.md) for presets, timing, and audio responsibilities; render a short pilot before applying a transition throughout an edit.

For publication, switch to `content-studio-social-youtube-publish` or `content-studio-social-instagram-publish` and read [publishing](references/publishing.md). `npx videogen publish <id>` previews YouTube now; add `--platform instagram` to preview a Reel or `--at <future ISO>` to preview native YouTube scheduling. `--confirm` performs the requested action after checks and rendered review. Use `--resume` only for a recorded incomplete setup; never repeat an uncertain upload. Keep scheduled and private YouTube uploads in drafts until a public backup is verified by the channel's content-helper workflow.

The Hairline renderer is a video style, not an HTML handoff. Use [Hairline video style](references/hairline.md) for deterministic, narration-timed scenes and the source attribution.
