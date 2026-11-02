# Content Studio skill names

**Created:** 2026-11-02

## Contract

All discoverable lifecycle skills use the `content-studio-` family. `content-studio` routes to `content-studio-ideagen`, `content-studio-videogen`, `content-studio-videopreprocess`, `content-studio-videoedit`, `content-studio-publish`, and `content-studio-archive`. Preprocessing ends at reviewed camera clips; editing covers trim/cut/join, manual-export review, transcription, captions, and thumbnail proposal.

The canonical source stays under `content-studio/skills/`. A versioned global install discovers exactly seven entrypoints and removes only managed links for superseded names. A content project keeps the existing videogen package name, CLI, and imports, but `sync-skill` installs `content-studio-videogen` and removes its prior managed local copy. Release a new immutable tag and pin it in the channel repository. Preserve all existing video folders and scenes.

## Acceptance

Seven skill frontmatter names match their folders; docs links resolve; global and project skill discovery contain no superseded names. Ordered preprocessing and edit commands remain available. Local multilingual transcription produces actual caption and frame artifacts. Clean tagged npm install, repository tests, content checks, and remote heads pass.
