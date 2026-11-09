# Music shortlist example

Illustrative shortlist, not a licensed track recommendation. No music file is committed.

```powershell
python content-studio/skills/content-studio-video/audio/music/scripts/music.py review --channel <slug> --draft <id> --category cinematic --mood calm --max-duration 240 --count 5
```

The real command writes `.content-studio/analysis/music-review.html` with local audio
players. Approval is by exact title. A later `select` writes `music-selection.json` and
`music-credits.txt`; `mix` writes `<id>-final-with-music.mp4` and `music-mix.json`.
