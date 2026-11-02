# Music library

Local catalog for YouTube Audio Library tracks used in vlogs.

## Important: the audio is not committed

YouTube Audio Library tracks may be used in videos, but their license does not
permit redistribution or standalone delivery. This repository is public, so the
MP3s live in `local/`, which is gitignored. Git LFS does not change that
licensing rule; it only helps with media that is legally redistributable.

Only these files are committed:

- `library.json` — title, artist, category, license, attribution, and hashes
- `credits.md` — generated attribution-ready credits
- this README

The audio itself stays on this machine (and in any private backup you choose).

## Initialization

```powershell
node content-studio/scripts/music-library.mjs init
node content-studio/scripts/music-library.mjs open
```

`init` creates the category folders under `local/` and refreshes the manifest.
`open` opens the official Audio Library in your browser. There is no automated
download: sign in to YouTube Studio, filter by genre, and use each track's
**DOWNLOAD** button. Downloading through a bot or scraper violates YouTube's
terms.

## Add a downloaded track

```powershell
node content-studio/scripts/music-library.mjs add "C:\Users\you\Downloads\Track.mp3" `
  --category cinematic `
  --title "Track title" `
  --artist "Artist name" `
  --mood "Inspirational" `
  --license youtube-audio-library `
  --source-url "https://www.youtube.com/audiolibrary"
```

Use `--license youtube-audio-library-cc-by` and `--attribution "Music: ..."`
when the track requires credit. The script copies the file into
`local/<category>/`, records its SHA-256 and duration, and regenerates
`credits.md`.

If you already placed files in `local/<category>/`, register them in bulk:

```powershell
node content-studio/scripts/music-library.mjs scan
```

Then inspect and correct titles/artists in `library.json`, or remove the row
and re-add it with explicit metadata.

## Commands

| Command | Purpose |
|---|---|
| `init` | Create local category folders and refresh credits |
| `open` | Open the official YouTube Audio Library |
| `add <file>` | Copy/move one download and register it |
| `scan` | Register files already under `local/` |
| `list` | Show the catalog grouped by category |
| `verify` | Check files exist and hashes match |
| `credits` | Regenerate `credits.md` |

Use `--root <dir>` to point at a different music library root. Add `--move` to
`add` to move instead of copy.

## Categories

Categories follow the Audio Library genre filter:

Ambient, Alternative & Punk, Children's, Cinematic, Classical, Country & Folk,
Dance & Electronic, Hip-Hop & Rap, Holiday, Jazz & Blues, Pop, R&B & Soul,
Reggae, Rock, Soundtrack, World, and Uncategorized.

The folder name is the slugified category, for example
`local/dance-electronic/`.

## Attribution

Most Audio Library tracks need no attribution. Creative Commons tracks do.
Check the license column before downloading and keep the generated attribution
text with the video's description. `credits.md` groups every track and has a
separate section for tracks that require credit.

## Content ID

Audio Library tracks are known to YouTube and are generally not claimed through
Content ID. Keep `library.json` and the download date as proof of source. Do not
re-upload the MP3s as standalone audio or publish them on another platform
unless that track's license explicitly allows it.

## Backups

Because `local/` is gitignored, back it up separately. Use a private Git LFS
repository or private cloud storage, not this public repository. The manifest
and `credits.md` are safe to commit.
