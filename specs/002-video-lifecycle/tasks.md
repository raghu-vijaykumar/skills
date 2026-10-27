# Tasks

- [x] Inventory source videos and local YouTube backup; resolve a one-to-one migration map.
- [x] Copy all 76 Revise Labs video sources and channel assets into the content repository without losing local edits. Copy the separate Out of Office intro to its own channel drafts.
- [x] Git-track published title, description, thumbnail, source and provenance; exclude binary media. Verify all 75 migrated video.tsx files in a clean worktree.
- [x] Implement ID-based backup handoff and duplicate-safe reusable YouTube publishing.
- [x] Keep new idea briefs in one draft folder and validate representative draft composition and short render.
- [x] Tag and pin videogen-v0.2.2, install videogen, content-helper, and video-idea-engine globally, and push the skills and content repositories.
- [x] Verify clean Git-tag installation, a fresh neutral-theme scaffold and one-second render, the migrated Revise Labs draft check, and the 62-file Out of Office intro Drive copy.
- [x] Complete and verify the rclone binary-media copies. The personal client has Drive API access; `long` (431), `shorts` (2,137), `drafts` (1,323), shared assets (48), the external source cache (51), and `archive.txt` all match with 0 differences.
- [x] Remove obsolete Revise Labs copies after Drive verification, update the legacy repository documentation, and commit/push the cleanup. The runtime tests moved to the content repository, which now runs 301 tests (one media-dependent) and pins `videogen-v0.2.3`; a content package can resolve an archived video edition through `publishedDirs`.
