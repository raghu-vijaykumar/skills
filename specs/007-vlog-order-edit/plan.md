# Implementation plan

1. Use the existing eight-column `_timeline.csv` contract. Compare it with draft-root camera files, probe new files, infer a local UTC offset, and assign capture-time numbers through collision-safe two-phase renames.
2. Refresh ordering in the draft preprocessing and join entry points. Key per-clip processing folders by original camera basename so later inserts do not orphan reports.
3. Add FFmpeg trim and cut filter graphs with audio, output validation, source color preservation, and an explicit SDR path for Dolby Vision.
4. Normalize join inputs to a common SDR format, then concatenate in timeline or explicit input order. Use enhanced audio when a Dolby Vision source has only a voice sidecar.
5. Cover ordering, actual media editing, and safety behavior with focused tests; document commands in the vlog skill.
