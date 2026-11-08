---
name: content-studio-video-restoration
description: Apply diagnosis-first picture denoise, deflicker, lens correction, sharpening, or refinement.
---

# content-studio-video-restoration

Before production edits, complete the mandatory `content-studio-workflow` precheck with the selected method, exact script, output, estimate, fallback, and review criterion. Choose one exact method script and compare it with untouched source. Available scripts are `denoise_light.py`, `denoise_medium.py`, `denoise_nlmeans.py`, `deflicker.py`, `lens.py`, `sharpen_light.py`, `sharpen_medium.py`, and `refine.py`. A deblur model is not implemented; conservative sharpening cannot recover missed focus. Review temporal side effects and the delivered output.
