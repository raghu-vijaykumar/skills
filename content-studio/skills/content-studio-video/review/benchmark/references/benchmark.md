# Content Studio benchmark grid

Build one synchronized video that shows each enhancement checkpoint side by
side. The layout preserves native resolution and never crops a panel.

## Command

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

## Layout

For the 5-panel vlog benchmark:

```text
3840 px wide
┌──────────────────────┬──────────────────────┐
│ 1 ORIGINAL 1920×1080 │ 2 PREPROCESSED 1920×1080 │
├──────────────────────┴──────────────────────┤
│ 3 UPSCALED 4K          3840×2160            │
├─────────────────────────────────────────────┤
│ 4 COLOR 4K             3840×2160            │
├─────────────────────────────────────────────┤
│ 5 COLOR WARM 4K        3840×2160            │
└─────────────────────────────────────────────┘
Total: 3840×7560
```

- 1080p panels stay 1080p.
- 4K panels stay 4K.
- Nothing is cropped.
- Top-row panels are placed side by side; full rows are stacked below.
- Labels identify each checkpoint.

All panels must have the same duration within 0.15s. Generate them from the same
base edit. A duration mismatch is rejected because the comparison would fall out
of sync.

## Audio

Use the preprocessed audio by default so every panel shares the cleaned
soundtrack. The source track is copied into the grid.

## Output

`benchmark.json` records panel labels, paths, native sizes, output size, audio,
and duration.

The benchmark is a review artifact. It does not modify any source or panel.
