# Feature Specification: Named object blur

**Created**: 2026-11-18

**Branch**: `main`

**Status**: Implemented

## User stories

### US1 — Find the requested object

Given one finished SDR edit and a plain-language target, find every matching instance on every output frame. A normalized frame click can select one particular instance. Save source-linked detections, a lossless outline mask, and frame-level uncertainty evidence without altering the source.

### US2 — Correct and review coverage

Accept reviewed per-frame boxes and polygons to correct missed or excess masks. The editor inspects all frames for concealment and records a human coverage review bound to the exact source, analysis, and mask bytes. No machine score substitutes for this review.

### US3 — Blur through the delivery timeline

Add a pending object-blur operation to the immutable timeline. Preview a bounded range before approval. Refuse final export if the source, mask, analysis, coverage record, or timeline approval changed. Apply the blur during the one final SDR video encode, preserving audio and unaffected picture areas.

## Requirements

- **FR-001**: Expose one canonical `content-studio-video-object-blur` leaf and route requests to it after mandatory preflight.
- **FR-002**: Process every timeline output frame, all matching instances by default, with optional single-object click selection.
- **FR-003**: Keep model revisions, source hashes, frame counts, dimensions, corrections, uncertainty, and mask hashes in local draft evidence.
- **FR-004**: Require human review of every frame and resolution of flagged frames before final export.
- **FR-005**: Reject HDR/Dolby Vision, timeline cuts/joins, geometric edits, and any picture arrangement that would misalign the v1 mask.
- **FR-006**: Preserve source and audio, perform one final video encode, and verify the exact delivered file.
- **FR-007**: Add tests, capability documentation, and synthetic rendered evidence without committing private production media or model weights.

## Success criteria

- Synthetic moving and multiple objects produce masks on the intended frames; outside-mask pixels remain unaffected.
- Missing or stale coverage evidence cannot pass final validation or approval.
- The exact delivery render has the expected blur, duration, audio, and one video encoder invocation.
- Focused tests and repository documentation gates pass; only feature files are committed and pushed.
