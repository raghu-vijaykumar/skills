# Tasks: Timeline-first final rendering

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [contract](contracts/timeline.md)
**Tests**: Contract and synthetic-media tests are required for timing, approval, and single-export claims.

## Phase 1: Setup

- [X] T001 Create the canonical delivery-timeline skill, method registry, and script/test directories at content-studio/skills/content-studio-video/timeline/
- [X] T002 Document the new route and current compatibility boundary in content-studio/skills/content-studio-video/SKILL.md and README.md

## Phase 2: Foundation

- [X] T003 Implement strict versioned timeline schema, source identity, time-base and operation validation in content-studio/skills/content-studio-video/timeline/scripts/model.py
- [X] T004 Implement deterministic cut and overlap resolution, stable IDs, and immutable revision writes in content-studio/skills/content-studio-video/timeline/scripts/model.py
- [X] T005 Implement plan binding, asset fingerprinting, and human timeline-approval verification in content-studio/skills/content-studio-video/timeline/scripts/approval.py
- [X] T006 Add model/approval contract tests in content-studio/skills/content-studio-video/timeline/tests/test_model.py

## Phase 3: User Story 1 - Approve an entire edit

**Independent test**: A short source, cut, timed picture change, approved voice asset, and title produce no final output until exact plan/timeline approval; approved render produces one export.

- [X] T007 [US1] Add init, validate, fingerprint, and render CLI commands in content-studio/skills/content-studio-video/timeline/scripts/timeline.py
- [X] T008 [US1] Compile source clips and basic picture/audio tracks into one final export in content-studio/skills/content-studio-video/timeline/scripts/compiler.py
- [X] T009 [US1] Add explicit voice placement, source-audio mix, title, and output settings to the single export in content-studio/skills/content-studio-video/timeline/scripts/compiler.py
- [X] T010 [US1] Add end-to-end approval and encode-count tests using short generated media in content-studio/skills/content-studio-video/timeline/tests/test_delivery.py

## Phase 4: User Story 2 - Target ranges and ordering

**Independent test**: Approved cuts, denoise 1:00-10:00, upscale 2:00-2:15, transitions, audio effects, and graphics affect only the resolved ranges in one final output.

- [X] T011 [US2] Split picture processing at cut and effect boundaries and preserve source-to-output mapping in content-studio/skills/content-studio-video/timeline/scripts/compiler.py
- [ ] T012 [US2] Add typed geometry, denoise, deflicker, Lanczos/AI upscale, color, and sharpening adapters with explicit stage order in content-studio/skills/content-studio-video/timeline/scripts/adapters/
- [X] T013 [US2] Add supported point and join transitions with resolved duration and audio crossfades in content-studio/skills/content-studio-video/timeline/scripts/compiler.py
- [ ] T014 [US2] Add voice, music, SFX, cleanup, mastering, and timed graphics adapters in content-studio/skills/content-studio-video/timeline/scripts/adapters/
- [ ] T015 [US2] Add frame/audio sample checks around every selected range in content-studio/skills/content-studio-video/timeline/tests/test_delivery.py (boundary evidence is implemented; automated per-method assertions remain)

## Phase 5: User Story 3 - Revision path

**Independent test**: Changing any cue, asset, method, timing, or render setting creates a new version; the old approval fails and the new revision runs through the same export.

- [X] T016 [US3] Add revise command and immutable history in content-studio/skills/content-studio-video/timeline/scripts/timeline.py
- [X] T017 [US3] Add stale approval and changed asset regression tests in content-studio/skills/content-studio-video/timeline/tests/test_model.py
- [X] T018 [US3] Add render record and exact-output verification in content-studio/skills/content-studio-video/timeline/scripts/verify.py

## Phase 6: User Story 4 - Supported capability contract

**Independent test**: Every unsupported, missing, or incomplete operation fails validation before output; new methods need an adapter, test, and final-output evidence.

- [ ] T019 [US4] Inventory specialist methods and mark their delivery-timeline adapter readiness in content-studio/skills/content-studio-video/timeline/methods.json
- [X] T020 [US4] Add strict capability lookup and fail-before-encode behavior in content-studio/skills/content-studio-video/timeline/scripts/model.py
- [X] T021 [US4] Add unsupported/HDR/missing-asset tests in content-studio/skills/content-studio-video/timeline/tests/test_delivery.py
- [ ] T022 [US4] Update affected specialist SKILL.md files and workflow precheck text to distinguish preview methods from delivery-timeline methods
- [ ] T023 [US4] Route raw-clip preparation to analysis and optional labelled edit proxies, carrying permanent enhancement decisions into the delivery timeline in content-studio/skills/content-studio-video/source/preprocess/ and content-studio/skills/content-studio-workflow/scripts/preflight.py (analysis-only handoff implemented; source-to-manual-edit mapping remains)

## Final Phase: Validation and documentation

- [X] T024 Run focused and full relevant tests, docs check, and synthetic render pilot; record results in specs/013-timeline-first-render/quickstart.md
- [ ] T025 Review staged diff, commit only feature files, push main, and verify remote HEAD

## Dependencies

T001-T006 precede all story work. US1 establishes the export path. US2 extends its operation adapters. US3 extends the same CLI and approval gate. US4 validates adapter claims and can be refined as each adapter lands. T024-T025 follow all required implementation tasks.

## Implementation strategy

Build the plan/timeline/approval/render vertical slice first, then range and media adapters. Do not advertise a method as supported in the delivery timeline until its exact-final test passes. The full feature is complete only when all supported video and audio methods requested for an edit either run through the canonical timeline or are explicitly refused before approval.
