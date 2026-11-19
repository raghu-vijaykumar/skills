# Requested caption capability matrix

Captions are opt-in and use an approved precheck, bounded preview, pending
timeline handoff, human review, and exact-master verification. No caption or
transcript work runs for an ordinary vlog draft.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `captions-ass` | Supported | Reviewed timed cues + font → hashed ASS sidecar and pending timeline operation | Yes | [Cue, safe-zone and render fixtures](tests/test_captions.py) and [workflow](SKILL.md) | Exact cue text and font need human preview review; changed bytes or timeline require new approval. |
