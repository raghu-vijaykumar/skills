# Video upscaling

Upscaling reconstructs resolution. It does **not** replace color correction,
exposure correction, or motion-blur repair. AI models can sharpen edges and
invent plausible detail, but they can also hallucinate faces, text, signs, and
fine patterns.

## When to use it

- A 1080p clip must join a 4K final canvas.
- A delivery needs 4K even though the source is 1080p.
- The user explicitly asks for AI upscaling.

Do not upscale to hide focus misses, motion blur, noise, or a bad color cast.
Run `enhance analyze` first and keep those corrections separate.

## Vlog 4K stage

For vlog drafts, upscale the cleaned `processed-clips/*/final.mp4` files before
final assembly:

```powershell
content-studio upscale --draft <draft> --target 4k
```

- Clips already at 4K are skipped.
- Lower-resolution clip files are AI-upscaled and replaced; the previous file is
  kept as `final-pre-upscale.mp4`.
- `upscale-batch.json` records every decision.
- `--dry-run` lists what would change.
- `--limit 1` tests one clip first.

Lifecycle order for a 4K vlog:

```text
preprocess
  → AutoCut rough cut + approval
  → upscale low-resolution processed clips to 4K
  → final join at 4K
  → color analysis and correction on the 4K master
  → music
  → package approval
```

Color correction deliberately happens **after** upscaling. Upscaling can change
noise and edge character, so correcting color before upscaling would invalidate
the review evidence.

The batch command refuses portrait/landscape mismatches rather than distorting
them. Use a matching `--target` or keep that clip at its native resolution and
mark C23 not applicable with a reason.

## Command

```powershell
content-studio upscale `
  --input <clip.mp4> `
  --output <clip-4k.mp4> `
  --scale 2 `
  --model realesr-animevideov3 `
  --tile 256
```

- `--scale 2` turns 1080p into 3840×2160.
- `--backend realesrgan` uses Real-ESRGAN ncnn/Vulkan.
- `--backend lanczos` is the non-AI fallback: scale + unsharp, fast and
  predictable, but no invented detail.
- `--start` and `--duration` make a short test excerpt.
- `--tile` controls VRAM. 256 is safe on 8 GB; try 512 on a faster GPU.
- `--work` overrides the intermediate frame folder.
- `--force` clears the work folder first.

The output keeps the source audio and frame rate. Frames are extracted as PNG,
upscaled, then reassembled with H.265.

## Real-ESRGAN install

Download the official Windows ncnn/Vulkan release:

```text
https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip
```

The command auto-detects:

1. `--realesrgan <path>`
2. `REALESRGAN_NCNN`
3. `realesrgan-ncnn-vulkan` on `PATH`
4. `<repo>/tmp/realesrgan/realesrgan-ncnn-vulkan.exe`

Model choices:

- `realesr-animevideov3` — video-oriented, x2/x3/x4, lower artifact risk
- `realesrgan-x4plus` — sharper general model, slower, more hallucination risk
- `realesrgan-x4plus-anime` — 2D/anime material

Verify the model license before commercial use.

## Outputs

```text
<output-folder>/.content-studio/upscale/<clip>/
  frames/
  upscaled/
  upscale.json
  before-after.jpg
```

`upscale.json` records backend, model, scale, tile, source/output sizes,
runtime, and the explicit note that upscaling does not correct color or blur.

## Limitations

- Frame-by-frame upscaling can flicker because each frame is processed alone.
- No temporal model is bundled. BasicVSR++/RealBasicVSR and Topaz Video AI are
  separate, heavier options.
- The full video is currently processed in one run; interrupted frames can be
  resumed by rerunning with the same work folder, but frame-level resume is not
  yet automatic.
- AI upscaling is presentation enhancement, not evidence-grade reconstruction.
