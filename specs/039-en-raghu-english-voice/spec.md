# Feature Specification: en-raghu English Voice

**Branch**: `main`

**Created**: 2026-11-19

**Status**: Approved by the owner's request to add, commit, and push the profile.

## User Scenarios & Testing

### User Story 1 - Reuse two approved references (Priority: P1)

The owner can select `en-raghu` in any Content Studio workspace and choose either of the two English takes they reviewed.

**Independent Test**: `status --profile en-raghu` resolves the bundled profile and lists `take2` and `take3`; both stored audio files match their recorded hashes.

**Acceptance Scenarios**:

1. Given a workspace without a local `en-raghu`, when its status is requested, then Content Studio resolves the bundled English profile.
2. Given either approved variant, when synthesis is planned, then that variant's exact audio hash is bound to the plan.

### User Story 2 - Generate English narration (Priority: P1)

The owner can supply an approved English segment script and generate local WAVs using Chatterbox Turbo and one chosen reference.

**Independent Test**: A one-segment render with the local model produces a decodable WAV whose words round-trip to the script.

**Acceptance Scenarios**:

1. Given an English script, consented profile, local model weights, and `take2` or `take3`, when synthesis runs, then a 24 kHz segment and resumable manifest are written under the workspace.
2. Given a changed reference, text, or model revision, when synthesis runs again, then stale audio is not reused.
3. Given a missing or altered reference, unsupported backend, or non-Latin script, when synthesis is requested, then it stops before loading the model.

### User Story 3 - Preserve Kannada synthesis (Priority: P2)

Existing IndicF5 profiles and commands keep their current behavior.

**Independent Test**: Existing voice tests pass and the Kannada mixed-script gate still runs before model loading.

## Requirements

### Functional Requirements

- **FR-001**: Bundle `en-raghu` with the two approved reference takes, their hashes, language `en`, backend identity, and the owner's consent and repository authorization.
- **FR-002**: Select an English reference by a named variant; require a choice when more than one variant exists.
- **FR-003**: Use the profile's backend to route English synthesis to local Chatterbox Turbo and existing IndicF5 synthesis to IndicF5.
- **FR-004**: Keep model weights, virtual environments, generated narration, and comparison previews outside Git.
- **FR-005**: Preserve text, timing, reference hash, model revision, and rendered duration in the existing narration manifest.
- **FR-006**: Require human listening and exact-script review before any generated narration is used in a production video.

### Key Entities

- **Voice profile**: Consented speaker, language, backend, source samples, and available reference variants.
- **Reference variant**: Named clean clip with SHA-256 and duration.
- **Narration segment**: Approved English text and timing, rendered as a local WAV.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Both approved references are retrievable by name and pass hash validation.
- **SC-002**: A real English test segment decodes, does not clip, and round-trip transcription recovers the intended words.
- **SC-003**: Existing IndicF5 tests pass without changing the older `raghu` or `rakshitha` profiles.
- **SC-004**: The commit contains no model weights or generated preview audio.

## Assumptions

- The owner's request to add the profile and commit and push explicitly authorizes these two short biometric reference clips in this repository.
- The two reviewed references remain alternatives; a production script selects one before render.
- Chatterbox Turbo is an optional local dependency. The official model checkpoint remains outside the repository.
