# Tasks: LinkedIn idea to post

## Foundations

- [x] T001 Extend social precheck and tests without changing existing video gates.
- [x] T002 Add durable draft contract, stage hashes and cross-chat status commands.

## P1: Intake and reviews

- [x] T003 Add LinkedIn skill instructions and personal workspace intake.
- [x] T004 Add angle, draft and final approval transitions and stale-input tests.

## P2: Media editions

- [x] T005 Add text, image, GIF, PDF document carousel and video package validation, distinguishing illustration from evidence.
- [x] T006 Support reusable project presets and per-post production methods; reuse content card and video tools as optional routes, documenting final-size review.

## P3: Direct publication

- [x] T007 Add OAuth connect and secret storage.
- [x] T008 Add versioned Posts/Images/Documents/Videos API publisher with dry run, receipts and retry guard.
- [x] T009 Test mock API success, access failure, expiry and uncertain responses.

## Finish

- [x] T010 Update public docs, run checks, review exact sample outputs, commit and push the coherent feature on `main`.

Dependency order: T001–T002, then T003–T006, then T007–T009, then T010. Each P1–P3 journey has a separate fixture-based acceptance test.
