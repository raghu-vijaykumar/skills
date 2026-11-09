# Restoration command examples

Illustrative commands. `previews/denoise-before-after.png` is a real 1:1 crop from a
synthetic noisy source and the `denoise-light` output; the other rows have no committed
render.

```powershell
python content-studio/skills/content-studio-video/edit/restoration/scripts/deflicker.py --input <clip> --output <out.mp4>
python content-studio/skills/content-studio-video/edit/restoration/scripts/lens.py --input <clip> --output <out.mp4>
python content-studio/skills/content-studio-video/edit/restoration/scripts/sharpen_light.py --input <clip> --output <out.mp4>
python content-studio/skills/content-studio-video/edit/restoration/scripts/sharpen_medium.py --input <clip> --output <out.mp4>
python content-studio/skills/content-studio-video/edit/restoration/scripts/refine.py --input <clip> --output <out.mp4>
```

`deblur` is marked unsupported and has no script. Conservative sharpening cannot
recover missed focus.
