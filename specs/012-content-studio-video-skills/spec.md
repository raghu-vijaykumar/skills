# Feature Specification: Content Studio video skill migration

**Feature Branch**: `raghu/content-studio-video-skills`
**Created**: 2026-11-08
**Status**: Implemented and validated
**Input**: Implement the reviewed `content-studio/PROPOSED_FOLDER_STRUCTURE.md`, align all four prompt templates, both READMEs, and `AGENTS.md`.

## User Scenarios & Testing

### User Story 1 - Prepare footage for manual editing (P1)

A folder of raw camera videos triggers an approved source-preparation plan and produces individually prepared clips, then stops for the user's manual edit.

**Independent test**: A representative folder yields ordered clips and reports without an AutoCut, joined master, automatic blur removal, narration, overlays, or upscale.

1. Given raw clips, when the user asks to prepare them, then the precheck names exact operations, methods, scripts, outputs, estimates, and review criteria before processing.
2. Given approved source preparation, when it completes, then the user receives individual prepared clips and capture order while the originals remain available.
3. Given a direct operation-skill call, when it starts, then the same precheck and evidence gates apply.

### User Story 2 - Resume from a manually edited render (P1)

The user can later supply a rendered edit and request an evidence-linked voice script, approved voice, final-edit upscale, and code-generated overlays for named scenes, independently or in that order.

**Independent test**: A supplied manual edit can be analyzed and routed without running AutoCut; upscale runs on the completed picture before overlays, and overlays render at delivery resolution.

1. Given a manual render, when voice is requested, then the script is tied to that render's hash and reviewed before synthesis; cloning requires consent and a listening check.
2. Given a finished edit, when upscale is requested or justified, then untouched, Lanczos, and AI candidates are compared on bounded ranges and only the approved full edited video is upscaled.
3. Given named scenes, when overlays are requested, then cues use the reviewed edit timeline and code graphics are composited after any upscale.

### User Story 3 - Invoke each skill directly (P1)

The user can invoke a video category or leaf operation skill by its unique installed name. All video implementation files live under `content-studio-video/`; existing public names and commands remain compatible.

**Independent test**: Recursive discovery finds every nested `SKILL.md`, installs unique links, and each operation runs its relevant current backend without first invoking its parent router.

1. Given an installed bundle, when any nested skill is called directly, then its instructions, dependencies, and method entrypoint resolve.
2. Given an existing consumer command or package import, when run after migration, then it resolves to the same maintained implementation.
3. Given a proposed method without a working backend, when selected, then the skill reports it unsupported rather than claiming success.

### User Story 4 - Use truthful prompts and documentation (P2)

Prompt templates, both READMEs, `AGENTS.md`, and the proposal describe the shipped structure and workflow without promising unavailable methods.

**Independent test**: Docs and prompt checks pass; paths exist; raw-folder prompts stop at the handoff; AutoCut remains explicit-only; animation and social prompts check renderer and asset support.

## Edge Cases

- A source has Dolby Vision, HDR, blur, duplicate, unstable motion, or audio defects: preserve the original and route uncertain changes to review.
- A manual render changes after voice or overlay timing approval: invalidate derived timing and review evidence.
- A method needs a missing model, licensed asset, or unsupported backend: report `UNSUPPORTED` or retain source; never create a placeholder output.
- Installed skill names collide or a destination link is unmanaged: fail safely without deleting the other installation.
- A project depends on existing CLI, npm exports, or root skill names: preserve compatibility.

## Functional Requirements

- **FR-001**: All video-specific maintained implementations MUST reside under `content-studio/skills/content-studio-video/`; root legacy skill names may remain only as thin compatibility entrypoints.
- **FR-002**: Every usable category and operation MUST have a unique `SKILL.md` and be directly discoverable and installable.
- **FR-003**: Alternative implemented methods for an operation MUST have separate script entrypoints and explicit method IDs. Unimplemented methods MUST be visibly unavailable.
- **FR-004**: The installer and docs validator MUST recursively discover nested skill entrypoints, validate unique names, and preserve managed-install safety.
- **FR-005**: Existing CLI commands, package imports, and project installation paths MUST remain functional through compatibility dispatchers or updated exports.
- **FR-006**: The default camera workflow MUST be preprocessing to individual clips, manual handoff, and a stop; AutoCut MUST require an explicit request.
- **FR-007**: Voice work MUST use the user-supplied render, approval of evidence-linked script and voice, and consent for cloning.
- **FR-008**: Upscale MUST assess the full edited video after voice and before code-generated overlays; clean or already adequate video MUST be skipped.
- **FR-009**: Prompt templates and repo guidance MUST name the precheck, method selection, stop points, output paths, and separate publication authorization.
- **FR-010**: The migration MUST preserve originals, human review gates, source hashes, and existing test behavior.

## Success Criteria

- **SC-001**: Every shipped nested skill is linked under a unique top-level installed name and loads its own entrypoint directly.
- **SC-002**: A raw-folder path reaches a prepared-clip handoff without creating an automatic story edit, joined master, voice, upscale, or graphics.
- **SC-003**: A supplied-render path selects voice, upscale, and overlay stages in the requested order; no overlay pixels enter the upscale input.
- **SC-004**: Existing public CLI and package consumers pass their regression suites after the move.
- **SC-005**: Documentation validation and focused tests pass with no broken local links or untracked generated media.

## Assumptions

- Migration moves existing working backends; future method names in the proposal do not authorize inventing new enhancement models.
- Current root skill names and CLI commands are compatibility interfaces until consumers can migrate.
- This feature changes repository code and docs, not a content draft or published media.
