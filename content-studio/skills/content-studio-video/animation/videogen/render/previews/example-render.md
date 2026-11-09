# Bounded render example

Illustrative command/output example. `preview-range.mjs` refuses to run without an
explicit frame range.

```powershell
node content-studio/skills/content-studio-video/animation/videogen/render/scripts/preview-range.mjs <project> --from 0 --to 90
node content-studio/skills/content-studio-video/animation/videogen/render/scripts/delivery.mjs <project>
```

The preview route writes bounded evidence; the delivery route is for an approved
review. Inspect hero elements, motion, and audio in the exact rendered output.
