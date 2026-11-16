# Shared word choreography

A Rapid Take editor can reuse the same narrated scene in anime, pixel art, and future visual presets. The final narration, shot ranges, actor IDs, gestures, and object actions use one frame clock. Art components define their own geometry, palette, and surfaces and use sampled values to perform the shared action. Core Explainer can reuse the runtime with deliberate cue intervals.

## Acceptance

- A valid cue resolves to a named actor action. An invalid actor, action, channel or clock fails clearly.
- Changing artwork preserves the input state on every frame. Multiple channels can move across word boundaries. A new target samples the position already visible on its onset.
- Audit can compare shot and word timing and actor/action bindings between plans. A private paired render checks the same narration, visible actions and rig poses in two looks.
- Trace an observed visual event to its aligned word independently in each rendered look. Report its signed offset from speech using the decoded picture timestamp.
