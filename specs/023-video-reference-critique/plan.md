# Reference video critique

**Requirement.** Given a reference and a different cut, compare equivalent narrative beats by explicit time ranges, identify missing source coverage, and turn observed gaps into prioritized scene changes with a visible retest.

**Approach.** Add an independently discoverable Content Studio review skill with a local FFmpeg evidence command. Keep automated results limited to range coverage, fingerprints, stream metadata, and evidence renders. Use an authored map for mismatched timelines. Record subjective findings separately.

**Tasks**

- [x] Implement mapped motion and still evidence with tests for partial coverage, different clip lengths, and invalid ranges.
- [x] Route critique from Content Studio review and hand its prioritized findings into scene authoring.
- [x] Run on the original reel and the exact 22-second preview. Preserve private evidence, critique, and next-pass acceptance criteria in Motion Lab.
- [x] Run package checks and verify the managed installation.
