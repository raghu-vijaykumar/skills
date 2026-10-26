# Feature Specification: videogen extraction

**Feature Branch**: `raghu/videogen`
**Created**: 2026-10-25
**Status**: Approved

## User scenarios

### US1: Start a video in a fresh content repository (P1)

A creator installs a pinned tag of the skills repository, runs `videogen init` and `videogen new video`, then uses the `videogen` skill in Codex or OpenCode to author and review a Remotion video.

**Acceptance:** The new repository has a working Remotion entry, project config, neutral theme, and discoverable skill. A short range renders from a clean checkout.

### US2: Reuse the pipeline for video and posts (P1)

A content repository supplies its own video scenes, metadata, source media manifest, theme, and style. The toolkit generates or loads narration cues, validates the project, and renders selected video ranges and carousel/post editions.

**Acceptance:** All applicable gates run before rendering, failures stop the command, and the output is deterministic from declared inputs.

### US3: Migrate Revise Labs (P1)

The existing content repo pins the tagged toolkit while keeping scenes, research, ReviseGuy, and publishing locally. Older narrated films move to current cue-derived timing and motion/layout contracts without changing their approved teaching or visuals.

**Acceptance:** The 76 implemented video folders and existing content package pass applicable checks and rendered review. The two specified draft directories are removed.

## Requirements

- FR-001: The canonical skill and runtime live under `videogen/` in `raghu-vijaykumar/skills`.
- FR-002: The repository root is installable from a private Git tag as an npm package exposing the `videogen` CLI and typed Remotion runtime.
- FR-003: Project config supplies entry point, content roots, theme/style registry, and optional project gates/outro.
- FR-004: Video metadata supplies the main composition ID; Remotion resolves its runtime dimensions and duration.
- FR-005: Neutral and Revise Labs themes render video and cards without hard-coded brand strings in generic components.
- FR-006: Existing validation semantics remain enforceable, including creative review based on actual rendered evidence.
- FR-007: The skill is installed into `.agents/skills/videogen` for Codex and OpenCode, version matched to the package.
- FR-008: Source media provenance is committed while generated audio, media caches, and render outputs remain ignored.
