# Reference critique

## Capability matrix

| Method | Status | Input → output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `mapped-evidence` | Supported | Two local renders and a beat map → paired GIFs, timed frame sheets, coverage, and optional abrupt-change timestamps | Specialist only | [Synthetic render test](tests/test_compare.py) | Cut candidates need visual confirmation. Comparison artifacts remain private. |
| `frame-trace` | Supported | One mapped beat → consecutive frame index, viewer, region change percentages, and optional seam, landmark, hold and detail sheets | Specialist only | [Frame and trajectory tests](tests/test_frame_trace.py) | Reviewers supply each lane's event times, holds and fixed detail boxes. Change percentages flag inspection windows. |
| `track-objects` | Supported | Frame trace and object seeds → tracks, optional pan or uniform zoom compensated drift, and optional Remotion keyframes | Specialist only | [Frame and trajectory tests](tests/test_frame_trace.py) | Local texture matching needs reseeding across substantial shape changes and cuts. |
| `audit-word-cues` | Supported | Word-motion timeline and optional encoded video → coverage, cue signature, onset sheets, and regional change percentages | Specialist only | [Word cue tests](tests/test_word_cues.py) | Compare cue signatures for an art swap. Inspect the rendered actor and listen to the narration to judge timing. |
| `survey-reference` | Supported | One reference video → complete-duration review windows and actor inventory template | Specialist only | [Reference survey test](tests/test_reference_survey.py) | Candidate cuts and sampled motion need visual interpretation. |
| `score-objects` | Supported | Evidence-backed ratings → appearance and motion scores, deficits, revision deltas, and an optional ranked retest checklist | Specialist only | [Object scoring tests](tests/test_score_objects.py) | Scores reflect the reviewer's rubric and paired evidence. |
| `compare-actor` | Supported | A source, a rendered actor moment and an optional previous render → full-frame and scaled crop evidence | Specialist only | [Actor comparison tests](tests/test_compare_actor.py) | Supply each lane’s sample and box. Motion still needs consecutive frames. |
