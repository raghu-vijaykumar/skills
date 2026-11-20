# Feature Specification: Published Video Insights

**Feature Branch**: `main`
**Created**: 2026-11-20
**Status**: Implemented
**Input**: User request for agent-written Video Insights at channel and published-video scope, consumed by future edits.

## User Scenarios & Testing

### User Story 1 - Keep insights with published work (Priority: P1)

An editor prepares one channel Video Insights note and one note for each verified archived video. Notes show available measurements and preserve agent observations across report refreshes.

**Independent Test**: Prepare a synthetic archive twice with an authored edit between runs. Verify one channel note and one per-video note, with prose preserved.

**Acceptance Scenarios**:

1. Given verified archived videos, when preparation runs, then notes are keyed by stable video ID and unavailable metrics are labelled.
2. Given an authored note, when preparation repeats, then only the bounded measured-evidence section changes.
3. Given an indexed video pruned locally, when preparation repeats, then its identity and note remain.

### User Story 2 - Refresh reports and feedback (Priority: P2)

An editor refreshes existing owned YouTube reports and bounded viewer comments before preparing the notes. Unavailable access is reported without erasing cached evidence.

**Independent Test**: Stub report collectors and the comments endpoint; verify source status and partial failure.

**Acceptance Scenarios**:

1. Given working access, refresh updates the existing analytics store and comment evidence by published ID.
2. Given unavailable access, refresh reports the failed source and leaves prior evidence readable.

### User Story 3 - Use insights while editing (Priority: P3)

The agent reads channel and relevant published-video notes at planning and edit checkpoints, cites evidence for suggestions, and carries only approved changes into the existing plan and timeline.

**Independent Test**: Inspect the canonical route and confirm it names both scopes without adding draft insight files or bypassing precheck.

**Acceptance Scenarios**:

1. Given a new edit, relevant published insights inform outline, cut, narration, and package review.
2. Given no comparable evidence, the suggestion is labelled an editorial hypothesis.

### Edge Cases

- Local media can be pruned after backup; insight identity must survive.
- Cached reports can be stale; collection time is visible.
- Malformed note markers must fail without overwriting prose.
- A download ledger entry alone is not publication proof.

## Requirements

### Functional Requirements

- **FR-001**: Keep one agent-authored channel note and one note per verified published video, keyed by stable ID.
- **FR-002**: Preserve authored prose when measured evidence refreshes.
- **FR-003**: Separate observation, interpretation, suggested action, and uncertainty.
- **FR-004**: Reuse existing owned analytics, showing dates and missing fields honestly.
- **FR-005**: Retain verified identities after local pruning.
- **FR-006**: Collect bounded comments when authorized, without commenter identities.
- **FR-007**: Expose insights during planning; production edits still require human-approved precheck.
- **FR-008**: Keep notes and private analytics in the channel workspace, outside this skills repository.

### Key Entities

- **Published video**: Stable ID, channel, format, archive evidence, optional measurements.
- **Video Insights note**: Measured evidence block and agent-authored conclusions for one scope.
- **Source status**: Collection time and success, unavailable, or failure for each report source.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Repeat preparation preserves every authored note byte outside the evidence block.
- **SC-002**: A locally pruned indexed video retains a readable note.
- **SC-003**: One command refreshes available reports and prepares both note scopes, reporting partial failures.
- **SC-004**: A new edit can identify the channel note and supporting published-video notes before plan approval.
