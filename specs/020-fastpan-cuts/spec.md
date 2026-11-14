# Feature Specification: Fast pan cuts

**Created**: 2026-11-14
**Branch**: `main`
**Status**: Implemented
**Input**: The editor wants fast, blurred camera pans removed from a supplied vlog render through a separately callable Content Studio subskill. Slow motion was rejected because it preserves blur.

## User stories

### US1 — Find reviewable fast pans (P1)

The editor runs one read-only scan on a supplied SDR constant-frame-rate video. The result identifies candidate time ranges, motion evidence, uncertainty, and the source hash. Cuts, moving people, deliberate tracking, and baked-in overlays remain review cases; the scan never deletes footage or approves a cut.

**Independent test:** A synthetic sweep is flagged, while a static segment and an isolated scene cut are not presented as sustained pans. A report can be regenerated without changing the source.

### US2 — Review exact removal bounds (P1)

The editor records frame-aligned source ranges to remove and compares a short before/after preview with aligned source audio. The preview preserves readable views on both sides of the pan, leaves the source untouched, and exposes an abrupt or poor join for revision.

**Independent test:** A synthetic clip with a middle sweep produces a shorter preview with matching picture and audio duration; invalid, overlapping, or out-of-bounds cuts fail before encoding.

### US3 — Hand approved cuts to the delivery timeline (P1)

After the human approves the precise ranges, the subskill emits a `timeline.py revise` changes file containing the kept source spans. The native timeline performs the one final SDR render only after its separate plan and timeline approvals. The subskill does not create a full intermediate video or bypass either review gate.

**Independent test:** A reviewed two-cut fixture yields the expected kept spans and duration, validates in the native timeline, and rejects a changed source or a cut without a human review record.

## Requirements

- **FR-001**: Install and discover `content-studio-video-fastpan-cuts` as an independent nested skill.
- **FR-002**: Scan offline with bounded-resolution samples and report candidate ranges, source identity, motion score, confidence, and coverage. Treat every candidate as pending review.
- **FR-003**: Keep camera pans distinct from a final edit decision. Never infer that a high score alone authorizes removal.
- **FR-004**: Accept exact cut bounds in source frames; validate source identity, frame rate, bounds, overlap, and a usable retained range on each side. Recheck the full source hash at timeline handoff.
- **FR-005**: Make only bounded comparison previews, with source picture and audio cut at the same positions. Reject HDR/Dolby Vision or variable frame rate for the v1 render route.
- **FR-006**: Export reviewed cuts as kept picture ranges for the existing delivery timeline. Refuse a timeline with already timed operations, transitions, or multiple sources until those can be remapped safely.
- **FR-007**: Require the Content Studio precheck before any production edit, a separate human decision on cut ranges, timeline approval before final rendering, and exact-output review.
- **FR-008**: Keep private draft media and generated review clips outside Git. Commit only synthetic evidence.

## Success criteria

- A short synthetic pan is found within 0.5 seconds of its actual sweep, while a static section and isolated cut are excluded from the sustained-pan shortlist.
- Preview output never overwrites the input; picture and audio lengths differ by no more than one output frame after a cut.
- Invalid or unreviewed cut decisions cannot produce timeline changes.
- The emitted changes file validates through the existing timeline model and preserves the source hash.
- Discovery, capability, documentation, and focused tests pass on `main`.

## Assumptions

- The first delivery route targets one supplied SDR constant-frame-rate render, as in Dubai Day 5. Scanning is advisory and may flag deliberate tracking or foreground movement.
- Audio is cut in sync with removed picture. Aesthetic audio smoothing remains a separate reviewed choice.
- The editor reviews short comparisons and exact final output before accepting a cut.
