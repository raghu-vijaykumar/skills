---
name: content-studio-video-archive
description: Back up public YouTube uploads and their exact metadata to Git, and sync durable media through rclone to Drive. Use for an independent on-demand channel archive run.
---

# Content Studio Archive

Read the channel's rules and the [channel toolkit](../../edit/clip-edit/references/channel-helper.md). Run `python <bundle>/skills/content-studio-videoedit/scripts/content.py backup --channel <slug>` for public YouTube copies, exact title/description/thumbnail, and source reconciliation. Run `python <bundle>/skills/content-studio-videoedit/scripts/content.py sync --channel <slug>` to push draft and shared media to Drive. Use `rclone check` evidence before pruning local media. Do not delete remote data.

This is independent of publication and may run monthly on request. Keep unpublished or scheduled videos in drafts. A public video moves to `shorts/` or `long/` only after the backup and Drive copy are verified; Git tracks the small source and metadata, while large media lives on Drive.
