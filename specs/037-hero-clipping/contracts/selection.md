# Selection and timeline handoff contract

## Local record

Versioned selection JSON files live under the draft's `.content-studio/clipping/` directory. The `clipping.py` validator checks current source and evidence bytes. An abbreviated illustrative record:

```json
{
  "schema": "content-studio.hero-clipping.v1",
  "source": {"path": "../../long-form-final.mp4", "sha256": "<actual hash>",
             "duration": 154.0, "width": 1920, "height": 1080,
             "fps": 30.0, "color_transfer": "bt709", "has_audio": true},
  "hero": "The main object and its visible action",
  "candidates": [{"id": "c001", "source_in": 120.0, "source_out": 154.0,
                  "story_notes": "", "sound_boundary_notes": ""}],
  "selected": {"source_in": 120.0, "source_out": 154.0},
  "evidence": {"manifest": "selection-v001-source-review/evidence.json", "manifest_sha256": "<actual hash>",
               "frame_ids": ["f0000", "f0001"]},
  "crop_intervals": [
    {"source_in": 120.0, "source_out": 154.0,
     "method": "subjects", "target_width": 1080, "target_height": 1920,
     "x": 0.34, "y": 0.0, "w": 0.316406, "h": 1.0,
     "proposal_file": "crop-v001/reframe.json", "proposal_sha256": "<actual hash>",
     "preview_file": "crop-v001/reframe-review.html",
     "review_status": "pending_review", "review_note": ""}
  ],
  "editorial_review": {"status": "pending_review", "reviewer": "", "note": ""},
  "status": "pending_review"
}
```

The sample values are illustrative and are never valid approval evidence. Source and evidence paths are relative to the selection JSON. A record rejects a missing or changed source, nonpositive/out-of-bounds ranges, gaps/overlaps in complete crop coverage, crop rectangles outside 0–1, stale proposal bytes, and an aspect ratio that does not match the target portrait frame within tolerance. During proposal building, a final uncovered suffix is allowed; `validate --ready` requires full coverage and editor review.

## Leaf commands

`scripts/clipping.py` exposes `inspect`, `propose-crop`, `validate`, and `emit-changes`. `validate --selection <selection.json> --source <video> --ready` checks the reviewed record and exact source/evidence bytes. `emit-changes --selection <selection.json> --timeline <timeline-v001.json> --out <changes.json>` requires the current approved preflight plan and a reviewed selection; it cannot mark timeline operations approved.

## Handoff

After preflight approval, the script converts the reviewed selection into replacement `picture` and `operations` arrays for `timeline.py revise`. Each picture entry points at the original long-form source and its approved source interval. Each crop operation targets its resolved output interval and carries absolute selection/proposal/source-evidence paths plus hashes. Timeline validation checks those evidence bytes, source hashes, timing, method support, and approval state. The script does not write a human approval record.

The first version may split the one contiguous source range at a reviewed crop boundary, keeping adjacent source intervals without omitted frames. A visually jarring crop jump fails preview review. If no stable reviewed crop keeps the hero and context legible, mark the proposal `REVIEW` or `UNSUPPORTED` instead of exporting it as a successful hero crop.
