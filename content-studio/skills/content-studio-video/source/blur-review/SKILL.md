---
name: content-studio-video-blur-review
description: Inspect blur candidates and apply only human-approved camera-clip cuts.
---

# content-studio-video-blur-review

Before production edits, complete the mandatory `content-studio-workflow` precheck with the selected method, exact script, output, estimate, fallback, and review criterion. Use `scripts/apply_approved_cuts.py` only after checking `review.csv` and marking `remove=yes` for each approved span. The source preprocessor creates blur evidence without cutting by default. Never interpret a low sharpness score as permission to delete footage. Preserve source and verify the cut output.
