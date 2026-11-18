# Existing capability and gaps

## Reuse

- `review/understand/scripts/understand.py` produces source-hashed, timestamped frames and contact sheets for the full source or a bounded neighborhood. Sparse frames are discovery evidence, not proof of every hero appearance.
- `edit/reframe/scripts/subjects.py` accepts supplied subject boxes and produces one stable crop proposal with review images and JSON. `saliency.py` and `center.py` are alternative proposals, not semantic hero recognition. None produces a delivered portrait master.
- The delivery timeline already accepts source `source_in`/`source_out`, normalized `crop` geometry, portrait output dimensions, source audio, preview, approval, render, and verify.
- `content-studio-workflow` already profiles media, binds a human-reviewed plan to exact commands, and tracks checklist evidence.

## Gap for this feature

No canonical skill currently owns the editorial choice of a hero-led moment, its source-linked selection record, the review of complete action and sound, and the handoff of a chosen crop into one approved portrait timeline. The new leaf should coordinate those decisions without duplicating the existing crop estimator or renderer.

## Decision

Start with human-reviewed selection and stable crop intervals. Use a bounded crop preview before timeline approval. Do not run AutoCut unless separately requested. Smooth tracking, automatic hero search, HDR/Dolby Vision picture processing, and platform publication are later or separate work.
