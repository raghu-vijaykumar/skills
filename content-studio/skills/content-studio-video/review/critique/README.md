# Reference critique

## Capability matrix

| Method | Status | Input → output | Delivery timeline | Evidence | Limits |
| --- | --- | --- | --- | --- | --- |
| `mapped-evidence` | Supported | Two local renders and a beat map → paired GIFs, timed frame sheets, coverage, and optional abrupt-change timestamps | Specialist only | [Synthetic render test](tests/test_compare.py) | Cut candidates need visual confirmation. Comparison artifacts remain private. |
| `frame-trace` | Supported | One mapped beat → consecutive frame index, viewer, and region change percentages | Specialist only | [Frame and trajectory tests](tests/test_frame_trace.py) | Change percentages flag inspection windows. |
| `track-objects` | Supported | Frame trace and object seeds → tracks and optional Remotion keyframes | Specialist only | [Frame and trajectory tests](tests/test_frame_trace.py) | Local texture matching needs reseeding across substantial shape changes and cuts. |
| `audit-word-cues` | Supported | Word-motion timeline and optional encoded video → coverage, onset sheets, and regional change percentages | Specialist only | [Word cue tests](tests/test_word_cues.py) | Image differences flag review windows. Read the shot and compare audible and visible timing. |
