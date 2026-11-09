# Reflection decision example

The committed `previews/contact-sheet.jpg` is the actual contact sheet from a synthetic
source; detection returned `SKIP` for both scenes because no candidate rose above
threshold. That is a real negative result, not a demonstration of removal.

```text
scene-001: SKIP (candidate 0.000, glare 0.000, veil 0.000)
scene-002: SKIP (candidate 0.000, glare 0.000, veil 0.000)
decision: leave the source unchanged
```

`fix` renders only approved minor glare/veil scenes. `preview` renders a bounded
comparison for REVIEW/UNSUPPORTED scenes. `benchmark` evaluates an external licensed
backend. `ai` runs the optional DSRNet review pass and always returns review_required.
`generative-removal` is unsupported; no generative backend is bundled.
