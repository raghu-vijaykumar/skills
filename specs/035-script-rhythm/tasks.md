# Tasks: Script rhythm for Content Studio

## Phase 1: Setup

- [x] T001 Document the feature in `specs/035-script-rhythm/` and confirm the existing constitution and unrelated working-tree edits.

## Phase 2: Foundational

- [x] T002 Add focused analyzer tests in `content-studio/skills/content-studio-video/review/understand/tests/test_rhythm.py` for long runs, repeated openings, varied text, bilingual text, and optional timing.
- [x] T003 Implement the canonical analyzer and JSON-stdin CLI in `content-studio/skills/content-studio-video/review/understand/scripts/script_rhythm.py`.

## Phase 3: User Story 1 — edited voiceover

- [x] T004 [US1] Include advisory observations in `content-studio/skills/content-studio-video/review/understand/scripts/voiceover.py` without changing validation status or text.
- [x] T005 [US1] Test report and status compatibility in `content-studio/skills/content-studio-video/review/understand/tests/test_understand.py`.
- [x] T006 [US1] Update `content-studio/skills/content-studio-video/review/understand/references/voiceover.md` and its owning `SKILL.md` with format-aware drafting guidance.

## Phase 4: User Story 2 — code-driven narration

- [x] T007 [US2] Add a no-synthesis rhythm route and normal report refresh in `content-studio/skills/content-studio-video/animation/videogen/scripts/narration.mjs`.
- [x] T008 [US2] Test that route in `content-studio/skills/content-studio-video/animation/videogen/tests/script-rhythm.test.mjs`.
- [x] T009 [US2] Update narration-timing and narration-scoring guidance in `content-studio/skills/content-studio-video/animation/videogen/narration-timing/SKILL.md` and `content-studio/skills/content-studio-video/review/critique/references/narration-scoring.md`.

## Phase 5: Polish

- [x] T010 Run focused tests and `npm run check:docs`, review generated report evidence, and mark tasks complete in `specs/035-script-rhythm/tasks.md`.
- [x] T011 Stage only this feature, inspect the staged diff, commit, push, and verify the remote head.
- [x] T012 Record unconfirmed prompt specifics as `unknown` in vlog and code-driven narration guidance, with ticket status as an example.
