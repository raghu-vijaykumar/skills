# Feature Specification: Hero-led clipping from long-form video

**Feature Branch**: `main`
**Created**: 2026-11-19
**Status**: Planning
**Input**: Create a Content Studio clipping skill that selects a particular section of a long-form video where the scene's hero is present and turns it into a short-form Reel.

## User Scenarios & Testing

### User Story 1 - Select the moment (Priority: P1)

An editor supplies a finished long-form video and identifies the hero by a description or a rough timestamp. The skill shows timestamped source evidence and proposes one contiguous range with a complete opening, hero action, and ending. The editor can change the range before production.

**Independent Test**: Given a source with two plausible moments, the editor can identify the desired one, inspect its original picture and sound, and save exact start and end times tied to the source file.

**Acceptance Scenarios**:

1. **Given** a rough timestamp, **when** the editor requests a Reel, **then** the review presents that neighborhood with source timestamps and an editable range.
2. **Given** no timestamp, **when** the editor describes the hero, **then** timestamped contact sheets support a human search; the skill does not claim that sparse sampling proves the hero is absent elsewhere.
3. **Given** an incomplete spoken sentence or action at a proposed boundary, **when** the editor reviews it, **then** the range is adjusted or left pending review.

### User Story 2 - Keep the hero readable in portrait (Priority: P2)

The editor compares a 9:16 crop with the original scene and approves a framing that preserves the important person, object, or mechanism and its action. A crop that loses the hero is flagged for revision.

**Independent Test**: The editor can review source and crop side by side at the start, middle, end, and motion changes of the selected range.

**Acceptance Scenarios**:

1. **Given** a hero that stays within one crop, **when** the crop is previewed, **then** the approved crop geometry can be carried to the delivery timeline.
2. **Given** a hero that leaves the crop, **when** the preview is inspected, **then** the skill proposes shorter crop intervals or marks the framing for review; it does not silently switch to saliency or center crop.

### User Story 3 - Deliver the reviewed Reel (Priority: P3)

After the production plan and exact timeline are separately approved, the editor renders one portrait master and verifies its picture, sound, duration, and source provenance. Publishing remains a separate request.

**Independent Test**: A synthetic long-form source yields a portrait excerpt with the selected source frames, synchronized source sound, and a verified final file while the original remains unchanged.

**Acceptance Scenarios**:

1. **Given** an approved SDR source range and crop, **when** the timeline renders, **then** the output contains that range at the approved portrait size and preserves its source sound.
2. **Given** a changed source, selection, crop, or timeline, **when** final rendering is requested, **then** the old approval is rejected.

### Edge Cases

- The hero appears only briefly or is too small for a usable portrait crop.
- A cut crosses a shot change, spoken sentence, music beat, or sound effect tail.
- Two subjects or a wide mechanism need more horizontal context than a 9:16 crop permits.
- The input is HDR/Dolby Vision, silent, variable frame rate, or has a different orientation.
- The source footage contains a visible hero but no coherent short-form payoff.

## Requirements

### Functional Requirements

- **FR-001**: Expose one canonical, independently callable `content-studio-video-clipping` skill for a finished or approved long-form video; route simple requested trims to `clip-edit` and crop-only requests to `reframe`.
- **FR-002**: Keep the v1 selection to one contiguous source range. Record source identity, exact in/out, hero description, observed evidence, and unresolved questions in an editable selection record.
- **FR-003**: Present source-linked picture and sound before approval; never infer an event, action, or spoken claim solely from a filename or sparse frame.
- **FR-004**: Run the mandatory Content Studio precheck before any production edit. Record the selected method IDs, exact commands and arguments, measured estimate, output, fallback, and review criterion in its approved plan.
- **FR-005**: Present a portrait crop proposal that keeps the hero and relevant action readable. Require human review of the selected range and affected crop frames, including movement and shot boundaries.
- **FR-006**: Use the approved delivery timeline for source trim, crop, source audio, and final export. Refuse unsupported operations before rendering; do not require a full intermediate master.
- **FR-007**: Require separate human approval of the exact timeline revision and verify the exact delivered picture, audio, and file hash before package approval. Publishing requires its own authorization.
- **FR-008**: Preserve the long-form original and keep draft media and generated previews outside Git.
- **FR-009**: Treat HDR/Dolby Vision picture processing and smooth tracked crops as unsupported in v1. Present a reviewable alternative or stop rather than silently converting or approximating them.

### Key Entities

- **Clip selection**: Source identity, hero description, selected range, source-linked evidence, and editorial decision.
- **Crop proposal**: Target aspect ratio, crop geometry by approved interval, subject evidence, and framing review.
- **Delivery timeline**: Immutable approved source, picture, audio, output, and rendering decisions.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An editor can inspect and revise a proposed source range before any production edit.
- **SC-002**: On a known synthetic fixture, the selected first and last picture frames and audio span match the approved range within one output frame.
- **SC-003**: On representative reviewed frames, the editor confirms that the hero and its essential action remain visible at phone size; failed frames remain `REVIEW` or `UNSUPPORTED`.
- **SC-004**: Changing any approved input or decision invalidates final-render approval, and the original source hash remains unchanged.
- **SC-005**: The exact portrait master passes stream, duration, picture, and listening review before the skill reports delivery complete.

## Assumptions

- The first deliverable is a portrait 9:16 Reel/Short from one finished long-form source, with target duration chosen for the story rather than a hard-coded platform limit.
- V1 uses an SDR input and a stable crop per reviewed interval. It does not promise automatic semantic hero detection or smooth camera-like tracking.
- Existing narration, dialogue, and natural sound are retained by default. New narration, captions, music, SFX, and publication need their own reviewed decisions.
