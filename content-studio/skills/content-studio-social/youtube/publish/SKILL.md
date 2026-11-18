---
name: content-studio-social-youtube-publish
description: Publish or schedule an approved Content Studio video to YouTube after its separate publication authorization.
---

# YouTube Publish

Use the existing [video publishing skill](../../../content-studio-video/delivery/publish/SKILL.md) and [publishing contract](../../../content-studio-video/animation/videogen/references/publishing.md). This leaf selects the YouTube route; it does not implement a second uploader.

Review the approved full master, title, description, thumbnail, credits and package hashes. Run `node <bundle>/scripts/cli.mjs publish --channel <slug> --draft <id>` for a dry run. For an independently configured Remotion project, the compatible route is `videogen publish <id>`. Only after an explicit request for that package use the confirmed YouTube command; `--at <ISO timestamp with offset>` selects native scheduling. Keep the returned video ID and receipt, and reconcile uncertain responses before retrying. Public backup and archive remain a separate [delivery operation](../../../content-studio-video/delivery/archive/SKILL.md).
