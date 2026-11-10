# Clip edit and supplied-render evidence

Three one-second, 640 × 360 excerpts were made from already published Out of
Office Mode videos: Tomato Bath near 4:05 (A), Dubai Fountain near 1:35 (B),
and Tomato Bath near 4:20 (C). Their original audio was replaced by generated
440, 660, and 880 Hz tones. The source videos were never modified.

The maintained edit command produced a 3.021-second A → B → C join. A cut
removed 1–2 seconds and a separate trim kept 0.4–2.2 seconds. The short GIFs
are decoded from those three actual output files, with labels added by
`scripts/build_gallery.py`.

```powershell
python content-studio/skills/content-studio-video/edit/clip-edit/scripts/content.py edit join `
  --config <temporary-config.json> --input <a.mp4> --input <b.mp4> `
  --input <c.mp4> --out <joined.mp4> --size 640x360
python content-studio/skills/content-studio-video/edit/clip-edit/scripts/content.py edit cut `
  --config <temporary-config.json> --input <joined.mp4> `
  --remove 1-2 --out <cut.mp4>
python content-studio/skills/content-studio-video/edit/clip-edit/scripts/content.py edit trim `
  --config <temporary-config.json> --input <joined.mp4> `
  --start 0.4 --end 2.2 --out <trim.mp4>
python content-studio/skills/content-studio-video/edit/clip-edit/scripts/build_gallery.py `
  --joined <joined.mp4> --cut <cut.mp4> --trim <trim.mp4> `
  --out content-studio/skills/content-studio-video/edit/clip-edit/previews
```

A join requires an approved source order in a production edit. Keep every output
separate and review its transitions, color tags, audio, and full export.

## Supplied-render review

The joined output used for this bounded example had SHA-256
`3a4226db7714524db8427cfeec868f35c0ff95dfb446aeaf2a9220ceab8f0271`.
FFprobe reported H.264 video, AAC stereo audio, and 3.021354 seconds. The
[contact sheet](review-contact.jpg) confirms the ordered picture at three
sample times; the [MP3](review-audio.mp3) confirms the generated tone sequence.
The GIF and samples are review evidence only, not proof that an unsampled full
render is error-free. No title or creator action is inferred from these frames.
