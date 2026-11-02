# Content Studio bundle

`skills/` contains eight installed entrypoints, each owning its own tooling. `skills/content-studio-videogen/` holds the reusable Remotion runtime and CLI. `skills/content-studio-videoedit/` holds the shared channel helper for backup, Drive sync, analytics, vlog ordering, preprocessing, and editing. `skills/content-studio-styles/hairline-source/` preserves upstream attribution and design material. `scripts/` provides installation, local transcription, the music library helper, and a common publication package gate. `assets/music/` holds the local-only YouTube Audio Library catalog; see [assets/music/README.md](assets/music/README.md).

Edit this folder in the skills repository, release one tag, then install that exact version in content projects. Do not edit global installed copies.
