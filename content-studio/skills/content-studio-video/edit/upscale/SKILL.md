---
name: content-studio-video-upscale
description: Compare and, when justified, upscale one completed edited video before overlays.
---

# content-studio-video-upscale

Before production edits, complete the mandatory `content-studio-workflow` precheck with the selected method, exact script, output, estimate, fallback, and review criterion. Use `scripts/compare.py` on bounded ranges of the finished manual or voiced edit, then choose exactly one of `lanczos.py`, `real_esrgan.py`, or `pytorch.py` after the approved precheck. These entrypoints reject draft-batch and timeline-range flags. Skip clean or already sufficient footage. Check HDR/Dolby Vision before a tone map, preserve audio, and verify detail, noise, flicker, timing, and exact output. Render code graphics only after this stage.
