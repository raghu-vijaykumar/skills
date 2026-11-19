# Separate-recorder sync capability matrix

Analyze shared sound, audition bounded alignment, and reanalyze against the
supplied manual edit before any timeline handoff. Silent or ambiguous sound
stays unsupported and originals remain intact.

## Capability matrix

| Capability | Status | Input → Output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `sync-recorder` | Supported | Camera/edit audio + separate recorder → offset/drift report and short stereo audition | Yes | [Offset, drift and ambiguity fixtures](tests/test_sync.py) and [timeline handoff](SKILL.md) | One uncut SDR manual edit; early/late listening and exact-output review are required. |
