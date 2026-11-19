# Tasks: FFmpeg capabilities in Content Studio

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [operation handoffs](contracts/operation-handoffs.md)
**Organization**: Eight independently verifiable user stories. Existing Content Studio approvals and source preservation apply to every phase.

## Phase 1: Shared setup

- [ ] T001 Confirm current owning skills, references, method registries, and tests for all eight stories in `content-studio/skills/content-studio-video/` and `content-studio/skills/content-studio-workflow/`.
- [ ] T002 Record focused synthetic media commands and expected outcomes in `specs/038-ffmpeg-workflow-capabilities/quickstart.md`.

## Phase 2: User Story 1 - Diagnose media and machine

- [x] T003 [US1] Extend stream/display/timing probe in `content-studio/skills/content-studio-workflow/scripts/preflight.py`.
- [x] T004 [US1] Add selected-method FFmpeg component detection with available/missing/unknown results in `content-studio/skills/content-studio-workflow/scripts/preflight.py`.
- [x] T005 [US1] Cover multistream, VFR, and component-failure fixtures in `content-studio/skills/content-studio-workflow/tests/test_preflight.py`.
- [x] T006 [US1] Document the expanded precheck and selected-method gate in `content-studio/skills/content-studio-workflow/SKILL.md` and `references/planning.md`.

## Phase 3: User Story 2 - Check the exact master

- [ ] T007 [US2] Implement hash-bound format, loudness, content-candidate, and guide inspection in `content-studio/skills/content-studio-video/review/final-render/scripts/inspect.py`.
- [ ] T008 [US2] Bind inspection to timeline output review in `content-studio/skills/content-studio-video/timeline/scripts/verify.py` and `review/final-render/methods.json`.
- [ ] T009 [US2] Test known-defect, clean, intentional-content, and stale-output fixtures in `content-studio/skills/content-studio-video/review/final-render/tests/test_inspect.py`.
- [ ] T010 [US2] Document exact-master findings and review ownership in `content-studio/skills/content-studio-video/review/final-render/SKILL.md`.

## Phase 4: User Story 3 - Requested captions

- [ ] T011 [US3] Create canonical cue validation, font/safe-zone preview, and pending timeline handoff in `content-studio/skills/content-studio-video/edit/captions/scripts/captions.py`.
- [ ] T012 [US3] Add `content-studio-video-captions` skill, registry, and router references under `content-studio/skills/content-studio-video/edit/captions/` and `edit/SKILL.md`.
- [ ] T013 [US3] Verify exact cue timing, text, sidecar hash invalidation, and absent-by-default behavior in `content-studio/skills/content-studio-video/edit/captions/tests/test_captions.py`.

## Phase 5: User Story 4 - Separate recorder sync

- [ ] T014 [US4] Implement offset/drift/confidence analysis and bounded audition in `content-studio/skills/content-studio-video/source/sync/scripts/sync.py`.
- [ ] T015 [US4] Add canonical `content-studio-video-sync` skill, registry, and source router handoff in `content-studio/skills/content-studio-video/source/sync/` and `source/SKILL.md`.
- [ ] T016 [US4] Test delayed, drifting, silent, and ambiguous audio in `content-studio/skills/content-studio-video/source/sync/tests/test_sync.py`.
- [ ] T017 [US4] Add and validate a permanent manual-edit audio alignment adapter in `content-studio/skills/content-studio-video/timeline/scripts/model.py` and `compiler.py`.

## Phase 6: User Story 5 - Portrait framing evidence

- [ ] T018 [US5] Add subject coverage, motion-centre, crop-boundary, and destination guide evidence in `content-studio/skills/content-studio-video/edit/reframe/` and `edit/clipping/scripts/clipping.py`.
- [ ] T019 [US5] Cover lost hero and crop jump fixtures in `content-studio/skills/content-studio-video/edit/clipping/tests/test_clipping.py`.
- [ ] T020 [US5] Update framing review instructions in `content-studio/skills/content-studio-video/edit/clipping/SKILL.md` and `edit/reframe/SKILL.md`.

## Phase 7: User Story 6 - Measured final-mix loudness

- [ ] T021 [US6] Measure resolved mix and apply measured normalization in one final export in `content-studio/skills/content-studio-video/timeline/scripts/compiler.py`.
- [ ] T022 [US6] Verify exact output against approved loudness and true peak in `content-studio/skills/content-studio-video/timeline/scripts/verify.py`.
- [ ] T023 [US6] Test voice-plus-music, already-acceptable, and miss cases in `content-studio/skills/content-studio-video/timeline/tests/test_delivery.py`.
- [ ] T024 [US6] Document the timeline/standalone distinction in `content-studio/skills/content-studio-video/audio/mastering/SKILL.md` and `timeline/SKILL.md`.

## Phase 8: User Story 7 - Guarded smart cut

- [ ] T025 [US7] Implement cuts-only H.264 candidate with explicit source guards and boundary evidence in `content-studio/skills/content-studio-video/edit/clip-edit/scripts/`.
- [ ] T026 [US7] Test packet-copy, frame, and audio checks plus VFR/HDR/incompatible refusal in `content-studio/skills/content-studio-video/edit/clip-edit/tests/`.
- [ ] T027 [US7] Document comparison and accurate fallback in `content-studio/skills/content-studio-video/edit/clip-edit/SKILL.md` and its references.

## Phase 9: User Story 8 - Timeline retiming

- [ ] T028 [US8] Create canonical proposal and preview commands in `content-studio/skills/content-studio-video/edit/retime/scripts/retime.py` and its skill/registry.
- [ ] T029 [US8] Add finite speed, freeze, reverse, and loop validation and timing resolution in `content-studio/skills/content-studio-video/timeline/scripts/model.py`.
- [ ] T030 [US8] Compile all approved retime modes with explicit audio treatment into one export in `content-studio/skills/content-studio-video/timeline/scripts/compiler.py`.
- [ ] T031 [US8] Test frame order, durations, audio policies, downstream cue timing, and approval invalidation in `content-studio/skills/content-studio-video/timeline/tests/` and `edit/retime/tests/`.
- [ ] T032 [US8] Update routers and method documentation in `content-studio/skills/content-studio-video/edit/SKILL.md`, `content-studio/skills/content-studio-video/SKILL.md`, and `timeline/methods.json`.

## Phase 10: Cross-skill completion

- [ ] T033 Run `npm run check:docs` and relevant existing Python/Node suites; inspect exact rendered evidence where pixels or audio change.
- [ ] T034 Review staged feature diffs, commit complete slices to `main`, push to `origin`, and verify the pushed head.
- [ ] T035 Audit all eight user stories against `specs/038-ffmpeg-workflow-capabilities/spec.md` and record outcomes in a verification report in this feature directory.
