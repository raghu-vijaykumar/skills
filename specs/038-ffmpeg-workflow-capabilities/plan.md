# Implementation Plan: FFmpeg capabilities in Content Studio

**Branch**: `main` | **Date**: 2026-11-19 | **Spec**: [spec.md](spec.md)

## Summary

Implement the eight requested capabilities in their existing Content Studio owners or three new canonical leaves. Preserve preflight approval, the manual-edit source handoff, versioned delivery timelines, separate timeline approval, one final export for supported operations, exact-master review, and separate publication authorization. Use FFmpeg Skill as a behavior reference; do not add its broad skill entrypoint or project renderer to the production route.

## Technical Context

**Language/Version**: Python 3.13 on the current Windows host; repository scripts retain their existing supported Python floor.
**Primary Dependencies**: Local FFmpeg/FFprobe, existing Content Studio Python helpers, optional Pillow for review images. No runtime dependency on the external skill.
**Storage**: JSON reports and bounded PNG/WAV/MP4 evidence in draft `.content-studio/` folders; no generated media in Git.
**Testing**: Existing `unittest` suites, synthetic FFmpeg media for timing and output, `npm run check:docs`, exact-master review probes.
**Target Platform**: Current Windows workflow with portable command arrays and no shell-generated FFmpeg strings.
**Project Type**: Skill bundle and independently callable Python CLIs.
**Performance Goals**: Bound diagnosis and preview duration, seek source ranges before decoding, reuse source-hash analysis results where possible.
**Constraints**: Human approval gates; no raw-folder full enhanced clips; no default transcription; SDR-only picture adapters unless separately proven; one final video and audio encode per approved timeline output.
**Scale/Scope**: Eight story increments over existing skills and three new leaves: captions, sync, retime.

## Constitution Check

- **One canonical implementation**: Existing owners receive improvements; only distinct caption, sync, and retime workflows gain new leaves. No aliases.
- **Teaching and rendered evidence**: Crop, captions, retiming, and defect checks produce source-linked visual or listening evidence, then are reviewed on the exact master.
- **Portable interfaces**: Commands use project paths, stream metadata, cue files, time ranges, and destination settings, with no channel-specific hardcoding.
- **Real validation**: Missing capability, unsupported timeline operation, stale asset, or failed final measurement stops or returns REVIEW. Existing gates remain applicable.
- **Reproducible releases**: Tests use synthetic media. Generated assets and credentials remain outside Git. Commit each complete slice to `main` after staged-diff review and push.

## Design decisions

1. **US1 profile and capability report**: Extend `content-studio-workflow/scripts/preflight.py` with a source hash, display rotation, coded and display geometry, all audio streams, sampled frame timing, and component status. Required capabilities are derived from selected method IDs, not a machine-wide all-tools requirement. An introspection parser failure is `unknown`. The approved plan records this report and exact selected methods.
2. **US2 final review**: Add a technical review command owned by `review/final-render`; make `timeline/scripts/verify.py` use or reference it so the final report is bound to `output_sha256`. Use FFmpeg read-only detectors and bounded evidence. Automated flags remain `REVIEW`; clean content does not produce a creative PASS.
3. **US3 captions**: New `edit/captions` leaf validates SRT/ASS or a reviewed cue list, copies exact words into a hashed ASS sidecar, and emits a pending `motion-graphics-ass` operation through the existing timeline. The first delivery mode is burned captions. A later muxed-subtitle route must have separate timeline and exact-output tests before it is advertised.
4. **US4 sync**: New `source/sync` leaf measures offset at more than one speech-rich window, estimates linear drift, and writes a confidence-qualified report and bounded comparison. Raw-folder work ends with this handoff. A permanent audio alignment method is added to the delivery timeline only when verified against a supplied manual edit.
5. **US5 framing**: Extend `edit/reframe` analysis and `edit/clipping` proposals with subject-box coverage, motion-centre and crop-change evidence. Safe-zone guides are overlays on review images; they do not alter source pixels. Preserve the editor's subject choice and method selection.
6. **US6 loudness**: Keep the standalone mastering logic. For a timeline `loudnorm` operation, run the resolved audio graph to a null output for measurement, then pass measured normalization parameters into the final graph. Source decoding for analysis is permitted; the final audio is encoded once. Recheck delivered LUFS/true peak against the configured target.
7. **US7 smart cut**: Add a cuts-only candidate method under `edit/clip-edit`, with codec/VFR/HDR guards and frame/audio boundary proof. Do not combine packet-copy output with later picture filters. Offer the existing accurate timeline render as fallback when any precondition or proof fails.
8. **US8 retime**: New `edit/retime` leaf drafts finite speed, freeze, reverse, and loop changes. Extend timeline validation, time resolution, and FFmpeg graph compilation for supported SDR cases. Explicitly specify source-audio behavior; recompute later cue times from the retimed picture duration before approval.

## Project Structure

```text
specs/038-ffmpeg-workflow-capabilities/
  spec.md  plan.md  research.md  data-model.md  quickstart.md  tasks.md
  contracts/operation-handoffs.md
content-studio/skills/content-studio-workflow/scripts/preflight.py
content-studio/skills/content-studio-video/
  source/{preprocess,sync}/
  edit/{captions,clipping,reframe,clip-edit,retime}/
  audio/mastering/
  review/final-render/
  timeline/{methods.json,scripts/model.py,scripts/compiler.py,scripts/verify.py}/
```

**Structure Decision**: Keep all executable routes in the canonical nested skill that owns their decision and review process. The timeline is the only owner of final edited-video rendering.

## Implementation sequence

1. Implement source and machine diagnostics, with capability detection and focused preflight tests.
2. Implement exact-master technical review and hash-bound evidence, with known-defect and clean controls.
3. Add requested-caption workflow and timeline handoff; test cue text, timing, safe area, approval invalidation, and exact output.
4. Add separate-recorder sync analysis and bounded audition; test offset, drift, and ambiguous/silent cases.
5. Improve clipping/reframe evidence; test movement coverage, crop jumps, and review-guide placement.
6. Integrate measured final-mix loudness into one timeline export; test voice/music mix and final target.
7. Benchmark and implement guarded smart cut; verify boundary frames, audio, and packet reuse.
8. Add retime model, resolver, graph, review evidence, and all four methods; test downstream cue timing and one export.
9. Run docs and relevant suites, review staged changes, commit coherent slices, push `main`, and verify remote head.

## Post-design constitution check

The planned interfaces retain canonical owners, portable media inputs, human review, real output checks, and source-preserving delivery. No constitution exception is required.
