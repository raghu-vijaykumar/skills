# Feature Specification: Timeline-first final rendering

**Feature Branch**: `main` (user requested local main only)

**Created**: 2026-11-08

**Status**: In progress; bounded SDR delivery path implemented, specialist migration pending

**Input**: Plan, then create an editable timeline, obtain approval of the timeline, voice, edits, and effects, and render the final video and audio once. Revisions follow the same path.

## User Scenarios & Testing

### User Story 1 - Approve an entire edit before rendering (Priority: P1)

An editor starts with camera clips or a supplied manual edit, reviews a production plan, then reviews one timeline containing all requested picture, sound, voice, and graphic decisions before a final export begins.

**Why this priority**: The editor can see the complete edit and its estimated cost before committing to a long export.

**Independent Test**: Prepare a timeline for a short source with a cut, a timed picture adjustment, a voice asset, and a title. Show that no final media is created before approval, and that the approved revision yields one final media export.

**Acceptance Scenarios**:

1. **Given** a reviewed plan, **when** the timeline is created, **then** it lists source ranges, cuts, timed operations, voice and other audio assets, effects, order, expected duration, and output settings.
2. **Given** an unapproved timeline, **when** a final export is requested, **then** the export is refused without modifying source media.
3. **Given** approval of the exact plan and timeline revision, **when** export is requested, **then** all supported approved operations appear in the final picture and sound with one final video and audio rendering pass.
4. **Given** raw camera clips for a manual edit, **when** preparing the handoff, **then** diagnosis and optional edit proxies may run, but permanent enhancements are recorded for the eventual timeline instead of producing a chain of enhanced masters.

### User Story 2 - Target different ranges without repeated masters (Priority: P1)

An editor can remove approved blur spans, denoise 1:00–10:00, selectively upscale 2:00–2:15, and add transitions and voice without creating a new full-length intermediate master for each change.

**Why this priority**: Range targeting and one final export avoid needless full-video processing and generation loss.

**Independent Test**: A timed sample shows that the selected filters act only on the intended surviving frames, that the output canvas stays consistent, and that the final export decodes and encodes each used picture frame once.

**Acceptance Scenarios**:

1. **Given** approved cuts, **when** later effects are timed on the edited sequence, **then** their ranges are resolved against the resulting timeline and the original source ranges remain traceable.
2. **Given** overlapping denoise and upscale ranges, **when** the final video is rendered, **then** denoise precedes upscale in the overlap and neither effect is applied outside its approved range.
3. **Given** a transition with overlap, **when** its timing is approved, **then** the displayed duration and all later cue positions reflect that overlap before rendering.

### User Story 3 - Revise through the same approval path (Priority: P1)

After reviewing a preview or final export, the editor requests a change. The system creates a new timeline revision, refreshes timing and evidence, and seeks approval again before another final export.

**Why this priority**: A prior approval must never authorize a changed edit.

**Independent Test**: Change one voice cue or transition after approval and confirm that the old approval no longer permits rendering the new revision.

**Acceptance Scenarios**:

1. **Given** an approved timeline, **when** any edit, effect, asset, timing, or output setting changes, **then** the new revision is unapproved and the previous revision stays available.
2. **Given** an approved revised timeline, **when** export runs, **then** it follows the same validation and single-final-render path as the first export.

### User Story 4 - Handle unsupported operations honestly (Priority: P2)

The editor can see whether every planned operation has a timeline representation and a final renderer before approving costly work.

**Why this priority**: Silent omissions and surprise extra rendering passes make the final output unreliable.

**Independent Test**: Add an unavailable effect or missing voice asset and confirm that preflight names the exact problem and blocks final rendering.

**Acceptance Scenarios**:

1. **Given** an unsupported operation, **when** the timeline is validated, **then** validation names it and final rendering is refused; no replacement output is silently substituted.
2. **Given** a supported new enhancement, **when** it is introduced, **then** it can be planned, timed, approved, rendered, and verified through the same timeline path.

### Edge Cases

