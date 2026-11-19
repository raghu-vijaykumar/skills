# Data model

## MediaProfile

`source`, full `sha256`, file size, format duration, coded dimensions, display dimensions and rotation, video codec/pixel format/color tags/HDR-DV signal, nominal and sampled frame timing, `audio_streams[]` with stream index/codec/channels/layout/rate/start/duration. Unknown fields remain explicitly unknown. The profile is read-only evidence and does not authorize editing.

## MethodCapability

`method_id`, required component names, per-component `available | missing | unknown`, detected FFmpeg version/build, and overall usability. A missing or unknown selected requirement prevents claiming the method is ready. Optional components are reported separately.

## TechnicalFinding

`output_sha256`, `timeline_sha256` when applicable, `kind`, `start`, `end`, measurement, threshold, detector version, `REVIEW | SKIP | FIX | UNSUPPORTED`, and exact-master evidence paths. An older finding cannot be attached to changed output bytes.

## CaptionProposal

Hashed source cue file, exact cue text and times, font and language, target frame geometry, safe-area settings, generated sidecar hash, preview, and human review status. The timeline operation points to the sidecar and invalidates approval if bytes change.

## SyncProposal

Camera and recorder full hashes, sampled windows, offset in seconds, drift in parts per million, confidence/ambiguity, bounded audition path, and review status. An analysis report never overwrites camera or mic files.

## FramingEvidence

Source hash, source/output time, reviewed hero box if supplied, crop rectangle, retained-box fraction, motion-centre measurement, safe-zone guide image, and boundary discontinuity. Saliency alone does not create a hero identity.

## SmartCutDecision

Source hash, keep ranges, codec and VFR/HDR checks, candidate/fallback status, encoded boundary ranges, copied packet ranges, exact output hash, and frame/audio boundary proof.

## RetimeOperation

Source range, finite method (`speed | freeze | reverse | loop`), parameters, audio policy, resolved output range, reviewed evidence, and approval state. All following timeline cues resolve from the resulting output duration.
