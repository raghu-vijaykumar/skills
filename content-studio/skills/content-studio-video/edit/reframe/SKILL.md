---
name: content-studio-video-reframe
description: Create reviewed portrait reframes from finished or approved video ranges.
---

# content-studio-video-reframe

Before production edits, complete the mandatory `content-studio-workflow` precheck with the selected method, exact script, output, estimate, fallback, and review criterion. Choose one script after the precheck: `subjects.py` for supplied subject boxes, `saliency.py` for visual saliency, or `center.py` for a deliberate center crop. Inspect motion and subject clearance in the output; do not silently switch methods.

For every bounded proposal, run `scripts/framing_evidence.py --source <source> --proposal <proposal>/reframe.json --subjects <reviewed-boxes.json> --output <proposal>/framing-evidence.json` when hero boxes exist; omit `--subjects` for saliency or center. The script measures context lost, sampled hero coverage and movement, and draws 5%/10% destination guide frames over the existing crop preview. It does not infer a hero. Compare original, crop, guide frames, and moving footage at phone size. Reframe-only work keeps this report with its plan evidence; [hero-led clipping](../clipping/SKILL.md) also binds it into its selection and timeline handoff. A `REVIEW` candidate or `UNSUPPORTED` hero coverage needs a human framing decision before export.
