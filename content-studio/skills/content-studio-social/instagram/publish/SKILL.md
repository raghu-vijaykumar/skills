---
name: content-studio-social-instagram-publish
description: Publish an approved Content Studio Instagram Reel through the existing explicit-confirmation workflow.
---

# Instagram Publish

Use the existing [video publishing skill](../../../content-studio-video/delivery/publish/SKILL.md) and [publishing contract](../../../content-studio-video/animation/videogen/references/publishing.md). This leaf selects the Instagram Reel route; it does not implement a second uploader.

Review the approved portrait master, caption, package hashes and exact upload copy. Preview with `node <bundle>/scripts/cli.mjs publish --platform instagram --channel <slug> --draft <id>`. Only after a separate explicit publication request add `--confirm`. The existing publisher records the container and post IDs; uncertain `media_publish` results require account reconciliation before another attempt. Scheduling is not implemented by this route.
