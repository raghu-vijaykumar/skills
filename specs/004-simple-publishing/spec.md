# Feature Specification: simple video publishing

**Created:** 2026-11-01
**Status:** In progress

## User scenarios

A configured content project can publish a reviewed draft to YouTube now, publish a portrait Reel to Instagram now, or upload a private YouTube video with a future native publish time. Each action defaults to a dry run. There is no local queue or background runner.

## Requirements

- Keep publishing logic and agent instructions in the reusable `videogen` package. Projects supply metadata, a full-length render, credentials, and optional storage paths through `videogen.config.ts`.
- The CLI accepts `videogen publish <id> [--platform youtube|instagram] [--at <future ISO>] [--confirm] [--resume]`. `--at` is YouTube-only. The default platform is YouTube.
- A confirmed action runs project validation and checks committed authored source. YouTube requires matching title and description files and a thumbnail. Instagram requires a valid caption and a compliant portrait Reel upload copy made from the committed master without altering it.
- Record remote IDs and source/render fingerprints in the draft manifest. Never silently repeat an upload or a possibly successful Instagram publish after an uncertain API response. Resume only the safe incomplete steps.
- Keep credentials ignored by Git. A dry run needs no credentials and makes no network request or media copy.
- Remove the retired queue implementation and publisher scripts from the legacy checkout after the new package is pinned in the active content project. Preserve the legacy checkout's unrelated local edits and historical documents as truthful archive notes.

## Acceptance

- Mocked passing and failing tests cover platform selection, invalid metadata/time, Instagram container processing, duplicate protection, uncertain publish response, and YouTube scheduling.
- A clean Git-tag install exposes the three publishing actions and the matching skill instructions.
- Skills and content checks pass, docs and staged diffs pass, and relevant changes are selectively committed and pushed to each configured remote.
