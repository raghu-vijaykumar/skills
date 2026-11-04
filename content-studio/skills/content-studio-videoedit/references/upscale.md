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

# Render only the timeline's used ranges (one decision per clip, one asset per range)
content-studio upscale --draft <draft> --target 4k --timeline .content-studio/rough-cut/edit-timeline.json --timeline-ranges --preview --review
content-studio upscale --draft <draft> --target 4k --timeline .content-studio/rough-cut/edit-timeline.json --timeline-ranges --approve --write-timeline .content-studio/rough-cut/edit-timeline-upscaled.json

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

## Timeline range rendering

`--timeline-ranges` reads the video tracks of an editable timeline, merges
adjacent `source_in`/`source_out` ranges per clip, and renders one asset per
used range under `<clip>/upscaled/`. The decision is made once per clip from a
5 s preview, then applied to every range of that clip, so a 10-minute video is
not previewed 40 times.

`--write-timeline <path>` writes a copy of the timeline whose used clips point
at those assets and whose `enhancements` list gains
`{stage: "upscale", model, backend, denoise_strength, source_range,
review_status}`. The original timeline is never modified. The mapping is also
recorded in `.content-studio/upscale/timeline-map.json`.

## Speed and thermal limits

Measured on a 96-frame / 3.2 s window at 1080p → 4K:

| Stage | Time | Note |
|---|---|---|
| probe + extract | 1.4 s | PNG decode, one pass |
| inference (cool) | 0.75 s/frame | `general-x4v3`, FP16, tile 256 |
| inference (sustained) | ~2.5 s/frame | GPU reaches 93 °C, throttles to 1140/2100 MHz |
| frame staging | 0.035 s/frame (JPEG q95) | PNG was 0.76 s/frame — 22× slower |
| 4K encode | 3.7 s / 8.5 s (NVENC p5) | libx265 medium: 21.4 s |

JPEG staging plus NVENC removed most of the non-inference overhead, but on this
laptop-class GPU **thermals now dominate**. Rough 10-minute estimates:

| Mode | Estimate |
|---|---|
| PyTorch general, cool bursts | ~4 h |
| PyTorch general, sustained (measured) | ~12 h |
| ncnn `realesrgan-x4plus` | ~12 h+ (22–27 s/frame) |
| Timeline ranges only (~3 min used) | minutes |

If long renders matter, improve cooling/power limits first, use the general model
only on clips the gate marks FIX, and process fewer timeline ranges. The anime
model is animation-only and is never auto-selected for live footage.

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

Measured on clip 001 (1080p SDR → 4K, 5 s window, RTX 2070 Super, 8 GB):

| Backend | Model | Detail vs Lanczos | Inference | Peak VRAM |
|---|---|---|---|---|
| PyTorch CUDA | `realesr-general-x4v3` (denoise 0.5) | **+25.7 %** | 0.75–2.5 s/frame | 679 MB |
| ncnn/Vulkan | `realesr-animevideov3` (animation only, never auto) | +14.1 % | 0.40 s/frame | — |
| PyTorch CUDA | `RealESRGAN_x2plus` | +9.2 % | 3.1 s/frame | 347 MB |
| ncnn/Vulkan | `realesrgan-x4plus` (default ncnn) | not run | 22–27 s/frame | — |

When CUDA torch and the verified weights are present, the default backend is
**PyTorch with `realesr-general-x4v3`**. Without those, the ncnn backend defaults
to the general `realesrgan-x4plus`, then Lanczos. The anime model is available
only through an explicit `--model` and is never chosen for live footage.

The denoise strength blends `realesr-general-x4v3.pth` with
`realesr-general-wdn-x4v3.pth`: `0` keeps the sharper model, `1` uses the
denoise-trained weights, and the default is `0.5`.

## Installing the PyTorch stack

CUDA torch (cu128 wheels work with the 610.x driver):

```powershell
python -m pip install --index-url https://download.pytorch.org/whl/cu128 torch torchvision
```

Checkpoints are **not** downloaded automatically. Put verified files in
`<repo>/tmp/realesrgan/weights/` (gitignored) and keep a `weights.json` beside
them with the source URL, SHA-256, and license:

```text
realesr-general-x4v3.pth
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth
  sha256 8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292
realesr-general-wdn-x4v3.pth
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth
  sha256 1641f8c4464b9f097c9fdda5589273713f67cf59f3d909e0bd688f0cee269dca
RealESRGAN_x2plus.pth
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth
  sha256 49fafd45f8fd7aa8d31ab2a22d14d91b536c34494a5cfe31eb5d89c2fa266abb
```

`upscale.json` records the checkpoint file name and SHA-256 so a render can be
traced back to exact weights. Use `--weights`/`--weights2` to point at another
verified pair.

The upstream `realesrgan`/`basicsr` packages do not build on Python 3.13, so the
two model definitions live in `scripts/realesrgan_torch.py` with their upstream
licenses; only `torch`, `numpy`, and `Pillow` are required.

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

The bundled ncnn models are `realesrgan-x4plus` (default, live action),
`realesrgan-x4plus-anime` (2D), and `realesr-animevideov3` (animation only; it is
never auto-selected for live footage).

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
  verify/lanczos-reference.mp4  delivery-verification reference
<clip>/upscaled/                timeline-range assets
  upscale.json                full render manifest
  chunk-*.mp4                 chunked inference when --chunk is used
```

`upscale.json` caches on the source SHA-256 plus every render parameter. A
second run with the same source and settings returns `"cached": true` without
re-encoding. The batch keeps `final-pre-upscale.mp4` and only replaces
`final.mp4` after a verified FIX or an explicit override. A `verification_review`
result leaves the previous file in place and points at the unapplied asset for
inspection.

## Delivery verification

A passing preview is provisional. Every AI render is re-measured after encoding,
against fresh 1.5 s Lanczos references near the beginning, middle, and end of
long clips (one centered window for clips up to 3 s), with the same
detail/noise/flicker/jitter/luma/clipping gates. The result is stored in
`upscale.json` as `verification.status`:

- `verified` — the delivered output cleared the criterion; safe to apply.
- `review` — the delivery did not clear it. A batch leaves `final.mp4` untouched
  and lists the asset under `verification_review`; timeline-range assets that fail
  are excluded from the map.
- `unverified_override` — you forced the render with `--approve` or `--mode always`;
  it is applied but labelled for human review.

`verification` also records each checked window, its criteria, reference and
delivered metrics, and the reference clips. Every window must pass for `verified`.

## Limitations

- No temporal model is bundled. Per-frame upscaling can still flicker; the
  temporal gate catches obvious cases but does not restore motion coherence.
- The general ncnn model is impractically slow at 1080p on this GPU. Use the
  video model or install the PyTorch backend.
- Faces, signs, and text are not separately detected. Review those clips by hand.
- AI upscaling is presentation enhancement, not evidence-grade reconstruction.
