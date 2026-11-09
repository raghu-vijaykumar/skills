# Join example

Illustrative command. `previews/trim-preview.gif` is a real trim from a synthetic clip;
no two-shot join is committed.

```powershell
python content-studio/skills/content-studio-video/edit/clip-edit/scripts/content.py edit join --inputs <a.mp4> <b.mp4> --out <joined.mp4>
```

A join requires an approved source order. Keep each output separate and review
transitions, color tags, audio, and the full export.
