# AI upscale command example

Illustrative commands; AI backends need local weights and are not exercised in this
evidence set. `previews/lanczos-before-after.png` is a real comparison for Lanczos.

```powershell
python content-studio/skills/content-studio-video/edit/upscale/scripts/real_esrgan.py --input <finished-edit.mp4> --output <upscaled.mp4> --target 4k
python content-studio/skills/content-studio-video/edit/upscale/scripts/pytorch.py --input <finished-edit.mp4> --output <upscaled.mp4> --target 4k
```

Both entrypoints reject draft-batch and timeline-range flags. Upscaling reconstructs
resolution; it does not correct color, exposure, motion blur, or missed focus.
