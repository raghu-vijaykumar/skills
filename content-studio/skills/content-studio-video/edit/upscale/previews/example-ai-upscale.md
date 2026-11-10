# AI upscale gallery provenance

All four linked GIFs show moving, actual method outputs. A 1.2-second, 10 fps portion
of the published Out of Office Mode Tomato Bath video near 4:05 was first
downsampled to 320 × 180 in a temporary MP4. The three upscalers then produced
640 × 360 video tracks from that same input. All outputs were checked at 12
frames and 1.2 seconds. The source is unchanged; temporary video tracks and
checkpoints are not committed.

```powershell
python content-studio/skills/content-studio-video/edit/upscale/scripts/lanczos.py `
  --input <temporary-source.mp4> --output <temporary-lanczos.mp4> --scale 2
python content-studio/skills/content-studio-video/edit/upscale/scripts/real_esrgan.py `
  --input <temporary-source.mp4> --output <temporary-vulkan.mp4> --scale 2 `
  --model realesrgan-x4plus --realesrgan <realesrgan-ncnn-vulkan.exe>
python content-studio/skills/content-studio-video/edit/upscale/scripts/pytorch.py `
  --input <temporary-source.mp4> --output <temporary-pytorch.mp4> --scale 2 `
  --model realesr-general-x4v3 --weights <realesr-general-x4v3.pth> `
  --weights2 <realesr-general-wdn-x4v3.pth>
python content-studio/skills/content-studio-video/edit/upscale/scripts/compare.py `
  --input <temporary-source.mp4> --output <unused-output.mp4> --target 640x360 `
  --backend pytorch --model realesr-general-x4v3 `
  --weights <realesr-general-x4v3.pth> --weights2 <realesr-general-wdn-x4v3.pth>
python content-studio/skills/content-studio-video/edit/upscale/scripts/build_gallery.py `
  --source <temporary-source.mp4> --lanczos <temporary-lanczos.mp4> `
  --ncnn <temporary-vulkan.mp4> --pytorch <temporary-pytorch.mp4> `
  --compare-lanczos <compare-preview-lanczos.mp4> `
  --compare-ai <compare-preview-ai.mp4> `
  --out content-studio/skills/content-studio-video/edit/upscale/previews
```

The NCNN executable and model were from the official Real-ESRGAN Windows release.
The PyTorch `realesr-general-x4v3.pth` checkpoint SHA-256 was
`8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292`.
The x4 NCNN model is run at native 4× scale and resized to 2× after tile
assembly; requesting 2× directly produced a visibly corrupted frame in the
bounded test. Both specialist entrypoints reject draft-batch and timeline-range
flags. Upscaling does not correct color, exposure, motion blur, or missed focus.
