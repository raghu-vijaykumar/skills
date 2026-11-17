# Score objects and animation against a reference

Give every visible actor a stable ID in the source inventory. Include hero objects, persistent props, faces and secondary actors that explain an action. Keep a reusable asset score for repeated artwork, then rate its animation for each distinct action and pose. Rate a genuinely absent actor as missing. Group incidental repeats only when they share the same art, movement, and purpose.

## Production checkpoints

1. **Storyboard.** Save an inventory of stable hero, moving-part, and action IDs. Record the reference and expected start, action, contact and settled states for each. Use separate IDs for independent joints, rotors, layers, or repeated actions with different cues. Name inherited motion under its parent. Use traceable real images for physical objects and people, including stylized treatments. For fictional designs or schematics, record visual sources for real features and use the reviewed design or documented behavior to define the comparison target.
2. **Proof.** Inspect isolated assets at matching angles, then watch the full action in the narrated composition at delivery size. Score all in-scope IDs and save the report and retests. For 2D, inspect contours, anatomy, rig joints and overlaps. For 2.5D, inspect layer depth, parallax, masks and edge reveals through the camera move. For 3D, inspect pivots, contact, clearance, occlusion and surface response. All three use the same six axes.
3. **Fix and rescore.** For each gap, record the ID, time or cue, observed problem, proposed source-level change and what visible result would pass. Within the approved plan, compare the smallest useful rerender with the previous cut and the original benchmark. Watch at normal speed and step through the entire affected action at native cadence. Keep the better version and repeat within the plan's iteration budget. Bring unresolved evidence, regressions or exhausted retries to the existing human review checkpoint with the last comparison and open fix.
4. **Exact master.** Run the same scorer on the encoded export with the full delivery inventory. Compare intersecting IDs with the latest comparable proof or master report, check cue sync and seams, and rescore from the master frames. Report individual scores, changes and remaining issues alongside the package scorecard. A short proof covers its own inventory only.

In the precheck, name `score-objects`, its exact checkpoint commands, output paths and acceptance criteria. Put the score report, retest checklist and source/previous/current evidence in the approved step outputs. At scene proof and exact-master human review, show those files and any unresolved issues.

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

For a retest, add `--previous EARLIER_CUT` and put a `previous` sample with its own `seconds` and `box` on each actor. The sheet reads source, previous and candidate. The evidence fingerprints every input. Use the middle column to verify the revision gained the intended quality and to spot changes to framing and contrast before changing the score. For movement, use the [three-lane frame trace](frame-tracing.md) to compare the complete action across the same cuts and check the actual onset, contact and result.

For a hardware enclosure, verify depth at the most oblique viewing angle and during the door, card, or tray movement. Check that a wide chassis surface does not cover its front details, the moving part remains seated when closed, and the part that carries the explanation has an independent cue. Inspect the shared asset on both sides of its cut when it persists across shots.

Use [paired detail crops](frame-tracing.md) when a hand covers a prop, a lid swings, or a tray slides into a rack. Compare the same contact before and after its cue. Use the full frame to score whether the small interaction reads during playback.

When several changes happen within the same shot, map their [landmarks](frame-tracing.md) by the visible action. Choose the arrival, contact or activation, and settled result. Jump to matching events in both lanes before judging timing, even when the word, pause, or camera cut differs between versions.

For a large number, status, or decision, use a paired hold interval after the entry settles. Time how long the result is legible in each cut, then check the full sheet and sequence for crowding, competing motion, or an early exit. Judge staging and timing from that evidence alongside the moment of first reveal.

For a recurring presenter, score the held face and hand form separately when both matter. Map a complete gesture from its first motion through the target, cue word and recovery. Check the visible hand at native cadence for finger separation, wrist attachment and overlap with the face or prop. For acting, compare the function of the gaze, expression and gesture to the matching teaching beat, even if the new narration uses different words. An isolated preview shows anatomy and motion. The full narrated frame shows whether the pose directs attention to the right object at the right time.

```text
python scripts/score_objects.py --ledger objects.json --out scores.json
python scripts/score_objects.py --ledger revised-objects.json --previous scores.json --out revised-scores.json --retests retests.md
```

The JSON has an `objects` list. Each row has a stable `id`, `reference` and `candidate` (or `null` for an absent candidate), and a `revision` with a retest for any deficit. Each complete side has `evidence`, `observation`, `appearance` with `form`, `material` and `staging`, and `motion` with `mechanics`, `timing` and `continuity`. Use `motion: null` on both sides for an intentionally static prop. Use `review_note` with a `revision` to keep a material open problem visible regardless of the scores. If the part is too obscured to score or has yet to be inspected, pair the note with `candidate: null`. The script summarizes reviewer-assigned scores.

For a production checkpoint, add the storyboard inventory as JSON, for example `{"ids":["cooler-lift","bracket-fan-spin","far-fan-spin"]}`. Record the reviewed render's SHA-256 in the ledger's top-level `render_sha256`. Run the scorer on each proof or master file.

```text
python scripts/score_objects.py --checkpoint proof --inventory proof-parts.json --render proof.mp4 --ledger proof-objects.json --out proof-scores.json --retests proof-retests.md
python scripts/score_objects.py --checkpoint master --inventory master-parts.json --render final.mp4 --ledger master-objects.json --previous proof-scores.json --out master-scores.json --retests master-retests.md
```

Use a new output path for each pass. The checkpoint rejects omitted inventory IDs and a mismatched render hash. A valid report with open parts or regressions exits with code `2` and still writes the report and checklist. Keep comparably reviewed axes stable across passes. The report carries an unresolved regression target into the next retry, even if the new score still meets the original benchmark. When a deliberate tradeoff requires human review, surface both versions and the open finding in the checkpoint evidence.

The optional Markdown checklist starts with missing actors, then sorts open retests by the sum of their lower axes. It also flags any axis that fell since the preceding review. Use it to choose the next cut to revise, taking into account how long the actor remains on screen and whether the deficit changes what the viewer understands. Regenerate the checklist from the new evidence-backed ledger after each pass.

For a new topic, the [real-world photo workflow](photo-reference.md) supports still-to-render comparisons and a separate motion basis. The report uses `review` when appearance meets its target and motion evidence remains open. If appearance also has a deficit, the result remains `improve` and names the pending motion basis in the checklist. A newly established motion basis starts its own baseline and preserves the existing appearance comparison.
