# Delivery timeline contract

## Commands

- `timeline.py init --plan <approved-plan> --source <media> --output <new-master.mp4> --timeline <revision.json>` creates a draft without rendering.
- `timeline.py revise --timeline <revision.json> --plan <current-approved-plan.json> --changes <replacement-fields.json> --out <new-revision.json> --output <new-master.mp4>` creates an immutable successor. The change file replaces complete top-level `picture`, `transitions`, `operations`, or `audio` arrays when those fields are supplied. Both commands snapshot approved plan, approval, and checklist bytes beside their timeline revision.
- `timeline validate --timeline <revision>` checks timing, all source hashes, all method adapters, output safety, and calculated duration; it prints a review summary.
- `timeline fingerprint --timeline <revision>` prints the exact approval fingerprint for human review.
- `timeline.py preview --timeline <revision.json> --start <seconds> --duration <seconds> --output <preview.mp4>` renders a bounded composite review preview without final approval.
- `timeline.py render --timeline <revision.json> --approval <human-record.json>` refuses stale/missing approval, unsupported effects, or overwritten sources before encoding; it writes the final media file named in the timeline and a render record.
- `timeline.py verify --record <render-record.json>` checks the delivered file hash, streams, and duration. Affected-range quality and listening review remains required separately.

## Timing and ordering

Times are half-open `[start,end)` on the resolved picture timeline after cuts. Source times remain available for traceability. Breakpoints split processing at cuts and operation boundaries. Supported geometry precedes denoise/deflicker; upscale precedes color/sharpen and delivery-resolution graphics. Audio assets are mixed and processed before final sample encoding. Stabilization is pending an adapter. Any conflict or unsupported order is an error.

## Approval record

A human-supplied record names `actor: human`, `reviewer`, `review_note`, `approved_at`, and `fingerprint`. The fingerprint includes snapshotted plan, preflight approval and checklist bytes, timeline bytes, referenced asset hashes, and the renderer capability revision. The CLI never creates human approval automatically. A revision requires a new record.

## Compatibility

Existing specialist scripts remain available for bounded diagnosis/preview and existing consumers. They are not the unified final-render route. A method is advertised as timeline-ready only after its adapter and integration evidence pass.
