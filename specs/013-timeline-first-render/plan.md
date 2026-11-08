# Implementation Plan: Timeline-first final rendering

**Branch**: `main` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

## Summary

Introduce one canonical delivery timeline after the approved workflow plan. Every picture, voice, music, audio, graphic, and transition operation is attached to an immutable revision. Validate the complete revision and its assets before a human approves it; compile the approved revision into one final video/audio export. Revisions use the same gate. Unsupported adapters fail before rendering.

## Technical Context

- **Language/Version**: Python 3, JSON timeline contract.
- **Primary Dependencies**: Existing FFmpeg/FFprobe and Python media adapters; optional local inference backends only when present and benchmarked.
- **Storage**: Draft-local `.content-studio/timeline/` revisions, approvals, previews, manifests, and render records. Originals remain immutable.
- **Testing**: Python unittest contract tests; generated short synthetic media for end-to-end timing, picture, audio, and encode-count verification; docs check and existing regressions.
- **Target Platform**: Windows-first local CLI with portable paths.
- **Project Type**: Content Studio skill/CLI bundle.
- **Performance Goals**: One delivery encode per used frame and sample; no full-length per-effect intermediate master.
- **Constraints**: Mandatory workflow precheck and human plan approval precede timeline edits; human timeline/voice/effect approval precedes final render; HDR/DV and subjective fixes retain review gates.
- **Scale/Scope**: Manual-export-as-source and multi-source timelines; source preparation produces analysis or edit proxies while permanent edits wait for the delivery timeline. All supported picture, audio, voice, transition, and graphic methods eventually route through adapters.

## Constitution Check

- **One canonical implementation**: the delivery timeline compiler owns final assembly; specialist tools provide analysis, previews, or typed adapters, not a second production path.
- **Teaching and rendered evidence**: retain bounded previews and exact-final verification; code checks never substitute for watching/listening.
- **Portable interfaces**: no channel-specific paths, fonts, models, or assets hard-coded into the timeline.
- **Real validation**: missing adapters, assets, approval, or unsafe HDR handling are errors before encode.
- **Reproducible releases**: generated media and approvals live in drafts, outside Git. Contract changes receive docs and tests.

## Project Structure

```text
content-studio/skills/content-studio-workflow/
  scripts/preflight.py                 # plan approval remains first
content-studio/skills/content-studio-video/
  timeline/
    SKILL.md
    methods.json
    scripts/timeline.py                # revision, approval, validation, render CLI
    scripts/model.py                   # schema and time resolution
    scripts/compiler.py                # typed operations -> one delivery graph
    scripts/adapters/                  # picture, audio, voice, graphics, transitions
    tests/
  edit/autocut/scripts/timeline.py     # legacy importer/rough-cut review route
  edit/{restoration,upscale,transitions,motion-graphics}/
  audio/{narration,mastering,music}/
specs/013-timeline-first-render/
```

**Structure Decision**: Add a delivery timeline beside the existing specialist tree. Do not stretch the AutoCut rough-cut renderer into a universal master renderer; it currently renders before final approval, caches encoded segments, and ignores some annotations. Import its source edit where needed, preserving existing CLI compatibility.

## Phase 0 Research

See [research.md](research.md). The old native timeline renders cached H.264 segments, then stream-concats. Transition annotations are not consumed. The current upscale and narration specialists create separate media. Approved temporal polish can apply across an entire clip. A new compiler must split at exact effect boundaries and combine audio and picture in one delivery graph.

## Phase 1 Design

- [Data model](data-model.md) defines immutable revisions, operation IDs, explicit time bases, asset fingerprints, approval fingerprints, and render records.
- [Timeline contract](contracts/timeline.md) defines validation, ordering, approvals, and the one-encode render API.
- [Quickstart](quickstart.md) demonstrates initial and revised render and a refusal case.

## Implementation sequence

1. Add versioned timeline model, source and asset hashing, cut/overlap time resolution, and strict typed-operation validation.
2. Integrate existing plan approval and introduce a separate human timeline approval bound to revision bytes, referenced asset hashes, and render settings. Refuse stale/agent-generated approvals.
3. Build the single delivery compiler. Segment at range boundaries in memory, apply geometry/denoise/deflicker/upscale/color/sharpen in order, then transitions and graphics; combine source audio, approved voice/music/SFX, and audio processing in the same export. Never silently drop a declared operation.
4. Adapt currently supported specialist methods in slices, including preview/inference assets where a model cannot run inline. A temporary model frame cache is allowed; a full-length enhanced master is not.
5. Route initial export and all revisions through the same CLI, preflight, timeline approval, render record, and final-output verification.
6. Update skill guidance, prompts, docs, method registries, and focused tests; run synthetic media pilots and existing regression gates.

## Risks

- AI inference, temporal stabilization, and two-pass loudness may need analysis or temporary frames before encode; document these as preparation, not extra full-master exports.
- Many existing effects cannot be expressed by one simple FFmpeg filter. Adapter readiness must be tracked per method and blocked until verified.
- Cut and transition overlaps alter later cue positions; show resolved times before approval and invalidate approval on any subsequent change.
- Audio sync and HDR/DV metadata can be damaged by a new graph; prove both on representative media before advertising support.
