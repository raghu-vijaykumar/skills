# Tasks: Shot-aware SFX selection

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## US1 — Identify effects

- [x] T001 [US1] Add optional reviewed `sfx_profile` and `describe-sfx` CLI to `content-studio/skills/content-studio-video/stock-library/scripts/library.py`.
- [x] T002 [US1] Show profile and shot tag search in the private catalogue README.

## US2 — Suggest for shots

- [x] T003 [US2] Add deterministic shot manifest validation, tag and duration ranking, and a JSON proposal CLI.
- [x] T004 [US2] Document exact command binding to Content Studio Workflow and the separate timeline review.

## US3 — Keep rights gate

- [x] T005 [US3] Exclude reference-only media from delivery mode and mark reference proposals unavailable for placement.
- [x] T006 [US3] Add focused tests and update the skill method matrix and docs.

## Production catalogue

- [ ] T007 Run the mandatory precheck and obtain approval of the current tag update plan.
- [ ] T008 Apply editor-supported profiles to E01, E02, R05, and R18 and verify catalogue hashes, reference-only status, and selection proposals.
