# Score, fix and rescore narration

1. **Internal script analysis.** List stable windows for the opening, chapter transitions, dense stretches and payoff. Give each window a viewer question or an intended change in understanding. Score the full script for accuracy, hook, rehooks, clarity, variety and payoff. Score each planned window for clarity, story progress and spoken cadence. Compare adjacent windows to catch repeated setups, information and sentence patterns. Resolve factual and timing issues internally, then present the complete playable narration for the editor's listening review. Share the written script if requested.

   Use the advisory rhythm report before synthesis to locate runs of long phrases and repeated openings. For shorts, a brief line can mark a real turn. For a long explainer, check whether each chapter answers a question and earns the next one. Preserve a long explanation when the mechanism needs it; do not add a short line solely to satisfy a pattern.
2. **Voice proof.** Listen to the isolated take and the narrated picture at normal speed. Rate each window for intelligibility, pacing, emphasis, variety and sync. For **every cue**, inspect its boundary/middle frames, record the visible scene and visual start/end, then check that its spoken meaning and first/last audible words stay in that scene. A generic venue fact over an unrelated shot is a mismatch. Compare neighboring phrases for repeated pitch contours, stress, pauses and energy. Mark unlistened audio, missing frame evidence, or unavailable picture sync as pending until the evidence is available.

   Confirm that a written pivot is audible through a natural pause or emphasis. If the line works on paper but the synthetic or recorded take sounds flat or rushed, revise the wording or retake it at normal speed and compare the adjacent phrases.
3. **Fix and retest.** Write the timecode, specific defect, change to make and audible or visible result that would pass. Within the approved scope, rewrite or shorten a mismatched line, regenerate its take at 1.0x, and compare it with the retained version at similar loudness, including adjacent beats. Do not use speed changes to fit a visual window. Rescore and carry unresolved findings forward. Keep the stronger take and use the existing proof review for choices that need human judgment.
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
- For each rated axis, locate the script line or audio time range and describe the observed issue or strength. Score `story_progress` by the planned role of the beat, such as creating curiosity, answering a question or delivering the payoff. Score `cadence` by how the words read aloud. A passing `sync` score requires both visual meaning match and audio inside the reviewed start/end; include the cue sheet and picture version in the evidence. Record the actual recording and picture versions in the performance evidence.
- Compare against the best retained take when a retry is weaker. Keep its report as the baseline until a new candidate improves the window. Add the listening evidence and exact fix to `retest`.

```text
python scripts/score_artifacts.py --ledger narration-v1.json --out narration-scores-v1.json --retests narration-retests-v1.md
python scripts/score_artifacts.py --ledger narration-v2.json --previous narration-scores-v1.json --out narration-scores-v2.json --retests narration-retests-v2.md
```
