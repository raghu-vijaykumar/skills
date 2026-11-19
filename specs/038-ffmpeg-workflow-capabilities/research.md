# Research: FFmpeg workflow capabilities

## Existing ownership

- `content-studio-workflow` profiles sources, capacity, and bounded decode/scale estimates, but its probe reads the first video stream only and its tool check is executable presence.
- `timeline` validates immutable revisions, full SHA-256 asset identity, approved methods, and one final FFmpeg export for its current SDR adapter set; HDR/DV picture processing remains refused.
- `review/final-render` names exact-master review but has no dedicated content-defect method. Timeline verification currently checks output identity, geometry, duration, sample rate, and selected loudness, then extracts affected-range evidence.
- `edit/clipping` already owns hero-led excerpt selection and handoff; `edit/reframe` owns subject, saliency, and center crop choices. Neither needs a new generic fit skill.
- `audio/mastering` already uses measured two-pass EBU R128 for standalone files; the timeline's `loudnorm` expression is single-pass.
- `edit/autocut` already analyzes scenes and silence for an explicit experimental rough-cut request. This feature does not make it the raw-folder default.

## External reference decisions

- FFmpeg Skill's `probe`, `doctor`, `check`, `caption`, `sync`, `cut --smart`, and retime tools provide behavior examples. The implementation will remain locally owned and governed by Content Studio approvals.
- Its `render.py` executes several intermediate stages; using it for final delivery would conflict with the one-export timeline target.
- Platform upload limits change. The final checker will report dated or caller-supplied limits as guidance, while stream facts and measured defects are current-file evidence.
- A contact sheet or motion centroid cannot identify the semantic hero. Subject boxes and editorial decisions remain human-reviewed.
- A smart cut is only valuable for a compatible cuts-only path. A post-cut picture filter would force another encode.
- HDR/Dolby Vision tags alone do not prove RPU preservation; the existing packet-copy verification remains the preservation route.

## Open engineering checks

- Measure practical VFR detection costs and avoid full-file frame scanning in preflight.
- Prove exact-master defect detectors against clean and intentional-black controls to tune review thresholds.
- Validate caption font coverage on the installed FFmpeg build and representative Kannada/English cues.
- Validate sync confidence on dialogue and ambiguous music; never turn a low-confidence offset into an automatic edit.
- Measure smart-cut packet reuse and boundary accuracy on GOP variants before advertising the method as supported.
