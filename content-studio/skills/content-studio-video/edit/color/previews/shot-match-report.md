# Shot-match example and accepted command

The [three-panel image](shot-match-before-after.jpg) is an actual method output.
A 1.5-second, 640 × 360, 8 fps excerpt from the published Out of Office Mode
Tomato Bath video near 4:05 was used as reference. A temporary copy was shifted
with FFmpeg `colorchannelmixer=rr=1.15:bb=0.85` and placed in a one-clip input
folder. `shot_match.py` then returned gains `rr=0.8932`, `gg=1.0149`,
`bb=1.12` for that copy. The source and reference were preserved.

```powershell
python content-studio/skills/content-studio-video/edit/color/scripts/shot_match.py `
  --folder <one-or-more-input-clips> --output-dir <matched-output-folder> `
  --reference <reference-clip.mp4>
python content-studio/skills/content-studio-video/edit/color/scripts/build_gallery.py `
  --reference <reference-clip.mp4> --before <shifted-input.mp4> `
  --after <matched-output.mp4> `
  --out content-studio/skills/content-studio-video/edit/color/previews/shot-match-before-after.jpg
```

The prior example's `--input/--output` flags were not accepted by this entrypoint;
the folder flags above were exercised. Review temporal consistency and skin
tones against the untouched edit before approving a color change.
