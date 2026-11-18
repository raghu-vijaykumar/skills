---
name: content-studio-video-object-blur
description: Find a named object in a finished edited video and blur every reviewed appearance through the delivery timeline.
---

# Object blur

Use this leaf when the editor names an object to conceal in a supplied finished edit. Text selects every matching instance by default. An optional frame click selects one instance; reselect after a cut if identity is uncertain. This is a frame-by-frame redaction aid, not a guarantee that a model found every sensitive detail.

Before production analysis or editing, run the mandatory [Content Studio precheck](../../../content-studio-workflow/SKILL.md). Profile the draft and source, benchmark a short model pilot, then show an editable plan with `analyze`, `changes`, timeline commands, actual arguments, duration estimate, outputs, fallback, and full-frame review criterion. Obtain explicit approval of that exact plan. Keep model weights and every draft mask, report, and preview outside this repository.

The v1 route accepts one full-length SDR manual render as an uncut delivery-timeline picture. Internal cuts already present in that render are supported. HDR/Dolby Vision, additional timeline cuts or joins, and other picture effects are unsupported because they would misalign the matte. Audio operations may coexist. The tool does not alter the source.

`scripts/object_blur.py analyze --timeline <v001.json> --target "license plates" --out-dir <draft>/.content-studio/object-blur/run-001` detects the target on every output frame, segments every match, and writes `detections.jsonl`, `frames.jsonl`, a lossless `mask.mkv`, and `analysis.json`. Add `--click FRAME,X,Y` with normalized coordinates to select one object; repeat `--click` after a track loss or cut. Use `--corrections <corrections.json>` to replace boxes or add/exclude normalized mask polygons on named frames. Run a new empty output directory for each correction pass.

Inspect the source, mask and a bounded timeline preview at native delivery size, frame by frame across the entire clip. Correct missed objects, false positives, edge leaks, identity switches, and all flagged frames; then inspect again. The editor writes `coverage-review.json` with their name and review note, source/analysis/mask hashes, `frames_reviewed` equal to `analysis.frames`, and `resolved_frames` equal to `analysis.flagged_frames`. The tool never writes this human record.

`scripts/object_blur.py changes --timeline <v001.json> --analysis <run>/analysis.json --coverage-review <run>/coverage-review.json --out <changes.json>` adds a pending `object-blur` operation. Omit `--coverage-review` only for an unapproved preview revision. Use `timeline.py revise`, `validate`, and a bounded `preview`; after human timeline approval, mark the operation approved in a new revision, obtain its fingerprint approval, render once, and verify the exact master. Validation rejects missing or stale coverage review before export. Any mask correction changes the hash and requires a new review and timeline approval. Publishing remains separately authorized.

See [the capability matrix and review record](README.md).