- Approved blur removal is a cut, never an automatic deletion; a cut may divide an enhancement range.
- A source clip can be reused at multiple timeline positions; a source-time effect must map to the intended occurrence.
- Missing source, changed source bytes, missing model, changed voice asset, or expired approval invalidates render readiness.
- Overlapping effects must have an explicit order, and conflicting effects must be rejected before rendering.
- A manual edit can be the picture source, but any later requested change must still enter the timeline.
- HDR/Dolby Vision, variable frame rate, and unsupported codecs require an explicit supported route; no implicit tone map or metadata loss.
- A short preview may render for review without granting final approval or creating a full intermediate master.

## Requirements

### Functional Requirements

- **FR-001**: Every production edit MUST follow plan → editable timeline → explicit human approval → final render.
- **FR-002**: The timeline MUST be the source of truth for picture cuts, source mapping, enhancements, transitions, graphics, voice placement, music, sound effects, audio processing, and output settings.
- **FR-003**: Each timed operation MUST identify its timeline range, affected track or clip, parameters, source or asset identity, review state, and execution order.
- **FR-004**: The system MUST resolve cuts and duration-changing transitions before presenting the timeline for approval and MUST show the resulting duration and cue positions.
- **FR-005**: Final approval MUST bind to the exact plan, timeline revision, input assets, and output settings. Any change MUST require a new approval.
- **FR-006**: A supported final render MUST apply all approved operations in their declared order while encoding each used delivered picture frame and audio sample once. It MUST NOT require a full-length intermediate master for each operation.
- **FR-007**: Bounded previews and reusable temporary inference or cache assets MAY be generated before final rendering. They MUST be distinguished from the final output and MUST NOT silently replace timeline operations.
- **FR-008**: The system MUST validate every operation and required asset before the final render, rejecting unsupported or incomplete entries rather than ignoring them.
- **FR-009**: A revision MUST create a new immutable timeline version and follow the same plan, approval, and render gates as the initial version.
- **FR-010**: The final rendered output MUST be checked against approved affected ranges, timing, audio sync, resolution, color handling, and enhancement side-effect criteria.
- **FR-011**: Source media and previous timeline versions MUST remain intact. Blur cuts and subjective picture or sound changes MUST retain human review.
- **FR-012**: New editing or enhancement capabilities MUST provide timeline representation, validation, rendering, review evidence, and final-output verification before being advertised as supported in this workflow.
- **FR-013**: Raw-clip preparation MUST carry selected permanent picture and audio changes forward as timeline instructions; optional edit proxies MUST be labelled as temporary and MUST NOT become an unreviewed final source.

### Key Entities

- **Production plan**: Reviewed operation choices, methods, estimates, fallbacks, and acceptance criteria.
- **Timeline revision**: Immutable version of source ranges, tracks, operations, timing, assets, and output settings.
- **Operation**: An approved or pending timed edit to picture or sound, with parameters and execution order.
- **Approval**: Human decision bound to exact plan, timeline, assets, and output settings.
- **Render record**: Final output identity, timeline revision, applied operation list, timing, and verification results.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In a representative edit containing cuts, range effects, voice, audio processing, graphics, and transitions, 100% of supported approved operations appear in one final export and no full-length intermediate master is created.
- **SC-002**: A 1:00–10:00 denoise range and 2:00–2:15 upscale range affect only the intended surviving frames, with frame-boundary accuracy at the delivery frame rate.
- **SC-003**: Every changed timeline revision or input asset invalidates the previous approval before export, in 100% of tested changes.
- **SC-004**: Every unsupported or incomplete operation is reported before final export; none is silently omitted.
- **SC-005**: A reviewer can inspect the planned duration, operation ranges, voice placement, and transition timing before approving both an initial edit and a revision.
- **SC-006**: A raw-clip handoff with three requested enhancements creates no full-length enhanced delivery master before the approved final timeline render.

## Assumptions

- Voice synthesis or recording can create an audio asset for review before final render; placing and mixing that asset into the video occurs at final render.
- The raw-camera workflow can still hand originals or edit proxies to the user for manual editing; permanent picture and audio enhancements are recorded on the eventual delivery timeline and applied at final render. AutoCut remains explicit-request-only.
- One final render means one delivery encode per output revision. Short previews and temporary model inference data are allowed.
- Publication and package approval remain separate from timeline and render approval.
