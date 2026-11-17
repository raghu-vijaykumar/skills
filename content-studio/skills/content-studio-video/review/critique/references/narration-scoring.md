# Score, fix and rescore narration

1. **Script and storyboard.** List stable windows for the opening, chapter transitions, dense stretches and payoff. Give each window a viewer question or an intended change in understanding. Score the full script for accuracy, hook, rehooks, clarity, variety and payoff. Score each planned window for clarity, story progress and spoken cadence. Compare adjacent windows to catch repeated setups, information and sentence patterns. Bring the script scores and unresolved edits to the script review.
2. **Voice proof.** Listen to the isolated take and the narrated picture at normal speed. Rate each window for intelligibility, pacing, emphasis, variety and sync. Compare neighboring phrases for repeated pitch contours, stress, pauses and energy. Check for a clear cue and enough time to register the result. Mark unlistened audio or unavailable picture sync as pending until the evidence is available.
3. **Fix and retest.** Write the timecode, specific defect, change to make and audible or visible result that would pass. Within the approved scope, make a bounded rewrite, delivery or timing change. Compare the new take and the retained version at similar loudness, including the adjacent beats. Rescore and carry unresolved findings forward. Keep the stronger take and use the existing proof review for choices that need human judgment.
4. **Exact master.** Listen through the encoded cut. Re-evaluate the scored windows, wording changes, cue offsets, joins, and whether the ending delivers the opening promise. Link the scored report, retest checklist and isolated comparisons to the exact master review. Track measured audience retention separately when it becomes available. Editorial ratings describe retention potential.

| If the score is low | Change and retest |
| --- | --- |
| Opening hook | Lead with a concrete problem, consequence or surprising result the video can show. Check whether the opening makes the question and stakes clear. |
| Rehook or story progress | At a chapter transition, show the consequence of the previous answer or introduce the next unresolved question. Check that the new beat adds information and earns the transition. |
| Flat or repetitive delivery | Rewrite repeated sentence shapes. Vary phrase length, stress, pauses and emphasis as the meaning changes. Rerecord or regenerate the affected passage and listen across both joins. |
| Pacing, intelligibility or late visual cue | Shorten a crowded phrase, correct pronunciation or give a key word more room. Realign the revised audio and verify against picture. For Rapid Take, regenerate the word clock and check affected object actions. For an explainer, preserve the time needed to follow the mechanism. |
| Weak payoff | Bring back the opening example and show what the viewer can now explain or predict. Check whether a first-time viewer can connect the ending to the promise. |

## Use the artifact scorer

- Keep the audience and scope stable across passes. Include the full script row plus a `script_beat` and a `narration` row for each planned window. For example, use `opening.script` and `opening.voice`. Put them in `required_ids` and use `pending` for evidence that has yet to be reviewed.
- For each rated axis, locate the script line or audio time range and describe the observed issue or strength. Score `story_progress` by the planned role of the beat, such as creating curiosity, answering a question or delivering the payoff. Score `cadence` by how the words read aloud. Record the actual recording and picture versions in the performance evidence.
- Compare against the best retained take when a retry is weaker. Keep its report as the baseline until a new candidate improves the window. Add the listening evidence and exact fix to `retest`.

```text
python scripts/score_artifacts.py --ledger narration-v1.json --out narration-scores-v1.json --retests narration-retests-v1.md
python scripts/score_artifacts.py --ledger narration-v2.json --previous narration-scores-v1.json --out narration-scores-v2.json --retests narration-retests-v2.md
```
