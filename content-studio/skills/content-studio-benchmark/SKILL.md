---
name: content-studio-benchmark
description: Build synchronized native-resolution benchmark grids comparing original, preprocessed, upscaled, and color-corrected video panels. Use to review enhancement checkpoints live.
---

# Content Studio Benchmark

Build one video that shows each enhancement checkpoint side by side without
cropping or downscaling any panel.

```powershell
content-studio benchmark `
  --original <original-with-cuts.mp4> `
  --preprocessed <preprocessed.mp4> `
  --upscaled <upscaled-4k.mp4> `
  --color <color-natural-4k.mp4> `
  --color-warm <color-warm-4k.mp4> `
  --audio <preprocessed.mp4> `
  --output <content-studio-benchmark.mp4> `
  --width 3840
```

The 5-panel vlog layout keeps two 1080p panels in the top row and stacks three
full-width 4K panels below, producing 3840×7560. Panels must have matching
durations within 0.15s; the command rejects mismatches so the comparison stays
synchronized.

Read [the benchmark grid workflow](references/benchmark.md) for layout,
duration, audio, and metadata details.

This skill only assembles review artifacts. It does not preprocess, upscale, or
color-correct footage; use `content-studio-videopreprocess`,
`content-studio-videoedit`, and the upscale/enhance commands for those stages.
