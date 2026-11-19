# Feature Specification: FFmpeg capabilities in Content Studio

**Feature Branch**: `main`
**Created**: 2026-11-19
**Status**: In progress
**Input**: Implement all eight agreed improvements in the existing Content Studio process.

## User Scenarios & Testing

### User Story 1 - Diagnose media and machine (Priority: P1)

An editor sees actual source streams, frame timing, color, and selected-method availability before approving a production plan.

**Independent Test**: A mixed-format fixture reports all audio streams, display rotation, likely VFR, and an unavailable or unknown component without changing media.

**Acceptance Scenarios**:
1. **Given** VFR footage with multiple audio streams, **when** preflight profiles it, **then** it reports the observed timing and every audio stream.
2. **Given** a selected method whose required component is missing or unknown, **when** preflight runs, **then** it identifies the uncertainty before encoding.

### User Story 2 - Check the exact master (Priority: P1)

An editor receives timecoded technical findings tied to the delivered file hash, with review evidence at affected ranges.

**Independent Test**: Controlled black, frozen, flash, and audio-dropout fixtures produce relevant findings while a clean control avoids them.

**Acceptance Scenarios**:
1. **Given** a delivered master, **when** review runs, **then** it checks stream format, color tags, loudness, true peak, and content-defect candidates.
2. **Given** a portrait destination, **when** graphics are reviewed, **then** the evidence shows destination UI and text-safe guides.
3. **Given** a replaced master, **when** an old report is reused, **then** its hash mismatch is visible and it cannot prove current review.

### User Story 3 - Add requested captions (Priority: P1)

An editor explicitly requests captions, reviews exact cue words, timing, font coverage, and safe-zone fit, and adds approved captions to the delivery timeline.

**Independent Test**: Two supplied cues appear at the approved times in a timeline preview and exact master; an unrequested vlog has no caption work.

**Acceptance Scenarios**:
1. **Given** a timed caption file, **when** proposed, **then** its text, timing, font, line fit, and safe zone are reviewable before approval.
2. **Given** changed cues or sidecar bytes, **when** old timeline approval is used, **then** delivery rejects it.

### User Story 4 - Align separate recorder sound (Priority: P2)

An editor with camera sound and a separate mic gets measured offset and drift, a short audition, and a source-linked manual-edit handoff.

**Independent Test**: A delayed and drifting synthetic recording yields an accurate, confidence-qualified report and bounded audition without changing originals.

**Acceptance Scenarios**:
1. **Given** shared sound, **when** analysis runs, **then** it reports offset, drift, confidence, and measured ranges.
2. **Given** silence or ambiguous correlation, **when** analysis runs, **then** it returns REVIEW instead of an exact-looking answer.
3. **Given** source preparation, **when** sync is requested, **then** it creates no enhanced full-length source clip; permanent alignment waits for an approved timeline.

### User Story 5 - Review portrait framing (Priority: P2)

An editor sees crop loss, subject clearance, destination UI coverage, and crop jumps while approving hero-led portrait clips.

**Independent Test**: A moving-subject fixture exposes known lost coverage and an adjacent-crop discontinuity with source-versus-crop evidence.

**Acceptance Scenarios**:
1. **Given** a reviewed subject box, **when** a crop is proposed, **then** the report measures retained coverage and shows affected source and crop frames.
2. **Given** adjacent crops, **when** their boundary is previewed, **then** visible discontinuity is flagged for human review.
3. **Given** motion saliency alone, **when** no hero is identified, **then** the report does not claim semantic hero detection.

### User Story 6 - Measure final-mix loudness (Priority: P2)

An editor masters the resolved composite mix using measured values and verifies exact-master loudness and true peak while encoding final audio once.

**Independent Test**: A voice-plus-music fixture reaches the project target within tolerance without a full intermediate audio master.

**Acceptance Scenarios**:
1. **Given** a loudness operation, **when** rendering starts, **then** its parameters are measured from the resolved mix.
2. **Given** an already acceptable mix, **when** reviewed, **then** a SKIP decision preserves the selected treatment.
3. **Given** a final miss, **when** verification runs, **then** it reports REVIEW.

### User Story 7 - Offer accurate low-reencode cuts (Priority: P3)

An editor can compare an accurate cuts-only H.264 delivery with an option that copies unaffected packets and encodes only boundary groups.

**Independent Test**: A long-GOP fixture cut between keyframes retains source-correlated boundary frames and synchronized audio, with packet-copy evidence.

