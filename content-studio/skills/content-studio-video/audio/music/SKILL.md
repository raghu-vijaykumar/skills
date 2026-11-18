---
name: content-studio-video-music
description: Choose, review, mix, and save background music from YouTube Audio Library or Pixabay Music for one draft, with license and attribution tracking. Use after the edit and before publication.
---

# Content Studio Music

Before mixing or selecting music for a draft, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist.

Read the channel rules and the draft. Confirm the master duration, the intended mood, and whether the channel is monetized. Check for an existing `music-selection.json` before choosing.

## Choose a source

**YouTube Audio Library** is the default for YouTube videos. Tracks are free to use in videos, including monetized ones, but some require attribution. The Audio Library cannot be redistributed, and downloads must be made manually in YouTube Studio.

**Pixabay Music** is the default when the video also goes to Instagram, TikTok, or another non-YouTube platform. Pixabay's Content License allows commercial use without attribution and has no music API; download manually and check the Content ID shield on the track page.

Never scrape or automate either site. Never commit the MP3s to the public skills repository.

## Build the catalog

The local catalog lives at `<bundle>/assets/music`. Its `local/` folder is gitignored. If the skill is installed globally, point at the source checkout:

```powershell
$env:CONTENT_STUDIO_MUSIC = "C:\workspace\skills\content-studio\assets\music"
```

Initialize and record a track for discovery without an MP3:

```powershell
node <bundle>/scripts/music-library.mjs init
node <bundle>/scripts/music-library.mjs candidate `
  --title "Beat Your Competition" --artist "Vibe Tracks" `
  --category "Dance & Electronic" --mood "funky, energetic" `
  --preview-url "https://www.youtube.com/watch?v=ijjNFvZ-u90"
```

Candidate entries have no local audio, duration, hash, or confirmed license. They may appear in lists and review pages, but **cannot be selected or mixed**. Confirm the exact track and license in Studio when a video needs it, manually download the MP3, then attach it with `add` using the same title and artist; `add` promotes the candidate rather than duplicating it. If Studio says Creative Commons, include its exact `--attribution` text.

Import manually downloaded files:

```powershell
node <bundle>/scripts/music-library.mjs init
node <bundle>/scripts/music-library.mjs open
node <bundle>/scripts/music-library.mjs add "C:\Users\you\Downloads\track.mp3" `
  --title "Track" --artist "Artist" --category cinematic `
  --license youtube-audio-library
node <bundle>/scripts/music-library.mjs scan
node <bundle>/scripts/music-library.mjs list
```

Use `--license pixabay` for Pixabay tracks. Use `--license youtube-audio-library-cc-by` and `--attribution "..."` for Creative Commons tracks that require credit.

## Build a shortlist

```powershell
python <this-skill>/scripts/music.py review `
  --channel <slug> --draft <id> `
  --category cinematic --mood calm --max-duration 240 --count 5
```

This writes `.content-studio/analysis/music-review.html` with audio players for local tracks and reference links for candidates. Show that page to the user and ask them to approve one track by exact title. For a candidate, obtain its manual Studio download and license details before writing the selection. Do not write a selection before approval.

Useful filters:

```powershell
python <this-skill>/scripts/music.py list --category ambient
python <this-skill>/scripts/music.py list --query "piano" --json
python <this-skill>/scripts/music.py list --min-duration 120 --max-duration 300
```

## Record the approved selection

```powershell
python <this-skill>/scripts/music.py select `
  --channel <slug> --draft <id> --track "Exact Track Title"
```

This writes:

- `music-selection.json` — the catalog reference, license, hash, and chosen metadata
- `music-credits.txt` — the exact attribution line, or “No attribution required.”

No audio is copied into the draft. The selection references the local catalog file.

Confirm with:

```powershell
python <this-skill>/scripts/music.py show --channel <slug> --draft <id>
```

## Mix the approved track

```powershell
python <this-skill>/scripts/music.py mix `
  --channel <slug> --draft <id>
```

It writes `<id>-final-with-music.mp4` and `music-mix.json` without changing the approved master. Music is looped or trimmed to the master duration, faded at the edges, and ducked under speech only when an optional transcript contains speech. Review the mixed master, then replace `<id>-final.mp4` only after approval and repeat package approval because the master hash changed.

## Handoff

Give `music-selection.json`, `music-mix.json`, and `<id>-final-with-music.mp4` to `content-studio-video-clip-edit` when assembling the final master. When publishing, copy `music-credits.txt` into the video description if the track requires attribution. Publishing still needs the user's explicit request.

Read [the music guide](references/music-guide.md) for license details, Pixabay Content ID handling, and catalog troubleshooting.
