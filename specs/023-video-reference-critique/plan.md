# Reference video critique

**Requirement.** Given a reference and a different cut, compare equivalent narrative beats by explicit time ranges, identify missing source coverage, and turn observed gaps into prioritized scene changes with a visible retest.

**Approach.** Add an independently discoverable Content Studio review skill with a local FFmpeg evidence command. Keep automated results limited to range coverage, fingerprints, stream metadata, and evidence renders. Use an authored map for mismatched timelines. Record subjective findings separately.

**Tasks**

- [x] Implement mapped motion and still evidence with tests for partial coverage, different clip lengths, and invalid ranges.
- [x] Route critique from Content Studio review and hand its prioritized findings into scene authoring.
- [x] Run on the original reel and the exact 22-second preview. Preserve private evidence, critique, and next-pass acceptance criteria in Motion Lab.
- [x] Run package checks and verify the managed installation.

## Consecutive frames and motion transfer

The sparse review missed subsecond handoffs. For one mapped beat, decode all displayed pictures at each input's timestamps. Index and display each lane independently. Use region change percentages to find transitions and seeded object matching to locate visible translation. Export canvas-relative MotionObject keys in contiguous segments. A confidence loss stays visible as a gap. Verify with unequal frame rates, an occluded synthetic actor, and the original and reconstructed payment retry sequence.

For revision review, allow an optional independently mapped previous cut to join the same frame trace. The three exact streams carry their own ranges, word anchors, event times, holds, and normalized crop bounds. Confirm the previous lane preserves its decoded timebase and the two-lane workflow still runs with its existing map.

Play the selected frames together at real or quarter speed using each lane’s presentation timestamps. Verify with different start offsets and rates and confirm manual stepping cancels joint playback.

## Word action windows

For a Rapid Take shot, expose a pre-render inspection of compiled actions to flag
repeated targets and changes arriving after the next word. Reuse the compiled
tracks across art presets. Review the visible result with the existing word cue
audit, frame trace, and actor scorecard. Cover immediate changes, overlapping
actions, identical targets and a one-frame cue window in the runtime tests.
