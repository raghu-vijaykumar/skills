# Selective AI restoration and upscaling

Upscaling reconstructs resolution. It does **not** replace color correction,
exposure correction, or motion-blur repair. AI models can sharpen edges and
invent plausible detail, but they can also hallucinate faces, text, signs, and
fine patterns. Content Studio therefore proposes an enhancement before applying
it.

## Decision flow

```text
analyze source (resolution, sharpness, noise, HDR)
  → render a 5 s Lanczos candidate and a 5 s AI candidate
  → compare detail, noise, clipping, exposure, flicker
  → FIX        measurable gain, no artifacts   → render the clip
  → REVIEW     improvement with a soft warning → wait for approval
  → SKIP       no measurable gain              → use Lanczos if 4K is required
  → UNSUPPORTED HDR/DV, orientation, backend   → leave untouched
```

A clip is never FIX without a preview. `--analyze-only` records the cheap
diagnosis; `--preview` renders the comparison without replacing anything.

## Commands

```powershell
# Diagnose a draft: no rendering, no file changes
content-studio upscale --draft <draft> --target 4k --analyze-only --review

# Render 5 s comparisons for the first five clips and write review links
content-studio upscale --draft <draft> --target 4k --preview --review --limit 5

# Apply only the clips that passed the gate (REVIEW rows wait)
content-studio upscale --draft <draft> --target 4k --review --limit 5

# Accept REVIEW decisions whose previews you checked
content-studio upscale --draft <draft> --target 4k --approve

# Force AI on every clip without analysis (records the override)
content-studio upscale --draft <draft> --target 4k --mode always

# Restrict the batch to clips referenced by an editable timeline
content-studio upscale --draft <draft> --target 4k --timeline .content-studio/rough-cut/edit-timeline.json

# One clip, explicit render
content-studio upscale --input <clip.mp4> --output <clip-4k.mp4> --target 4k --chunk 120
```

The draft batch reads `.content-studio/processed-clips/*/final.mp4`. Those are
the cleaned SDR deliverables, not the HDR originals.

## Gates

Measured on the rendered previews, with Lanczos as the baseline:

| Gate | FIX | REVIEW | Rejected |
|---|---|---|---|
| edge sharpness | ≥ 3 % gain | — | below 3 % → SKIP |
| noise floor | ≤ 1.20× | 1.20–1.50× | > 1.50× |
| temporal change | ≤ 1.35× | 1.35–2.00× | > 2.00× |
| sharpness jitter | ≤ 0.30 | 0.30–0.45 | > 0.45 |
| exposure shift | ≤ 0.12 | — | > 0.12 |
| clipping | no increase | — | any increase |

Temporal change compares adjacent-frame differences of the AI candidate with
those of the Lanczos candidate, so camera motion cancels out and only
model-introduced flicker remains.

## Timestamps and variable frame rate

Phone footage is often variable-frame-rate. The pipeline reads the source frame
timestamps with `ffprobe` and rebuilds the video with a concat demuxer so the
original timing survives. If the probe and decoder disagree about a segment,
the fallback holds each frame for `duration / frame_count`, which keeps audio
synchronization exact and is recorded as `"timing": "uniform_fallback"`.

`--chunk N` processes N frames at a time and keeps only one chunk on disk. The
default is `0` (one pass); use `--chunk 96` or `--chunk 120` for long 4K clips to
bound temporary storage. Chunked runs verify that every chunk's frame count
matches before concatenating.

## HDR and color

- HDR HLG/PQ and Dolby Vision sources are `UNSUPPORTED` unless `--allow-hdr` is
  passed. There is no verified tone-map in this path, so the tool refuses to
  guess.
- 10-bit SDR sources stay 10-bit (`libx265 yuv420p10le`) and keep available
  color tags.
- Vlog batches run on the SDR `final.mp4` produced by preprocess, so no HDR
  round-trip is involved.
- The pipeline records source/output pixel formats and color tags in
  `upscale.json`.

## Models and measured throughput

| Backend | Default | Notes |
|---|---|---|
| ncnn/Vulkan | `realesr-animevideov3` | native 2×/3×/4×; ~0.4 s/frame at 1080p on an RTX 2070 Super |
| ncnn/Vulkan | `realesrgan-x4plus` (opt-in) | general photo model; **22–27 s/frame** at 1080p because it computes 4× internally |
| PyTorch | `realesr-general-x4v3` | lightweight general model with `--denoise-strength`; needs `--weights` |

`realesr-general-x4v3` is not part of the ncnn release. On this machine the
PyTorch stack is CPU-only, so ncnn remains the practical backend and the fast
video model is the default. The gate decides whether it helps; the general model
is one flag away when throughput allows.

PyTorch checkpoints are never downloaded silently. Pass `--weights <file>` and
keep the license record beside it.

## Install

Download the official Windows ncnn/Vulkan release:

```text
https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip
```

The command auto-detects:

1. `--realesrgan <path>`
2. `REALESRGAN_NCNN`
3. `realesrgan-ncnn-vulkan` on `PATH`
4. `<repo>/tmp/realesrgan/realesrgan-ncnn-vulkan.exe`

Verify the model license before commercial use. Real-ESRGAN is BSD-3-Clause and
the ncnn/Vulkan build is MIT; keep their notices with any redistribution.

## Cache and outputs

```text
<draft>/.content-studio/upscale/
  upscale-batch.json          decisions for every clip
  upscale-review.html         table with links to previews
<clip>/upscale-work/
  preview/preview.json        metrics, decision, reasons
  preview/preview.html        three-panel image and both videos
  preview/three-panel.jpg
  preview/preview-lanczos.mp4
  preview/preview-ai.mp4
  upscale.json                full render manifest
  chunk-*.mp4                 chunked inference when --chunk is used
```

`upscale.json` caches on the source SHA-256 plus every render parameter. A
second run with the same source and settings returns `"cached": true` without
re-encoding. The batch keeps `final-pre-upscale.mp4` and only replaces
`final.mp4` after a FIX or an explicit approval.

## Limitations

- No temporal model is bundled. Per-frame upscaling can still flicker; the
  temporal gate catches obvious cases but does not restore motion coherence.
- The general ncnn model is impractically slow at 1080p on this GPU. Use the
  video model or install the PyTorch backend.
- Faces, signs, and text are not separately detected. Review those clips by hand.
- AI upscaling is presentation enhancement, not evidence-grade reconstruction.
