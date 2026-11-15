# Feature Specification: Idea to authored explainer

**Branch**: `main` | **Created**: 2026-11-15 | **Status**: Approved private test

## User scenarios

### P1 — Create a video from a new idea

Given an idea and optional channel, an agent creates a research brief, narration, frame-indexed scene plan, original assets, review evidence, and a rendered video. With no channel, the draft remains channel neutral and contains no invented analytics. The viewer sees a mechanism explained through changing objects and state, not a title slideshow.

### P1 — Private reconstruction study

Given a visual reference, an agent may use it to analyze pacing and framing but the delivered render must contain only newly authored visuals and audio. The Stripe study covers the source duration and all 18 chapters. Asset provenance and source hashes make the separation auditable.

### P2 — Reuse on a distinct long video

The same system produces an approximately five-minute landscape explanation of why web pages stay stale after deployment, with scene-specific visual treatment and verified technical claims.

## Functional requirements

- **FR-001**: Scene plans declare absolute frame bounds, narration cues, representation, semantic state changes, camera motion, presenter state, assets, and source IDs.
- **FR-002**: Pre-render validation rejects unsupported scene types, gaps/overlaps, missing assets, missing hashes, and external reference-media paths.
- **FR-003**: Core Explainer scenes support portrait and landscape framing, reusable device, data, process, document/code, presenter, and dimensional hero components.
- **FR-004**: Channel neutral idea drafts do not require private analytics or assert synthetic metrics.
- **FR-005**: Content Studio skills document the agent-run path from idea through preview, creative review, and delivery.
- **FR-006**: A production record identifies generated/procedural/recorded asset origins and exact rendered evidence.

## Success criteria

- A fresh idea can be scaffolded and validated through the existing videogen CLI.
- Both private pilots have playable full-length renders with no decoded frame/audio errors.
- Provenance validation confirms no reference frame, audio, presenter, or cutout is consumed by their compositions.
- Portrait and landscape hero previews are inspected at native delivery size.

## Assumptions

- This is a private quality experiment; publication remains a separate action.
- The reference supplies motion and layout observations only. Specific internal Stripe architecture must not be inferred from the reel.
- The agent authors a scene plan and script; no fully automatic concept generator is promised.
