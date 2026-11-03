# Restoration and polish order

Run stages in this order. Geometry first, noise second, temporal stability third,
resolution fourth, color fifth, and sharpening last.

```text
lens correction
  → rolling-shutter / perspective correction
  → temporal denoise
  → deflicker / exposure stabilization
  → upscale
  → shot-to-shot color matching
  → selective color correction
  → sharpen / deblur
  → encode
```

Audio cleanup is independent and runs after final assembly or on the audio
master.

## Pre-upscale polish

```powershell
content-studio polish `
  --input <clip> --output <clip-polished.mp4> `
  --lens-k1 0.01 --denoise light --deflicker `
  --match-reference <reference-clip.mp4>
```

- `--lens-k1` / `--lens-k2`: lens distortion correction. These must come from a
  lens profile or a manual calibration; the tool does not guess them.
- `--perspective`: raw FFmpeg perspective coordinates for a manual
  rolling-shutter/skew correction. Automatic rolling-shutter detection is not
  implemented.
- `--denoise light|medium|nlmeans`: temporal denoise before upscaling.
- `--deflicker`: FFmpeg `deflicker` for auto-exposure pulsing.
- `--match-reference`: conservative mean-channel match to a reference shot.
- Leave `--sharpen off` here.

## Upscale

```powershell
content-studio upscale --input <clip-polished.mp4> --output <clip-4k.mp4> --scale 2
```

Denoise and deflicker must already be applied so the upscaler does not amplify
noise.

## Post-upscale polish

```powershell
content-studio polish `
  --input <clip-4k.mp4> --output <clip-4k-sharp.mp4> `
  --denoise off --sharpen light
```

Sharpening runs after scaling. Prefer `cas` (light/medium) over aggressive
`unsharp`. Review text, faces, and fine patterns for halos.

## Shot-to-shot matching

```powershell
content-studio match `
  --folder <matched-clips> --output-dir <matched-output>
```

This matches mean RGB balance across clips. It is not creative grading and
should not force different lighting conditions to look identical. Use a specific
`--reference` clip when the folder contains multiple lighting setups.

## Color correction

Run `content-studio enhance analyze` and `enhance render` after upscaling and
matching. Color review evidence must describe the final-resolution clip.

## Audio cleanup

```powershell
content-studio audio --folder <draft> --cleanup
```

or, for a specific pipeline:

```powershell
python <bundle>/skills/content-studio-audio/scripts/master.py `
  --folder <draft> --cleanup
```

`--cleanup` adds a de-esser and a gentle gate to the existing high-pass,
denoise, compression, and loudness chain. Use `--arnndn-model <model>` to use
RNNoise speech denoising instead of `afftdn`; the model file must be provided
locally.

## Quality metrics

```powershell
content-studio quality `
  --reference <before.mp4> --distorted <after.mp4> `
  --out <run>/quality.json
```

Records SSIM, PSNR, and VMAF when available. Use metrics as evidence, not as a
replacement for visual review.

## Limitations

- Automatic rolling-shutter detection is not implemented. `--perspective` is a
  manual correction path.
- Lens correction requires known distortion coefficients.
- Deblurring is conservative sharpening; it cannot recover true lost detail.
- Cross-clip matching uses mean channel statistics, not semantic scene
  understanding.
- VMAF can be unavailable if the local FFmpeg build lacks libvmaf.
