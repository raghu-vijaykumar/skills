# Score how a video teaches

After watching the exact cut at normal speed, evaluate each teaching beat against what its intended learner should be able to explain. Use the [object rubric](object-scoring.md) for form, materials, staging, and motion craft. Use this rubric for whether those visuals teach the correct mechanism.

| Axis | Check at intended delivery size |
| --- | --- |
| Accuracy | Parts, axes, labels, direction, counts, and stated cause match the documented mechanism. Mark illustrative or uncertain views. |
| Causality | The initial state, action, and result are visible in order. A viewer can tell what changed and why. |
| Motion readability | The meaningful movement reads at normal speed. Camera motion, overlays, labels, and timing leave the key contact or settled result readable. |
| Language | The narration or text names visible parts, explains unfamiliar terms when needed, and cues the exact action in language the target audience can follow. |

Use **1** for a missing or misleading lesson, **2** for a lesson that depends on guessing, **3** for a clear basic explanation, **4** for a grounded explanation with a readable result, and **5** when the beat makes the mechanism independently explainable and transferable. Record the evidence and a concrete observation behind every score. The default gate is accuracy at least 4 and every other axis at least 3. Factual errors and misleading motion block readiness regardless of average.

For a high-school audience, write three short checks per beat. Ask the viewer to **identify** a visible part or state, **predict** the result of a small change, and **explain** the cause in their own words. Set the expected answer before showing the clip. Record actual learner responses only when observed. Keep the check open when reviewing alone. In an iterated cut, keep the objective and questions fixed.

## Ledger and retest

Run `python scripts/score_teaching.py --ledger teaching.json --out teaching-report.json`. For a new cut add `--previous teaching-report.json` and choose a fresh output path.

- Top level takes `audience`, `render` with exact file evidence or manifest, and a nonempty `beats` list.
- Each beat takes `id`, `objective`, timecoded `evidence`, and `axes` keyed by `accuracy`, `causality`, `motion_readability`, and `language`. Each axis has `score` and `observation`.
- Use `blockers` for factual or misleading-motion issues and `retest` for the concrete correction and expected evidence whenever a score is below its floor, a blocker remains, or a learner check fails.
- Supply `checks` keyed by `identify`, `predict`, and `explain`. Each has `question` and `expected`. Add `learner_result: {"met": true, "evidence": "observed response"}` only after a learner answers.
- Compare axis changes independently. An editorial pass keeps the shot ready for review. A learner demonstration describes the recorded checks for that specific render.
