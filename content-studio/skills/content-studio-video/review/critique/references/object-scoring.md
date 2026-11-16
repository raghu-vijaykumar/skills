# Score objects and animation against a reference

Give every visible actor a stable ID in the source inventory. Include hero objects, persistent props, faces and secondary actors that explain an action. Keep a reusable asset score for repeated artwork, then rate its animation for each distinct action and pose. Rate a genuinely absent actor as missing. Group incidental repeats only when they share the same art, movement, and purpose.

## Rubric

Use the same criteria and viewing conditions on both sides. Match the scale, action state and viewing area when judging craft, then inspect the real frame to judge staging and legibility. For motion, watch the complete action at real speed and step its anticipation, contact, transition and hold at native cadence. Faces and hands need separate evidence when they matter to the shot.

| Axis | What to inspect |
| --- | --- |
| Appearance · form | Recognizable silhouette, proportions, anatomy, construction details, and believable depth for the object. |
| Appearance · material | Values, texture, highlights, shadows, reflections, and how convincing the intended finish looks. |
| Appearance · staging | Readability at phone size, appropriate detail, scale and clearance, and clear emphasis relative to surrounding props. |
| Motion · mechanics | Pivots, trajectories, weight, easing, contacts, or expressive joints and eyes. |
| Motion · timing | What the action does on its spoken word, gesture or sound cue. Check emphasis and time to read the settled result. |
| Motion · continuity | Identity, pose, depth and lighting through occlusion, camera movement, handoffs and cuts. |

Rate each axis from 1 to 5. Use **1** for a placeholder or hard-to-read action, **2** for a recognizable but simplified study, **3** for solid authored work, **4** for polished and convincing work, and **5** for exceptional clarity and craft at the intended viewing size. Calibrate to the object and style. A technical schematic can score highly by explaining its mechanism clearly. A photorealistic reference calls for convincing surface and depth even if the new assets use a different design.

## Evidence and revision

For each object, record the time range, a crop or still, a motion trace or playback where applicable, and one concrete observation for each side. Fill the scores after review. For every deficit, name the exact change and the render state that verifies it. Retest the same actor against the same reference rating. Keep the appearance and motion totals separate and show any lower axis even when a total improves.

For an asset whose framing changed, use `python scripts/compare_actor.py --reference SOURCE --candidate CUT --map actors.json --out actor-review`. The manifest has an `actors` list with stable `id`, `reference`, and `candidate` fields. Each side declares `seconds` and a normalized `box` in left, top, right, bottom order. Choose moments with equivalent action states. The sheet shows the full composition with the actor outlined and a scaled crop in a separate panel. Occupancy measures the supplied box. Use the crop for form and material, the full frame for staging, and the timed sequence for motion.

For a hardware enclosure, verify depth at the most oblique viewing angle and during the door, card, or tray movement. Check that a wide chassis surface does not cover its front details, the moving part remains seated when closed, and the part that carries the explanation has an independent cue. Inspect the shared asset on both sides of its cut when it persists across shots.

For a recurring presenter, score the held face and hand form separately when both matter. Map a complete gesture from its first motion through the target, cue word and recovery. Check the visible hand at native cadence for finger separation, wrist attachment and overlap with the face or prop. For acting, compare the function of the gaze, expression and gesture to the matching teaching beat, even if the new narration uses different words. An isolated preview shows anatomy and motion. The full narrated frame shows whether the pose directs attention to the right object at the right time.

```text
python scripts/score_objects.py --ledger objects.json --out scores.json
python scripts/score_objects.py --ledger revised-objects.json --previous scores.json --out revised-scores.json
```

The JSON has an `objects` list. Each row has a stable `id`, `reference` and `candidate` (or `null` for an absent candidate), and a `revision` with a retest for any deficit. Each complete side has `evidence`, `observation`, `appearance` with `form`, `material` and `staging`, and `motion` with `mechanics`, `timing` and `continuity`. Use `motion: null` on both sides for an intentionally static prop. The script summarizes authored scores and flags any lower axis. It does not infer scores from pixel differences.
