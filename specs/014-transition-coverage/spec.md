# Feature Specification: Complete transition coverage

**Branch**: `main` (editor requested main-only work)
**Created**: 2026-11-09
**Status**: In progress
**Input**: Implement the remaining transition effects, including all eight catalog-only entries, in the editable single-render timeline.

## User scenarios

1. **Choose an existing effect (P1):** An editor can place every transition already rendered by the specialist tool on the delivery timeline. Point effects have editable start/end times; clip joins have an editable overlap duration.
2. **Choose a formerly catalog-only effect (P1):** An editor can join two real shots with collage, page turn, liquid streaks, liquid drops, fire, zoom out, spin, or heart. The catalog states when a treatment is an approximation of the named style.
3. **Approve and deliver (P1):** The complete transition plan is previewed, approved with the timeline fingerprint, then included in the one final render. A changed method, timing, or renderer invalidates approval.

## Requirements

- **FR-001:** All eight formerly catalog-only effects MUST have a real, visually distinct clip-join renderer, a catalog fidelity label, an individual entrypoint, and bounded preview support. None may silently map to a generic wipe or dissolve.
- **FR-002:** Every point and join effect that the specialist tool supports MUST be accepted by the delivery timeline, with the same intended visual treatment and an editable duration or range.
- **FR-003:** A join MUST use two actual shots, shorten the resolved picture and audio duration by its overlap, and crossfade audio when mixed. A one-master point effect MUST preserve duration. Unsupported route choices MUST fail before export.
- **FR-004:** An approved timeline MUST render all selected effects in one final encode. Short previews are allowed; no full intermediate master is required for a transition.
- **FR-005:** The timeline fingerprint MUST bind the transition implementation and catalog so a code or recipe change requires fresh human approval.
- **FR-006:** Synthetic media checks MUST confirm that all eight new effects render and have identifiable entrance, midpoint, and exit states. Timing, audio, source preservation, and method coverage MUST be checked.
- **FR-007:** Documentation MUST distinguish approximations from a faithful third-party asset and state the current scope and review criteria.

## Edge cases

- A join duration at or beyond either neighboring clip duration is rejected.
- A transition using an absent renderer, invalid expression, or incompatible source format fails before creating a final output.
- The final output remains SDR; HDR and Dolby Vision stay unsupported in this renderer.
- Revisions retain the old timeline and require approval of the new fingerprint.

## Success criteria

- Every previously catalog-only effect produces a distinct, decodable bounded join pilot with the expected duration and audio.
- Every specialist-supported transition is represented in the timeline method registry and runs in its single-export path.
- A representative mixed timeline containing a new join effect and a point effect produces one encoded output; stale approval is refused.
- The transition catalog, skill docs, registry, tests, and approval binding agree on supported methods.

## Assumptions

- The eight named effects may be code-generated approximations; they do not claim to reproduce a proprietary Clipchamp motion asset.
- The eight effects operate at real clip joins. They are not placed as point effects on an uncut master.
- This feature updates the editing tools; it does not change or re-render the Dubai Day 4 video.
