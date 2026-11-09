# Reproduce this measurement

```powershell
python content-studio/skills/content-studio-video/review/quality/scripts/measure.py   --reference <synthetic-source.mp4>   --distorted <processed-preview.mp4>   --out previews/example-quality.json
```

The committed example compares a synthetic testsrc2 source with a denoised preview.
SSIM/PSNR/VMAF measure fidelity to that reference; they do not prove the edit or
enhancement looks better.
