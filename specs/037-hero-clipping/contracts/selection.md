# Selection and timeline handoff contract

## Proposed local record

`selection.json` lives under the draft's `.content-studio/clipping/` directory. The exact schema will be validated by the new leaf script and covered by tests. An illustrative v1 record:

```json
{
  "schema_version": 1,
  "source": {"path": "long-form-final.mp4", "sha256": "<actual hash>"},
  "hero": "The main object and its visible action",
  "selected": {"source_in": 120.0, "source_out": 154.0},
  "evidence": {"frames": ["frame-0120", "frame-0137", "frame-0153"], "audio_review": "pending"},
  "crop_intervals": [
    {"source_in": 120.0, "source_out": 154.0,
     "method": "subjects", "x": 0.34, "y": 0.0, "w": 0.316, "h": 1.0,
     "review_status": "pending_review"}
  ],
  "status": "pending_review"
}
```

The sample values are illustrative and are never valid approval evidence. A record must reject a missing or changed source, nonpositive/out-of-bounds ranges, gaps/overlaps in crop coverage, crop rectangles outside 0–1, and a crop whose aspect does not match the target portrait frame within a defined rounding tolerance.

## Proposed leaf commands

The new `scripts/clipping.py` exposes `validate --selection <selection.json> --source <video>` for read-only source/range/crop checks and `emit-changes --selection <selection.json> --timeline <timeline-v001.json> --out <changes.json>` for a pending timeline handoff. These are implementation targets, not commands available in the current repository. `emit-changes` must require the current approved preflight plan and a reviewed selection; it cannot mark timeline operations approved.

## Handoff

After preflight approval, the new script converts the reviewed selection into replacement `picture` and `operations` arrays for `timeline.py revise`. Each picture entry points at the original long-form source and its approved source interval. Each crop operation targets its resolved output interval. The timeline's existing validator checks asset hashes, timing, method support, and approval state; the new script must not write a human approval record.

The first version may split the one contiguous source range at a reviewed crop boundary, keeping adjacent source intervals without omitted frames. A visually jarring crop jump fails preview review. If no stable reviewed crop keeps the hero and context legible, mark the proposal `REVIEW` or `UNSUPPORTED` rather than exporting it as a successful hero crop.
