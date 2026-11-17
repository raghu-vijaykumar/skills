---
name: content-studio-video-critique
description: Review rendered video, score hero assets and motion, and retest fixes against references with timecoded evidence.
---

# Content Studio video critique

Use for a creative reconstruction, style study, or two revisions with different cuts. For same-cut technical fidelity use [quality](../quality/SKILL.md). For a native grid of processing variants use [benchmark](../benchmark/SKILL.md).

For a dense, narrated reconstruction, use the [full reconstruction checklist](references/reconstruction.md). Start with the source-only survey, then follow the complete source from word timing and actor inventory through asset construction and independent render reviews.

For authored 2D, 2.5D, 3D, or hybrid hero motion, run the [object review loop](references/object-scoring.md#production-checkpoints) on the scene proof and exact master. Track each hero, independently moving part and distinct action from the storyboard. Score form, material, and staging separately from mechanics, timing, and continuity. Fix the smallest affected range, rerender, and rescore against the same evidence.

For a new topic without a video reference, use the [real-world photo workflow](references/photo-reference.md). Compare photographed views with the rendered hero and score motion against separate evidence for the operation.

For 3D explainers, use the [3D review checkpoints](../../animation/engineering-3d/references/code-first-explainer.md#critique-a-3d-render). Match a real device view for physical fidelity and the same teaching action for motion. Compare fixed-camera component proofs before judging the narrated camera move and record a code-level fix and retest for each deficit.

Use [teaching scoring](references/teaching-scoring.md) for educational beats. Verify the mechanism and its visible cause and effect, then track actual learner results separately from the reviewer’s score.

Use [artifact scoring](references/artifact-scoring.md) to cover the selected script, storyboard, models, animation, narration, mix, accessories, and exact master. Score hook, rehooks, variety and payoff alongside the technical and teaching evidence.

1. Fingerprint the exact reference and candidate. Agree or infer which qualities should match. Map equivalent beats with independent source and candidate ranges. Use a null candidate for a known omission and explicitly record occlusion or an unreviewed state. For a highlight reel, report coverage separately from quality.
2. Run `python <skill>/scripts/compare.py --reference <local-video> --candidate <local-video> --map <beat-map.json> --out <new-private-folder>`. For a full reconstruction, add `--cut-threshold 0.24` to survey abrupt changes across both videos and break dense chapters into separate actions. Read the [map and report guide](references/critique.md). FFmpeg and FFprobe plus Python Pillow produce a real-speed paired GIF and timestamped still sheet per mapped beat.
3. Inspect playbacks at original speed. When the request concerns animation completeness, choose a bounded sequence and use [frame tracing and object tracks](references/frame-tracing.md). Review all its consecutive frames to find short entrances, handoffs, masked transitions, or pose changes. Use separate object tracks for each edit, and export only verified movement for retargeting. Evaluate audio separately and state what you could inspect.
4. Record strengths and ranked gaps with timestamps for both sides, the viewer impact, a concrete revision, and a visible or audible retest. Mark off-scope and missing material explicitly. Report technical checks separately from the creative decision.
5. Hand the top findings to [scene authoring](../../animation/videogen/scene-authoring/SKILL.md) and update the draft review log. Run the same map on the next exact render, adjusting candidate anchors if the cut changes. When integrating a short proof into a full cut, verify the full render at both seams and check that its object, gesture, and speech cues use the correct scene clock. This is read-only diagnosis. Production corrections follow the [workflow precheck](../../../content-studio-workflow/SKILL.md). Keep reference comparison artifacts outside production media and release packages.
