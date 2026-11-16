# Build and score heroes from real-world photos

Use this route for a new explainer without a reference video. Start with real photos of the actual hardware, object, or person the narration describes. A future keyboard or mouse episode should use the specific model and revision when the mechanism differs across versions.

1. Build a small reference board for each hero. Record the original source or local capture, the visible side and state, and the features the viewer needs to recognize. Collect a useful overall view, an oblique or side view for depth, and a detail or teardown that shows the moving part. Mark missing or hidden detail. Use project-owned photos, manufacturer documentation, or other traceable real photographs. Keep the references in research and record provenance for the independently authored render assets.
2. Establish the action. Find real images of the same part at different states, a measured original capture, or documentation that explains its operation. Write the observed or documented order and what is expected to remain attached. For a keyboard this could be the keycap at rest, the linkage compressing, the contact triggering, and the cap returning. Use measured timing only when the source provides it. Choose an editorial pace for an illustrative close-up and test it against the narration. Mark undocumented internals as illustrative.
3. Draw or model the object and its separate moving parts from those views. Match silhouette, proportions, materials, and the details that identify it. Hold the original camera for the first action proof. Inspect the starting state, the moving joints and contacts, and the settled state before adding camera movement, captions, or sound.
4. Compare a real photo with the equivalent rendered state for appearance. Compare the actual moving render with the separate evidence for operation. Inspect the mechanism at native frame cadence and run the object scorer. Resolve appearance deficits and open motion evidence on the next pass.

## Compare a still with a rendered state

Use local photo files and the exact rendered video. The regular actor map applies. Omit seconds on the photo and keep seconds on the candidate. Boxes use normalized left, top, right, bottom coordinates in the displayed orientation.

    python scripts/compare_actor.py --reference-photo real-device.jpg --candidate draft.mp4 --map actor.json --out photo-comparison

    {"actors":[{"id":"keyboard-switch","reference":{"box":[0.1,0.2,0.9,0.8]},"candidate":{"seconds":5.7,"box":[0.1,0.3,0.9,0.7]}}]}

Repeat for the real-world views needed to judge a part. Compare a matching angle and state for form and material. Judge the staging axis against readability in the authored video.

## Cartoons and caricatures of real people

Use real photos of the person, including neutral and three-quarter views and a characteristic expression when available. Record the distinctive features and any deliberate exaggeration, then draw or model the character's original layers with the [presenter rig workflow](../../../animation/videogen/scene-authoring/references/presenter-rig.md).

For the appearance score, assess whether the stylized silhouette, face relationships and distinctive features still read as that person in a comparable view. Use material to assess the chosen drawing, shading or texture treatment and staging to assess likeness at delivery size. For motion, score blink, gaze, speech, expression changes and gesture continuity from the rendered performance. If reproducing the person's own mannerisms, compare against a real expression sequence or capture and keep that comparison open until it has motion evidence.

## Record the motion basis

Keep the normal reference appearance, candidate ratings and evidence fields from the [object scorer](object-scoring.md). Add these two fields to the reference object.

    "photos": [
      {"evidence": "unpressed-view.jpg", "shows": "Keycap over the open linkage"},
      {"evidence": "pressed-view.jpg", "shows": "Linkage compressed and contact closed"}
    ],
    "motion_basis": {
      "kind": "photo-sequence",
      "evidence": "Ordered real views of the same switch",
      "states": ["Keycap at rest", "Linkage compressed and contact closed"]
    }

- Use photo-sequence, documented-mechanism, or measured-capture when the evidence establishes ordered states. Supply the normal motion ratings. Assess timing against a documented interval when one exists, or against the intended narration and readability of the state changes.
- Use unverified and set reference motion to null when there is no basis for a motion comparison. The scorer can still show the candidate's motion score and will keep the retest open. Add a real action source and evaluate the same render to close it.
- Use static and set motion to null on both sides for an intentionally still object.

The scorer checks the presence and structure of the evidence. The reviewer confirms it depicts the same object and supports each visible action.
