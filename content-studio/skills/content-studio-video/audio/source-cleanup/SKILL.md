---
name: content-studio-video-source-cleanup
description: Compare camera-source speech cleanup methods before manual editing.
---

# content-studio-video-source-cleanup

Before production edits, complete the mandatory `content-studio-workflow` precheck with the selected method, exact script, output, estimate, fallback, and review criterion. After diagnosing an audible issue, choose `deepfilter.py`, `afftdn.py`, or `keep_source.py`; each is a distinct entrypoint to the maintained source-preparation engine. These scripts prepare a clip and may also write its blur review report. Compare candidate WAVs and verify the exact processed clip; skip denoise when the source is already clean.
