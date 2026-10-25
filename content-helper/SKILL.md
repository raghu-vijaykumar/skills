---
name: content-helper
description: Manage a YouTube channel end to end from one workspace: back up public, private and scheduled uploads to Google Drive, keep a local drafts folder in sync, prepend a channel intro, prune old local copies without touching Drive, and read retention/analytics with improvement pointers. Use when asked to back up or archive a channel, sync drafts, apply an intro, free local disk space, or analyse video retention.
---

# content-helper

One workspace per channel, one command family:

```
content.py backup     download public + private + scheduled uploads, mirror to Drive
content.py sync       push drafts/assets up, or pull drafts down
content.py draft      scaffold or list a draft folder
content.py intro      prepend the channel intro to a draft video
content.py prune      delete old published videos locally (Drive untouched)
content.py analytics retention curves and improvement pointers
content.py list       channels, local roots, draft counts
content.py doctor     check yt-dlp, ffmpeg, node, rclone, remotes
```

## Workspace layout

Everything for a channel lives under `<workspace>/<slug>` (default
`C:\workspace\content\out-of-office`) and that directory is the rclone source:

```
out-of-office/
  long/2026-10-24 - Title [VIDEOID]/      published long-form
        video.mp4  thumbnail.jpg  description.txt  metadata.json
  shorts/2026-02-17 - Title [VIDEOID]/    published shorts
  drafts/Ahara mela/                      work in progress
        video.mp4            edited cut (after intro)
        thumbnail.png
        title.txt  description.txt
        original-videos/     clips + video-before-intro.mp4
        draft.json           manifest
  assets/intro.mp4                        the intro clip used by `intro`
  archive.txt                             yt-dlp ledger, so pruned videos never re-download
  analytics/<videoId>/                    metrics.json, retention.csv, retention.svg
  backup-report.json                      last run summary (never uploaded)
```

## Config

`<skill>/config.json` is versioned with the skill. `config.local.json` (gitignored)
is merged over it for machine-specific values.

```json
{
  "workspace": "C:\\workspace\\content",
  "remoteRoot": "gdrive:YouTubeBackups",
  "browser": "brave",
  "browserDebugPort": 9223,
  "quality": "best",
  "transfers": 2,
  "includePrivate": true,
  "channels": {
    "out-of-office": {
      "name": "Out of Office Mode",
      "channelId": "UC-jjjJYPl8rlR029Aag5ZKw",
      "driveFolder": "gdrive:YouTubeBackups/out-of-office",
      "includePrivate": true,
      "intro": "assets/intro.mp4",
      "analytics": {
        "provider": "api",
        "credentials": "~/.config/content-helper/client_secret.json"
      }
    }
  }
}
```

| Field | Meaning |
| --- | --- |
| `workspace` | parent of every channel folder; the only directory rclone reads from |
| `driveFolder` | exact rclone destination per channel; subfolders `long`, `shorts`, `drafts`, `assets` are created under it |
| `url` / `channelId` | `/channel/UC…`, `/@handle` or a bare id; a url is resolved on demand |
| `quality` | `best` or a height cap such as `1080` |
| `includePrivate` | also capture scheduled, private and unlisted uploads |
| `intro` | intro clip path, relative to the channel root |
| `analytics.provider` | `api` (retention curves) or `studio` (browser harvest) |

## Sync model

Drive is the durable copy; the local folder is a working subset.

- `sync` pushes `drafts` and `assets` normally (edited files are updated) and pushes
  `long`/`shorts` immutably (already-present files are skipped).
- `sync --pull` copies `drafts` and `assets` **down** without deleting anything locally.
- No command ever deletes or truncates anything on Drive.

## Freeing local space

```powershell
python scripts/content.py prune --channel out-of-office --count 5 --dry-run
python scripts/content.py prune --channel out-of-office --count 5
```

Removes the 5 oldest published/scheduled videos from the local `long/` folder (add
`--include-shorts`, or `--newest` to take the most recent instead). Each folder is
verified against Drive with `rclone check` first; if the Drive copy is incomplete the
folder is kept. `archive.txt` entries stay, so the next `backup` will not re-download
what was pruned.

## Intro

```powershell
python scripts/content.py intro --channel out-of-office --draft "Ahara mela"
python scripts/content.py intro --channel out-of-office --all --force
```

Prepends `assets/intro.mp4`, scaling/cropping it to the draft's frame and frame rate,
adding silent audio when either clip lacks it, re-encoding with x264 crf 18. The
un-introed cut is preserved as `original-videos/video-before-intro.mp4`; `.intro.json`
records the hashes so a second run is a no-op unless `--force`.

## Analytics

```powershell
python scripts/content.py analytics --channel out-of-office --last 5
python scripts/content.py analytics --channel out-of-office --video VIDEOID
python scripts/content.py analytics --channel out-of-office --provider studio --last 3
```

Writes `analytics/report.md`, plus `metrics.json`, `retention.csv` and `retention.svg`
per video.

- `api` needs an OAuth **Desktop app** client with the YouTube Analytics API enabled,
  saved at `analytics.credentials`. First run opens a browser for consent and caches a
  refresh token at `~/.config/content-helper/token-<slug>.json`.
- `studio` reuses the browser debug session and harvests the JSON Studio loads for the
  Content tab. No setup, but undocumented and it may stop working after a Studio change.
- Analytics reads local `metadata.json`, so pruned videos are not in the report.

The report turns the curves into next-video pointers: hook loss in the first 10%,
the largest single drop with its timestamp, retention at the halfway mark, comparison
with the channel median, and CTR when impressions are available.

## Backup, private and scheduled uploads

Public channel tabs never list scheduled or private videos, and Chromium cookie
databases cannot be read by yt-dlp (`Failed to decrypt with DPAPI`). The backup runs a
Studio pass instead: it relaunches the configured browser with a debug port, reads the
Studio *Videos* and *Shorts* tables, exports session cookies over the DevTools protocol,
downloads only ids missing from `archive.txt`, then closes the browser. The browser is
briefly closed during this pass.

## Prerequisites

```powershell
python -m pip install --user yt-dlp yt-dlp-ejs websocket-client
winget install Gyan.FFmpeg
winget install OpenJS.NodeJS
winget install Rclone.Rclone
rclone config create gdrive drive scope=drive
```

`content.py doctor` reports which of these are missing.
