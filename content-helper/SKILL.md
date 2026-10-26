---
name: content-helper
description: Manage a YouTube channel end to end from one workspace: back up public, private and scheduled uploads to Google Drive, keep a local drafts folder in sync, prepend a channel intro, prune old local copies without touching Drive, collect retention/analytics into a dataset a model can reason over, and extract audio/frames/clips for segment review. Use when asked to back up or archive a channel, sync drafts, apply an intro, free local disk space, build a channel analytics dataset, or pull frames/audio from a video segment.
---

# content-helper

One workspace per channel, one command family:

```
content.py backup     download public + private + scheduled uploads, mirror to Drive
content.py sync       push drafts/assets up, or pull drafts down
content.py draft      scaffold or list a draft folder
content.py intro      prepend the channel intro to a draft video
content.py prune      delete old published videos locally (Drive untouched)
content.py insights   build the analytics dataset that a model turns into ideas
content.py media      extract audio, frames or a clip for segment review
content.py code       git-track the sources, snapshot to Drive, restore, prune
content.py analytics  retention and performance numbers
content.py list       channels, local roots, draft counts
content.py doctor     check yt-dlp, ffmpeg, node, rclone, remotes
```

## Workspace layout

Everything for a channel lives under `<workspace>/<slug>` (default
`C:\workspace\content\<slug>`) and that directory is the rclone source. Several
channels share one workspace, each with its own slug, Drive folder and git repo:

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
        src/                 optional code for a generated video
        draft.json           manifest
  assets/intro.mp4                        the intro clip used by `intro`
  archive.txt                             yt-dlp ledger, so pruned videos never re-download
  analytics/<videoId>/                    metrics.json, retention.csv, retention.svg
  .snapshots/*.bundle                     git snapshots already uploaded to Drive
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
  Content tab: retention values, views, average view duration and
  `shortsFeedImpressionsVtr`. No OAuth setup, but undocumented and it may break.
- Analytics reads local `metadata.json`, so pruned videos are not in the report.

The report is numbers only: per-video retention at 25/50/75%, the largest measured drop,
the same-format median, VTR when available. The API exposes no retention curve for
Shorts, so those rows carry views, average view duration, average percentage and VTR.

## Insights dataset

```powershell
python scripts/content.py insights --channel revise-labs
python scripts/content.py insights --channel revise-labs --refresh --vtr-count 20
```

Collects every video into `analytics/dataset.csv` and `analytics/insights.json` and
prints `analytics/insights.md`. Metrics are cached per video for 12 hours; VTR is cached
per short, so repeat runs only fetch what is missing. `--vtr-count 0` skips the browser
pass and reuses cached VTR.

`insights.json` is the intended input for a model:

```
channel, generated,
numbers           totals, medians, counts, subscribers per 1k views
correlations      r(VTR, views), r(average %, views)
duration_bands    n, median views, median average %, median VTR per band
upload_days       n and median views per weekday
topic_lanes       per title keyword: n, median views, median average %, median VTR, best video
videos[]          id, kind, title, dates, duration, views, watch minutes, avg view seconds,
                  avg %, VTR, subs/likes/comments/shares, retention at 25/50/75,
                  biggest drop position and size, title pattern, title length
```

The script deliberately stops at measurement: it does not generate titles, ideas or
advice. Interpretation belongs to the model that consumes `insights.json`.

## Media extraction

Pull the exact bytes needed to study a segment:

```powershell
python scripts/content.py media segment --channel revise-labs --video VIDEOID --start 0:00 --end 0:12 --count 6
python scripts/content.py media frames  --channel revise-labs --draft "Ahara mela" --at 0:00,0:03,0:07
python scripts/content.py media audio   --channel revise-labs --draft "Ahara mela" --start 0:30 --end 1:10
python scripts/content.py media clip    --channel revise-labs --video VIDEOID --start 1:05 --end 1:25
```

- targets: `--video ID` (published folder), `--draft NAME` (draft `video.mp4`) or
  `--path FILE`
- times accept `SS`, `MM:SS` or `HH:MM:SS`; without `--start/--end` the whole file is used
- `segment` writes all three: `audio-*.wav` (16 kHz mono, transcription friendly),
  `frame-*.png` (evenly spaced, or the exact `--at` timestamps) and `clip-*.mp4`
  (re-encoded for frame accuracy; `--copy` stream-copies instead)
- output defaults to `<channel>/analysis/<target>/`, override with `--out`

## From dataset to the next video

`insights.json` is the input for [video-idea-engine](../video-idea-engine/SKILL.md): research
sweep, scored idea selection, packaging before production, and a measurement loop that feeds
the next run.

```powershell
python ../video-idea-engine/scripts/plan.py --channel revise-labs --name "<idea>" --kind short
```

That scaffolds `drafts/<idea>/` with `research.md`, `brief.md`, `packaging.md` and
`measurement.md`, pre-filled with the channel's medians, strongest lane and best duration
band.

## Git-tracked sources

Code-generated channels keep their sources in git at the channel root, next to the media
the repo deliberately ignores:

```powershell
python scripts/content.py code init --channel revise-labs
git -C C:\workspace\content\revise-labs add -A
git -C C:\workspace\content\revise-labs commit -m "first cut"

python scripts/content.py code status   --channel revise-labs
python scripts/content.py code snapshot --channel revise-labs --message "before render"
python scripts/content.py code restore  --channel revise-labs --dest C:\workspace\content\revise-labs-restored
python scripts/content.py code prune    --channel revise-labs --keep 5
```

- `init` writes a `.gitignore` that excludes `long/`, `shorts/`, `assets/`, `analytics/`
  and media extensions, so drafts, scripts, titles and descriptions are tracked while
  videos and thumbnails stay out of git. Per-video code belongs in `drafts/<name>/src`.
- `snapshot` refuses to run with uncommitted changes (`--allow-dirty` overrides with a
  warning), creates a `git bundle` of every ref, uploads it to
  `<driveFolder>/code/snapshots/<utc>-<sha>.bundle`, and mirrors the tracked tree to
  `<driveFolder>/code/tree`. A bundle is a complete clone source: `git clone file.bundle`.
- `restore` picks the newest bundle (or `--name`) from Drive and clones it into `--dest`.
- `prune` deletes only local bundles beyond `--keep`, and only after confirming the same
  bundle exists on Drive with an identical size. Drive is never touched.

This is the same principle as `prune` for videos: local is a working subset, Drive is
the durable copy, and nothing is deleted locally before the Drive copy is verified.

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
