# Feature Specification: Shot-aware SFX selection

**Feature Branch**: `raghu/instagram-reel-sfx`
**Created**: 2026-11-11
**Status**: Implemented, installed, and private catalogue metadata updated under the approved production plan

## User scenarios and acceptance

### US1 — Identify existing effects (P1)

An editor listens to each stock SFX and records a plain-language identity plus tags describing the shot situations where it fits. The source hash, audio, rights state, and effects-only review remain intact. The private catalogue shows the description and can search by a shot tag.

### US2 — Select good matches for an edit (P1)

Given an edited-shot manifest with verified ranges, shot tags, and audio context, Workflow runs the stock selector as an approved plan step. It proposes a sound only when shot tags overlap and the full effect fits the shot. Dialogue and natural-sound shots receive no proposal. Every proposal requires editor review and does not change the timeline.

### US3 — Respect reuse rights (P1)

Default delivery selection excludes reference-only effects. Reference mode may show such a candidate for private comparison but marks it unavailable for placement. A reviewed effects-only stem with unknown rights remains reference-only.

## Constraints

- The tool does not infer audio identity from a waveform or shot meaning from pixels. Those labels must be supported by listening and an approved understanding/editing pass.
- The four Reel effects remain private, outside Git. E01, E02, and R05 must not acquire more specific identities than the editor's listening supports.
- Production catalogue changes require the Content Studio precheck, approved plan revision, checklist evidence, and final catalogue review.
- No direct automatic insertion, publication, or claim of licensed reuse.
