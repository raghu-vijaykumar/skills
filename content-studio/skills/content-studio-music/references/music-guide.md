# Music selection guide

## Source comparison

| | YouTube Audio Library | Pixabay Music |
|---|---|---|
| Where | YouTube Studio → Audio Library | pixabay.com/music |
| Cost | Free | Free |
| YouTube monetization | Allowed | Allowed, subject to Content ID checks |
| Other platforms | Only CC BY tracks, with credit | Allowed under the Content License |
| Attribution | Varies; filter by “Attribution not required” | Not required, but appreciated |
| Download | Manual, signed-in Studio | Manual |
| API | None for downloads | Images/videos only; no audio endpoint |
| Redistribution | Not allowed | Not allowed as standalone files |
| Content ID | Library tracks are known to YouTube | Some tracks are registered; check the shield |

Use YouTube Audio Library for YouTube-first vlogs. Use Pixabay Music when the same edit goes to Instagram, TikTok, or a client channel.

## License rules that matter

### YouTube Audio Library

- Standard tracks: use in YouTube videos, including monetized ones. No attribution.
- Creative Commons tracks: credit the artist exactly as YouTube generates it. These may be usable outside YouTube when the CC BY terms allow it.
- Do not re-upload or redistribute the MP3 as standalone audio.
- Do not use a track as the primary focus of the video.
- “Attribution not required” is not a redistribution permission.

### Pixabay Music

- Pixabay Content License: commercial and non-commercial use, modification allowed, no attribution required.
- Do not sell or distribute the track on a standalone basis.
- Some contributors register tracks with Content ID. The track page shows a shield; keep the download certificate and dispute a claim with it.
- Suggested credit, when you want one: `"Title" by Artist via Pixabay`.
- No music API. Do not script bulk downloads; Pixabay prohibits systematic mass downloading.

## Catalog layout

```text
content-studio/assets/music/
  README.md
  library.json               # committed manifest
  credits.md                 # committed attribution summary
  local/                     # gitignored audio
    ambient/
    cinematic/
    dance-electronic/
    ...
```

The catalog is shared across channels. Keep one copy and reference tracks by their relative file path in `library.json`.

When the skill is installed globally, the versioned bundle does not contain your local audio. Set:

```powershell
$env:CONTENT_STUDIO_MUSIC = "C:\workspace\skills\content-studio\assets\music"
```

or pass `--catalog` to `music.py`.

## Importing downloads

Single file with accurate metadata:

```powershell
node <bundle>/scripts/music-library.mjs add "C:\Users\you\Downloads\track.mp3" `
  --category cinematic `
  --title "Exact Title" `
  --artist "Artist" `
  --mood "Inspirational" `
  --license youtube-audio-library `
  --source-url "https://www.youtube.com/audiolibrary"
```

Pixabay:

```powershell
node <bundle>/scripts/music-library.mjs add "C:\Users\you\Downloads\track.mp3" `
  --category travel `
  --title "Exact Title" `
  --artist "Artist" `
  --license pixabay `
  --source-url "https://pixabay.com/music/..."
```

Bulk import files already placed in `local/<category>/`:

```powershell
node <bundle>/scripts/music-library.mjs scan
```

`scan` uses the file name as the title and `Unknown artist` as the artist. Correct the manifest afterward, or remove the row and re-add it with explicit metadata.

## Filtering the catalog

```powershell
python <this-skill>/scripts/music.py list
python <this-skill>/scripts/music.py list --category "Dance & Electronic"
python <this-skill>/scripts/music.py list --mood calm --max-duration 180
python <this-skill>/scripts/music.py list --query "piano" --json
```

Category matching accepts either the Audio Library label (`Dance & Electronic`) or the slug (`dance-electronic`).

## Review gate

```powershell
python <this-skill>/scripts/music.py review `
  --channel out-of-office --draft dubai-day-4 `
  --category cinematic --mood inspirational --count 5
```

The review page is written to `analysis/music-review.html` and uses `file:///` audio players, so it works without a server. Present the page, let the user listen, and wait for an exact title. Do not infer approval from silence or from a preference stated in an earlier draft.

## Selection record

```powershell
python <this-skill>/scripts/music.py select `
  --channel out-of-office --draft dubai-day-4 `
  --track "Exact Title"
```

Outputs:

```text
draft/
  music-selection.json
  music-credits.txt
  analysis/music-review.html
```

`music-selection.json` includes the catalog root, relative file, title, artist, category, mood, duration, license, attribution, and SHA-256. The audio remains in the local catalog; do not copy it into the content repository.

## Attribution and publishing

- If `music-credits.txt` says “No attribution required,” the description may omit music credit.
- If it contains an attribution line, paste that exact line into the description. Do not paraphrase a CC BY credit.
- Keep the source URL and license in the draft record.
- If the video is published outside YouTube and the track is YouTube Audio Library standard-license, stop: choose a Pixabay or CC BY track instead.

## Troubleshooting

**Empty folders.** `init` creates the category structure but does not download music. Download manually, then run `add` or `scan`.

**Catalog not found.** Run `music-library.mjs init`, or point `--catalog` at the source checkout.

**Track missing from review.** The audio file may have been moved or deleted. Run `music-library.mjs verify` and fix `library.json`.

**Ambiguous title.** Use the exact title or the relative file name. The script lists matching candidates when a substring is ambiguous.

**Wrong category.** Edit `library.json`, rerun `music-library.mjs credits`, and re-run `select` if the draft already has a selection.
