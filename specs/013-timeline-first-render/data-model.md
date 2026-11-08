# Data model: Timeline-first rendering

## Production plan

Existing preflight `plan.json` and human `approval.json` remain the first gate. The timeline records the plan SHA-256 used to construct it.

## Timeline revision

- `schema`, `revision`, `parent_sha256`, `plan_sha256`, `source_root`, `fps`, `width`, `height`, `color_policy`, `output`.
- Ordered picture clips with stable IDs, source paths and hashes, source in/out, timeline in/out, and optional transition overlap.
- Audio tracks referencing source audio, recorded/synthesized voice, music, or sound effects, with timing and gains.
- Operations with stable ID, method ID, target track/clip, timeline start/end, parameters, review status, and explicit stage order.
- Derived `resolved_duration` and cue positions are calculated, not accepted as unverified input.
- Revision is immutable; a change writes a new revision with its parent's fingerprint.

## Approval

Human review note and fingerprint covering exact plan bytes, timeline bytes, every input asset hash, render settings, and renderer capability version. Missing or changed data invalidates approval. The agent cannot infer approval from a generated preview.

## Render record

Timeline and approval fingerprints, input hashes, capability list, exact applied operations, output hash, duration/frame count/audio properties, command identity, and final review result. An incomplete record cannot authorize package approval.

## State transitions

`planned -> timeline_draft -> timeline_validated -> awaiting_human_approval -> approved -> rendering -> rendered -> verified`.

Any edit after approval creates a new `timeline_draft` revision. An unsupported operation yields `unsupported` before render. Verification failure yields `review` and never implies package approval.
