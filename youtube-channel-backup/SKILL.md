---
name: youtube-channel-backup
description: Back up a YouTube channel incrementally into per-video folders and copy it to a Google Drive folder with rclone. Use when asked to "back up my YouTube channel", "archive my videos", "save all my uploads", or to add a channel to the recurring backup config.
---

# YouTube channel backup

Downloads every video and Short from a configured channel into one folder per video,
then mirrors that folder to a Google Drive folder with `rclone copy`. Re-runs only fetch
what is new, so the same command works as a recurring backup.

## Output layout

```
<localRoot>/<channel-slug>/
  long/2026-10-24 - Title [VIDEOID]/
        video.mp4          best available video+audio, mp4 container
        thumbnail.jpg      maxres thumbnail
        description.txt    title, dates, URL, tags, description
        metadata.json      full yt-dlp metadata
  shorts/2026-02-17 - Title [VIDEOID]/...
  archive.txt              yt-dlp ledger of every downloaded id
  backup-report.json       last run summary
```

Folder names start with the upload date, so lexical order is chronological.

## Prerequisites

```powershell
python -m pip install --user yt-dlp yt-dlp-ejs websocket-client
winget install Gyan.FFmpeg
winget install OpenJS.NodeJS
winget install Rclone.Rclone
```

`node` is required: YouTube serves no real formats without a JavaScript runtime once the
challenge solver is needed (private and scheduled videos always need it).

## One-time setup

1. Create the config and edit it:

   ```powershell
   python scripts/backup.py --list
   ```

   That writes `~/.config/youtube-channel-backup/config.json` on first run:

   ```json
   {
     "localRoot": "C:\\Users\\raghu\\yt-backups",
     "remote": "gdrive:YouTubeBackups",
     "browser": "brave",
     "browserDebugPort": 9223,
     "quality": "best",
     "transfers": 2,
     "channels": {
       "out-of-office": {
         "name": "Out of Office Mode",
         "channelId": "UC-jjjJYPl8rlR029Aag5ZKw",
         "includeScheduled": true
       }
     }
   }
   ```

   `quality` accepts `best`, or a height cap such as `1080`.

2. Create the rclone remote once (browser opens, approve access):

   ```powershell
   rclone config create gdrive drive scope=drive
   rclone lsd gdrive:
   ```

   The Drive folder is `remote` + channel slug, so `gdrive:YouTubeBackups/out-of-office`.

## Run

```powershell
python scripts/backup.py --channel out-of-office
```

| Flag | Effect |
| --- | --- |
| `--channel SLUG` | one channel (default: every channel in the config) |
| `--no-upload` | download and file locally only |
| `--no-scheduled` | skip the Studio pass for scheduled/private uploads |
| `--cookies PATH` | use an existing cookies.txt instead of driving a browser |
| `--keep-cookies` | keep the exported cookies file for debugging |
| `--list` | show configured channels |

Adding a channel: append another entry under `channels` with a slug, display `name`,
and the `UC…` id (channel page → About → Share channel → Copy channel ID).

## How incrementality works

- `archive.txt` (yt-dlp `--download-archive`) records every id that was downloaded.
  Re-runs skip those ids even if the API listing changes.
- `rclone copy --ignore-existing` uploads only files whose names are absent on Drive.
  Nothing is ever deleted on Drive, so a bad local state cannot destroy the backup.
- `promote()` is idempotent: an existing per-video folder is reused, so partial runs
  converge instead of duplicating.
- `keepLocal` is informational only; nothing prunes the local copy automatically.

## Scheduled and private uploads

Public channel tabs never list scheduled or private videos, and yt-dlp cannot read a
Chromium cookie database on current builds (`Failed to decrypt with DPAPI`). This skill
reads the truth from YouTube Studio instead:

1. `scripts/browser_debug.ps1` closes the configured browser gracefully, relaunches it
   with `--remote-debugging-port`, and restores the previous session.
2. `scripts/studio_ids.py` opens the Studio *Videos* and *Shorts* tabs in that session,
   collects every row with its visibility, and exports the session cookies over the
   DevTools protocol (the browser decrypts them itself, so no DPAPI error).
3. Missing `Scheduled`/`Private` ids are downloaded with those cookies, filed, and
   uploaded.
4. The browser is closed again and the temporary cookies file is removed.

The browser is briefly closed during this pass; that is expected.

## Reporting back

After a run, read `<localRoot>/<slug>/backup-report.json` and report: new downloads,
long/shorts totals, whether the rclone copy succeeded (`rc == 0`), and anything logged
as `MISSING`, `ERROR`, or `WARNING`.

## Troubleshooting

- `n challenge solving failed` → install `yt-dlp-ejs` and `node`, and keep
  `--js-runtimes node` enabled (already in the script).
- `Requested format is not available` on a private video → the JS runtime is missing,
  so only storyboards were offered.
- `Failed to decrypt with DPAPI` → do not use `yt-dlp --cookies-from-browser`; use this
  skill's Studio pass or a cookies.txt export.
- `Could not copy Chrome cookie database` → the browser is running; the Studio pass
  closes it for you.
- Drive runs out of space or is quota-limited → raise the Drive plan or set `"remote": ""`
  to keep the run local.
- `This remote uses rclone's shared Google Drive client_id, which is being retired` → the
  backup still works today; create your own OAuth client when convenient and update
  `client_id`/`client_secret` in the rclone remote.
- The first upload of a large channel is limited by the uplink, not by the script
  (roughly 2 hours per 14 GB at 1.7 MB/s). Later runs only send new videos.
