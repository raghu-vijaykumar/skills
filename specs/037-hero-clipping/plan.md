# Implementation Plan: Hero-led clipping skill

**Branch**: `main` | **Date**: 2026-11-19 | **Spec**: [spec.md](spec.md)

## Summary

Add a canonical `content-studio-video-clipping` leaf at `content-studio/skills/content-studio-video/edit/clipping/`. It takes one finished SDR long-form video through source-linked moment selection, reviewed 9:16 hero framing, an approved delivery timeline, and exact-master verification. It reuses Content Studio's contact sheets, reframe proposals, preflight, and timeline renderer. It does not call AutoCut or create a full intermediate video.

## Technical Context

**Language/Version**: Python, as used by the existing Content Studio video scripts.
**Primary Dependencies**: Existing FFmpeg/ffprobe, Pillow contact sheets, reframe analysis, workflow preflight, and delivery timeline.
**Storage**: JSON and bounded review media under the draft's `.content-studio/clipping/`; no draft media in Git.
**Testing**: Focused Python unit/integration tests, synthetic rendered fixture, `npm run check:docs`, and phone-size picture/audio review.
**Target Platform**: Repository-managed Content Studio skill on the existing supported Windows workflow.
**Project Type**: Independently callable operation skill plus a small validation/handoff script.
**Performance Goals**: Profile the actual source and selected duration before giving an edit/render estimate; avoid full-source frame decoding for a chosen late excerpt.
**Constraints**: One contiguous SDR source range; 9:16 output; stable crop per reviewed interval; source and exact output hashes; two human approvals.
**Scale/Scope**: One Reel/Short from one approved long-form source per invocation.

## Constitution Check

- **One canonical implementation**: The new leaf owns selection and handoff; `reframe` owns crop proposals and `timeline` owns final rendering.
- **Teaching and rendered evidence**: The hero and action must read at phone size in the rendered preview and exact master.
- **Portable interfaces**: Inputs are project paths, source time ranges, hero description, target dimensions, and review evidence.
- **Real validation**: Unsupported HDR or missing/failed crop approval stops before export; tests include rendered picture and audio.
- **Reproducible releases**: Generated video and private draft evidence stay outside Git. No new model weights are required.

## Project Structure

```text
specs/037-hero-clipping/
  spec.md
  plan.md
  research.md
  data-model.md
  contracts/selection.md
  quickstart.md
  tasks.md

content-studio/skills/content-studio-video/edit/clipping/
  SKILL.md
  methods.json
  scripts/clipping.py
  tests/test_clipping.py
```

Update the existing `content-studio-video` and `content-studio-video-edit` routers, capability documentation, and any relevant method checks. Keep the current `clip-edit` and `reframe` leaves callable under their own names.

## Implementation sequence

1. **Intake and evidence**: Require an approved or finished source and hero cue. Probe and hash it; use `understand.py` for timestamped full-source discovery or a bounded neighborhood. Add a denser preview around the candidate. Show source picture and sound before selecting exact boundaries.
2. **Editable selection**: Save one contiguous range and hero/action rationale in `selection.json`. Validate time bounds and source hash. Review the hook, complete action, payoff, and sound boundary. The editor selects the range; a sparse sample never automatically certifies the scene.
3. **Portrait proposal**: Run `subjects.py` from supplied hero boxes as the preferred method. Offer `center.py` or `saliency.py` only as explicitly reviewed alternatives. Compare original and 9:16 crop at the start, middle, end, and movement/shot changes. Split the continuous source span into adjacent crop intervals only if needed and reviewed.
4. **Human review · preflight plan**: Run `content-studio-workflow` for the actual source. Show method IDs, exact argv, measured benchmark/time estimate, output, fallback, and acceptance criteria. Production work resumes only after the current plan revision is approved.
5. **Timeline handoff and preview**: Convert the reviewed selection/crops into the timeline's `picture` and `crop` operations. Validate 1080×1920 SDR output and source audio continuity. Render a bounded composite preview and review crop motion, picture quality, and sound. Obtain separate approval of the exact timeline revision.
6. **Render and verify**: Render once from the original source through the approved timeline. Verify the exact master file hash, source range, duration, frame geometry, audio sync, and representative/complete picture at phone size. Close preflight checklist evidence. Publication remains a separate action.

## Design limits and fallbacks

- The reframe analyzer offers one stable crop per interval. Smooth tracking is a later feature. If the hero moves beyond a stable crop, review adjacent crop intervals; if cuts are distracting or the context cannot fit, stop for a manual treatment decision.
- The delivery timeline accepts SDR crop processing. An HDR/Dolby Vision source needs a separately reviewed tone-map and renderer design before this skill can claim portrait delivery.
- No captions, new narration, music, SFX, or automatic upload are implied. Add them only through the corresponding approved Content Studio route.
- Estimates are source- and machine-specific. The preflight benchmark measures a short sample; final encoding overhead is measured or disclosed separately.

## Post-design constitution check

The design keeps a single owner for each operation, portable inputs, explicit method validation, delivery-size visual proof, and source-preserving output. No constitution exception is needed.
