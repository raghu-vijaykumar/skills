# Reproduce the stabilization preview

`previews/stabilize.gif` is a real before/after loop: source on the left, stabilized
output on the right, both from a synthetic 5-second shaky clip.

```powershell
python content-studio/skills/content-studio-video/source/stabilize/scripts/vidstab.py --input <shaky.mp4> --output <stabilized.mp4>
```

The method is fixed to two-pass `vidstab`. Compare a bounded preview and check crop
risk before using the output.
