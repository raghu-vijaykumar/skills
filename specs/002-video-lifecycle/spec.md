# Feature Specification: channel video lifecycle

**Created:** 2026-10-26
**Status:** In progress

## User scenarios

### Draft to published backup

One folder under `content/revise-labs/drafts/` owns each unfinished video. A completed render is published to YouTube with its exact title, description, and thumbnail. Once the upload is publicly available, content-helper downloads YouTube's copy, records the actual public metadata, moves the draft source into that video's `shorts/` or `long/` folder, commits and pushes the small source/metadata files, and verifies the media and source archive on Drive.

### Next idea

The idea engine reads actual channel analytics and creates one draft folder with a research and packaging brief. It never claims measured performance without fetched data.

## Requirements

- Each public video folder contains a Git-tracked `title.txt`, `description.txt`, thumbnail, source code, and provenance connecting its YouTube ID and source revision. The binary video, generated audio, and fetched source media are ignored by Git and backed up to Drive.
- A scheduled/private upload remains in `drafts/` until public backup is verified. Backup reconciliation uses YouTube ID; title matching is a reviewed one-time migration aid only.
- Publishing is a reusable `videogen` command with a dry run and project-supplied YouTube credentials. It records the returned YouTube ID with the draft, so retries cannot silently create duplicate uploads.
- The Revise Labs channel assets, ReviseGuy, and unfinished cartoon work live with channel content. Reusable Remotion animation, Three, design, font, validation, and publishing logic live in `videogen`.
- Preserve every current authored and uncommitted video change during migration. Keep an explicit `pending-backup` state for a published video without a verified archive. Never claim historical source code is exact without evidence.
- A content repository can be installed from a clean checkout, work on a draft, commit/push code to its configured private Git remote, and sync all binary assets to its configured Drive remote.

## Acceptance

- The 76 source video folders are accounted for once: verified published, unpublished draft, or pending backup.
- Passing and failing tests cover backup metadata, draft ID reconciliation, Git selection, Drive verification, and publish duplicate prevention.
- A representative draft loads in Studio and renders a short range from the content repo; archived source stays independently inspectable.
- Package and skill checks pass; changes are selectively committed and pushed, with the content and skills Git remotes verified.
