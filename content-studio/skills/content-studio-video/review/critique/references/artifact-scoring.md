# Score the video package

Inventory the selected deliverables before review. Score each generated item against its own evidence and delivery conditions. A review can cover a draft or a proof if it names that scope. Recheck the actual audiovisual result in the full cut.

| Artifact | Review |
| --- | --- |
| Script | Verify facts. Record when the viewer gets a concrete question, what renews curiosity in each chapter, and whether the ending delivers what the opening promises. Timecode repetitive wording, examples, or transitions. |
| Storyboard | Check cue timing, visible cause and effect, framing, and how often the representation changes when the idea calls for it. |
| Hero and animation | Link the exact render's [object checkpoint report](object-scoring.md#production-checkpoints) and retest checklist. Keep per-part and per-action findings visible alongside package-level ratings. |
| Narration | Use the [narration review loop](narration-scoring.md) to score the script and recorded performance by beat, compare fixes, and listen to the exact master. |
| Audio mix | Listen at delivery loudness on headphones and ordinary speakers when available. Check voice balance, noise, dynamics and continuity. Record loudness, peaks and dropouts when measured and review them with the listening evidence. |
| Captions, music, SFX and thumbnail | Review generated items at delivery size or loudness. Check text accuracy, timing and legibility. Check music and SFX fit, cue and balance. Confirm the thumbnail makes a legible promise the video fulfills. |
| Editable source and final master | Verify reproducible source and traceable inputs. Watch the exact master for hook, rehooks, variety, payoff, and continuity through cuts. |

Use **1** for missing or misleading, **2** for a material problem, **3** for clear baseline quality, **4** for polished delivery and **5** for exceptional, evidence-backed craft. The scorer gates factual and caption accuracy at 4 and other axes at 3. It also surfaces blockers and per-axis regressions. Hook, rehook and variety scores concern editorial retention potential. Report audience retention data separately if measured.

For a high-school explainer, also run [teaching scoring](teaching-scoring.md) on the mechanisms and keep the learner checks distinct from creative scores.

## Report

Run `python scripts/score_artifacts.py --ledger artifact-review.json --out artifact-scores.json`. For a revised cut, pass `--previous artifact-scores.json` and a fresh output path. Add `--retests review.md` for a checklist of low scores, pending reviews, and regressions.

- Supply top-level `scope`, `audience`, and `artifacts`. Give each item a stable `id`, a `kind` from the scorer’s `ARTIFACT_AXES`, and `state`. Use `required_ids` to check that planned review entries are present in the initial and revised reports.
- Set generated, inspected items to `scored`. Record `evidence` identifying the file, version or hash, and `ratings` keyed by the kind’s axes. Each rating has a `score` and an `observation` with a timecode, cue, or source line.
- Mark absent or unassessed items `pending`, `not_generated`, or `not_applicable` and give a `reason`. Keep them visible until covered or excluded by the selected scope. Use `blockers` for material failures and give each item needing revision a concrete `retest`.
- Reuse the same IDs and audience on retest. Compare each changed axis. Watch the full export for regressions at shot boundaries and across longer stretches of narration.
