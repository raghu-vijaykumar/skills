# Tasks: Fast pan cuts

## Specify and integrate

- [x] T001 Add the independent fast-pan subskill instructions, manifest, and capability matrix under `content-studio/skills/content-studio-video/edit/fastpan-cuts/`.
- [x] T002 Update the edit router, README lifecycle, video capability index, and capability-count check.

## Implement

- [x] T003 Implement source-linked, read-only fast-pan scanning and candidate reports in `scripts/fastpan.py`.
- [x] T004 Implement frame-aligned cut-decision validation and bounded picture/audio preview in `scripts/fastpan.py`.
- [x] T005 Implement guarded native timeline changes export for human-approved ranges in `scripts/fastpan.py`.

## Verify and finish

- [x] T006 Add meaningful synthetic scan, cut-preview, stale-input, and timeline tests in `tests/test_fastpan.py`.
- [x] T007 Generate small synthetic method evidence and run focused tests, `npm run check:docs`, capability checks, and skill validation.
- [x] T008 Review the staged feature diff, commit to `main`, push, and verify the remote commit.