**Acceptance Scenarios**:
1. **Given** compatible cuts-only media, **when** smart cut is selected, **then** boundary frames and audio timing are verified.
2. **Given** VFR, HDR/DV, incompatible codec, or additional picture effects, **when** proposed, **then** smart cut is refused or remains a bounded comparison candidate.
3. **Given** uncertain boundaries, **when** reviewed, **then** the accurate timeline route remains the approved fallback.

### User Story 8 - Retime on one timeline (Priority: P3)

An editor can request finite speed ranges, freeze, reverse, and loop, reviewing resulting picture, sound, duration, and downstream cue timing before approval.

**Independent Test**: Each method renders through one approved timeline export with the expected frame sequence and duration, preserving originals.

**Acceptance Scenarios**:
1. **Given** a retime, **when** the timeline resolves it, **then** later cues use resolved output time.
2. **Given** reverse, freeze, or speed change, **when** previewed, **then** source-audio treatment is explicit.
3. **Given** unsupported media or an unbounded loop, **when** validated, **then** it refuses before export.

### Edge Cases

- Display rotation differs from coded frame dimensions; a moving hero crosses crop boundaries.
- A source, sidecar, timeline revision, or final output changes after review.
- A mic starts late, has only music in common, or offers two similarly strong correlation peaks.
- Intentional black, frozen, flash, or silent material resembles a defect and needs human judgment.
- FFmpeg feature listing fails, or a listed filter fails on the actual command graph.
- A method receives VFR, HDR/Dolby Vision, multiple streams, or audio-only media outside its supported scope.

## Requirements

### Functional Requirements

- **FR-001**: Preserve the mandatory precheck, editable plan, step checklist, timeline approval, exact-master review, and separate publication authorization.
- **FR-002**: Preserve originals and the default raw-source-to-manual-edit handoff; never start AutoCut or generate vlog captions by default.
- **FR-003**: Provide source-linked stream and selected-method capability evidence with available, missing, and unknown states.
- **FR-004**: Bind technical findings and caption, sync, framing, and retime decisions to the exact assets and timeline revision they describe.
- **FR-005**: Provide timecoded exact-master technical findings and viewable or playable evidence without granting creative approval automatically.
- **FR-006**: Expose one canonical captions subskill and one canonical source-sync subskill with reviewed timeline handoffs.
- **FR-007**: Improve existing clipping and reframe skills with crop coverage, continuity, and destination-interface evidence.
- **FR-008**: Measure the final composite mix for loudness processing and verify delivered loudness and true peak without a full intermediate master.
- **FR-009**: Restrict smart cut to declared compatibility conditions and verify frame and audio boundaries.
- **FR-010**: Expose one canonical retime subskill for finite speed ranges, freeze, reverse, and loop with resolved timing and explicit audio treatment.
- **FR-011**: Reject unsupported timeline operations before final encoding and encode each delivered picture frame and audio sample at most once.
- **FR-012**: Document method limits, exact commands, fallback, and review evidence; keep private and generated media outside Git.

### Key Entities

- **Media profile**: Source hash, streams, display geometry, timing, and color evidence.
- **Capability result**: Method, required components, and available/missing/unknown status.
- **Review finding**: Exact-output hash, time, measured signal, evidence, and review state.
- **Operation proposal**: Source and plan identity, parameters, preview evidence, and human decision.
- **Timeline revision**: Approved picture, audio, graphics, timing, assets, and fingerprint.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Each of the eight stories has an owning skill, documented review path, and representative outcome test.
- **SC-002**: Missing or unknown selected FFmpeg capabilities surface before full output encoding.
- **SC-003**: Controlled defect fixtures produce timecoded exact-master findings, and reports identify their output hash.
- **SC-004**: Confident synthetic caption and sync fixtures match expected timing within one output frame and 20 ms of audio, respectively.
- **SC-005**: Changing an approved input, sidecar, decision, or output invalidates the corresponding approval or review evidence.
- **SC-006**: Applicable timeline and exact-output tests pass without source mutation or an unintended intermediate master.

## Assumptions

- Current Content Studio skills and timeline remain the canonical owners; the external tool is a reference for specific behavior.
- New picture-processing methods start with SDR unless a separate HDR/DV preservation or tone-map route is verified.
- Technical defect detection and platform guides inform human review; they do not decide creative acceptance.
