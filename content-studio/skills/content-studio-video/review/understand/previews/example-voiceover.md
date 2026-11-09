# Voiceover draft example

Illustrative structure, not an approved script. Timestamps must come from the approved
edit and every visual claim must cite an observed frame.

```json
{
  "id": "v01",
  "start": 0.0,
  "end": 4.0,
  "text": "Synthetic narration text for the matrix example.",
  "evidence_frame_ids": ["frame-0000", "frame-0001"],
  "needs_review": true,
  "notes": "Illustrative only; replace with verified observations."
}
```

The validator rejects overlapping segments, out-of-range times, unknown evidence frames,
and speech over the pace limit.
