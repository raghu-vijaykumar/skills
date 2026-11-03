# Content Studio skills

This repository is the editable source of the `content-studio` video lifecycle bundle. The npm package remains `@raghu-vijaykumar/videogen` so existing Remotion imports and the `videogen` CLI keep working. Its canonical source is under [content-studio](content-studio/).

| Skill | Use |
| --- | --- |
| [content-studio](content-studio/skills/content-studio/SKILL.md) | Route one draft through the lifecycle |
| [content-studio-ideagen](content-studio/skills/content-studio-ideagen/SKILL.md) | Owned analytics, public comparisons, digest, idea brief |
| [content-studio-styles](content-studio/skills/content-studio-styles/SKILL.md) | List built-in and project-enabled editorial styles and themes |
| [content-studio-videogen](content-studio/skills/content-studio-videogen/SKILL.md) | Narrated Remotion videos, themes, Hairline style, render review |
| [content-studio-autocut](content-studio/skills/content-studio-autocut/SKILL.md) | Reviewable rough cut from raw footage with transcript-aware selection |
| [content-studio-videopreprocess](content-studio/skills/content-studio-videopreprocess/SKILL.md) | Capture ordering, footage cleanup, blur and Dolby Vision review |
| [content-studio-videoedit](content-studio/skills/content-studio-videoedit/SKILL.md) | Clip editing or manual export review, transcription, captions, thumbnail |
| [content-studio-audio](content-studio/skills/content-studio-audio/SKILL.md) | Batch audio mastering with new video and extracted WAV outputs |
| [content-studio-music](content-studio/skills/content-studio-music/SKILL.md) | Choose and record YouTube Audio Library or Pixabay background music |
| [content-studio-publish](content-studio/skills/content-studio-publish/SKILL.md) | Reviewed package approval, YouTube now/schedule, Instagram now |
| [content-studio-archive](content-studio/skills/content-studio-archive/SKILL.md) | Independent public backup, Drive verification, monthly reconciliation |

## Draft lifecycle

A draft is one folder under `<workspace>/<channel>/drafts/<id>`. Raw media stays in that folder; the skills add plans, review artifacts, hashes, and publishing receipts around it. Remotion videos and camera-footage vlogs take different production paths, then converge on the same approval and publishing gate.

```text
idea ──► treatment ──┬── Remotion: scaffold → narration → render ──┐
                     │                                             │
raw footage ─────────┴── preprocess → AutoCut rough cut → edit ────┤
                                                                   ▼
                              transcript + captions + thumbnail + music
                                                                   ▼
                                    hash-bound human package approval
                                                                   ▼
                                      publish YouTube / Instagram
                                                                   ▼
                                      independent archive + Drive sync
```

### Deterministic checklist

When the main `content-studio` router is used, it creates `lifecycle-checklist.json` in the draft before production work. Direct specialist use remains one-off and does not create the checklist.

The checklist has fixed IDs C01-C22, in a fixed order. Every item must end as:

- `done` with evidence or a note
- `not_applicable` with a reason
- `deferred` with a reason (post-publish items only at approval time)

`pending` blocks. Post-publish items start deferred and must be resolved before the draft is closed.

```powershell
python <bundle>/skills/content-studio/scripts/checklist.py `
  --channel <slug> --draft <id> --kind edited init

python <bundle>/skills/content-studio/scripts/checklist.py `
  --channel <slug> --draft <id> set --id C07 --status done `
  --evidence "video.mp4" --note "watched end to end"

python <bundle>/skills/content-studio/scripts/checklist.py `
  --channel <slug> --draft <id> verify --phase pre_publish

python <bundle>/skills/content-studio/scripts/checklist.py `
  --channel <slug> --draft <id> verify --phase all
```

The publish gate rejects a main-lifecycle draft whose pre-publish items are pending, deferred, done without evidence, or not applicable without a reason. The full fixed item list is in [the lifecycle checklist](content-studio/skills/content-studio/references/lifecycle-checklist.md).

### 1. Open or create the draft

Pick the channel and one draft folder. Read the channel's owner rules and the draft's current state before changing it.

- **Remotion project:** run `npx videogen init <directory>` once, then `npx videogen scaffold <id> --title "Working title"`. Scaffolding preserves an existing idea brief and refuses to replace authored scenes.
- **Vlog or camera footage:** create `drafts/<id>/` and place the raw clips at its root. Preprocess them before AutoCut; for a standalone folder outside a channel, use `preprocess --folder <path>`.
- **Idea first:** use `content-studio-ideagen` for analytics, comparisons, and a brief; use `content-studio-styles` to choose a treatment.

`draft.json` is the draft's running record. Publication later stores the YouTube or Instagram ID and receipts there.

### 2. Clean and order the camera clips

`content-studio-videopreprocess` turns a camera dump into ordered, reviewed clips before any rough cut:

```powershell
python <bundle>/skills/content-studio-videoedit/scripts/content.py `
  preprocess --channel <slug> --draft <id>
```

For a standalone folder:

```powershell
python <bundle>/skills/content-studio-videoedit/scripts/content.py `
  preprocess --folder <path> --utc-offset +00:00
```

It detects exact and near duplicates, quarantines extras under `analysis/duplicates/`, orders clips by capture time, writes `_timeline.csv`, and renumbers them. It also extracts and enhances voice, lowers quiet gaps, proposes blur cuts, and flags stabilization crop.

Outputs live in `processed-clips/<camera-name>/`: `report.json`, `review.csv`, `review.html`, `enhanced-voice.wav`, and blur images. Set `remove=yes` for approved blur rows and rerun with `--apply-review`, or use `--final` to render a publish-ready 1920x1080 16:9 SDR `final.mp4` with all detected blur spans removed. Folder and draft final runs also join the exports into `final-video.mp4`. Use `--fit blur` to center a mismatched portrait clip over a blurred copy of itself instead of black pillars; `--fit pad` is the default and `--fit crop` fills the frame by cropping.

Review gates:

- **Blur:** inspect `review.csv` / `review.html` before approving cuts.
- **Dolby Vision:** install `dovi_tool`, run `--dv-proof`, check playback on the usual device, then use `--dv-approved`. Never treat an HLG-only file as Dolby Vision.
- **Final SDR:** `--final` intentionally drops the Dolby Vision RPU. Keep the proof path when DV must be preserved.

The per-clip `final.mp4` files are the clean input for AutoCut. AutoCut scans only the top level of its `--folder`, so stage them flat first:

```powershell
$draft = "C:\workspace\content\<channel>\drafts\<id>"
$stage = "$draft\analysis\autocut-input"
New-Item -ItemType Directory -Force $stage | Out-Null
Get-ChildItem "$draft\processed-clips" -Recurse -Filter final.mp4 |
  ForEach-Object { Copy-Item $_.FullName (Join-Path $stage ($_.Directory.Name + ".mp4")) }
```

If `--final` was not used, stage the approved `cut.*` or `processed.*` exports instead.

### 3. Shape the story with AutoCut (optional)

After preprocessing, `content-studio-autocut` selects speech and shots from the cleaned clips:

```powershell
python <bundle>/skills/content-studio-autocut/scripts/autocut.py `
  --folder <draft>/analysis/autocut-input --duration 12m --style travel-vlog `
  --output <draft>/rough-cut --orientation landscape --fit blur `
  --auto-transcribe --detect-scenes --quality-score
```

`--orientation landscape` filters portrait clips from a landscape edit. Use `--include-mismatched` or `--allow <filename>` for intentional exceptions. `--fit blur` centers a mismatched clip over a blurred copy of the same footage; `--fit crop` fills the frame by cropping; `--fit pad` leaves black bars. The decisions file records `orientation`, `size`, `fit`, and `skipped_sources`, and the timeline keeps the same fit for later renders.

It writes `rough-cut.mp4`, `edit-decisions.json`, `timeline.otio`, `timeline.json`, `review.html`, `review-state.json`, and review media under `review/` (contact sheet, frames, audio samples). Every selected range carries source in/out timestamps and a reason.

This is a proposal, not approval. Review the actual video, frames, and audio, then record a human decision:

```powershell
python <bundle>/skills/content-studio-autocut/scripts/review.py `
  --output <draft>/rough-cut --approve --reviewer human
```

Use `--request-changes "..."` to send it back. A revision resets approval and regenerates the review media. The deterministic heuristic uses scene cuts, silence, and duration; it does not understand landmarks or story without supplied transcripts or annotations. Do not claim semantics the analysis did not produce.

### 4. Master the audio (optional)

`content-studio-audio` masters a folder of videos without joining or trimming:

```powershell
python <bundle>/skills/content-studio-audio/scripts/master.py --folder <video-folder>
```

It writes `<video-folder>/audio-mastered/<stem>.mastered.wav` (48 kHz stereo PCM), `<stem>.mastered.mp4` (video stream copied when compatible), and `manifest.json` with loudness measurements. Inputs are never overwritten.

The default chain is high-pass, mild `afftdn` denoise, 2:1 compression, and two-pass EBU R128 normalization to -16 LUFS, 11 LU LRA, -1.5 dBTP. Review the result before replacing a production asset. Do not run it on already mastered outputs. Use `--force` only to replace generated outputs.

### 5. Edit the final master

`content-studio-videoedit` handles trim, cut, join, transcript, captions, and thumbnail:

```powershell
python <bundle>/skills/content-studio-videoedit/scripts/content.py `
  edit join --channel <slug> --draft <id>
```

Joined masters are 1920x1080 BT.709 SDR at 30 fps with stereo AAC; the full frame is kept and padded, HDR is tone mapped. Dolby Vision cuts require `--sdr` because the RPU cannot survive a frame-accurate re-encode.

When `video.mp4` exists:

```powershell
node <bundle>/scripts/cli.mjs transcribe --channel <slug> --draft <id>
```

Review `transcript.json` and `captions.srt` against the actual audio and representative frames. If the master has no intelligible speech, `transcript.json` records `speech: false`; mark transcript and captions not applicable rather than publishing fake captions. Draft the title and description from the transcript, voiceover, or audio context, not just the visuals.

Capture 4-6 representative frames and the spoken or voiceover context. Use an image-generation model to create a **16:9 landscape AI thumbnail** that reflects the actual subject, setting, and hook. Do not use a raw frame with overlaid text as the final thumbnail unless the user explicitly asks. Show the generated image and obtain approval before writing `thumbnail.png`. The full prompt and requirements are in [the AI thumbnail workflow](content-studio/skills/content-studio-videoedit/references/thumbnail.md).

### 6. Choose the music

`content-studio-music` builds a shortlist from the local catalog and records an approved selection:

```powershell
python <bundle>/skills/content-studio-music/scripts/music.py review `
  --channel <slug> --draft <id> --category cinematic --mood calm --count 5

python <bundle>/skills/content-studio-music/scripts/music.py select `
  --channel <slug> --draft <id> --track "Exact Title"
```

It writes `analysis/music-review.html` with playable candidates, then `music-selection.json` and `music-credits.txt` after approval. Audio stays in the local catalog and is not copied into the draft or committed to the public skills repository.

Use YouTube Audio Library for YouTube-first videos. Use Pixabay Music when the same edit also goes to Instagram, TikTok, or a client channel. Both are manual downloads; the scripts do not scrape either site. If a track requires attribution, paste the exact line from `music-credits.txt` into the description.

After approval, mix the track under the master:

```powershell
python <bundle>/skills/content-studio-music/scripts/music.py mix `
  --channel <slug> --draft <id>
```

It writes `video-with-music.mp4` and `music-mix.json`. Review the mixed master, then replace `video.mp4` and repeat package approval because the master hash changed.

### 7. Assemble and approve the publication package

A publication candidate contains:

| File | Purpose |
| --- | --- |
| `video.mp4` | Reviewed full-length master |
| `title.txt` | Exact title derived from transcript/voiceover/audio context |
| `description.txt` | Exact description from the same context, including music credit |
| `thumbnail.png` or `.jpg` | Approved AI-generated 16:9 thumbnail |
| `creative.json` | Theme, style, format, renderer, choices |
| `transcript.json` | Transcript tied to the master hash (edited exports) |
| `captions.srt` | Reviewed captions (edited exports) |
| `music-selection.json` | Approved music choice, when used |
| `music-credits.txt` | Exact attribution line, when required |

The user reviews the master, title, description, thumbnail, captions, and music credits. Record approval only after that review:

```powershell
node <bundle>/scripts/cli.mjs approve `
  --channel <slug> --draft <id> --note "reviewed master, title, description, thumbnail, captions, music"
```

This writes `package-approval.json` with a hash of the publication files: master, title, description, thumbnail, transcript, captions, and creative metadata. Put the exact music credit in `description.txt` before approval; changing the description after approval makes the package stale. The publish path re-checks the hashes before uploading.

### 8. Publish

Preview the exact render and metadata first:

```powershell
node <bundle>/scripts/cli.mjs publish --channel <slug> --draft <id>
```

After an explicit publication request:

```powershell
# YouTube now
node <bundle>/scripts/cli.mjs publish --channel <slug> --draft <id> --confirm

# Native YouTube schedule
node <bundle>/scripts/cli.mjs publish --channel <slug> --draft <id> `
  --at 2026-12-01T18:00:00+05:30 --confirm

# Instagram Reel now
node <bundle>/scripts/cli.mjs publish --channel <slug> --draft <id> `
  --platform instagram --confirm
```

Confirmed publishing verifies the package approval, probes the master, re-checks Remotion projects, and writes platform IDs and receipts into `draft.json`. A dry run needs no credentials and writes nothing. Instagram is immediate only. If an upload result is uncertain, reconcile the receipt before retrying; never upload twice.

### 9. Archive

This is independent of publication and runs on request, typically monthly:

```powershell
python <bundle>/skills/content-studio-videoedit/scripts/content.py backup --channel <slug>
python <bundle>/skills/content-studio-videoedit/scripts/content.py sync --channel <slug>
```

`backup` downloads public YouTube copies with exact title, description, and thumbnail; `sync` pushes durable media to Drive. Use `rclone check` evidence before pruning local media. Do not delete remote data. A public video moves from `drafts/` to `shorts/` or `long/` only after the backup and Drive copy are verified. Scheduled and private uploads remain drafts.

### Review gates

| Gate | Evidence | Human action |
| --- | --- | --- |
| Blur / stabilization | `review.csv`, `review.html`, report crop flag | Mark cuts or accept |
| Dolby Vision | `dv-proof.mov` | Check playback, then `--dv-approved` |
| AutoCut rough cut | `rough-cut.mp4`, frames, audio samples, `review-state.json` | Approve or request changes |
| Audio mastering | Mastered WAV/MP4 and `manifest.json` | Listen and compare |
| Master edit | Full `video.mp4` | Watch end to end |
| Package | Title, description, thumbnail, captions, music credits | Approve with note and hashes |
| Publication | Dry-run plan | Explicit request, then `--confirm` |
| Archive | YouTube backup and Drive check | Verify before pruning |

### Draft file map

| Path | Meaning |
| --- | --- |
| `drafts/<id>/` | Working draft |
| `_timeline.csv` | Capture order and original names |
| `analysis/duplicates/` | Quarantined duplicates and review |
| `processed-clips/` | Per-clip analysis, enhanced voice, cuts, `final.mp4` |
| `analysis/autocut-input/` | Flat staging folder of cleaned clips for AutoCut |
| `rough-cut/` | AutoCut outputs and review media |
| `audio-mastered/` | Mastered WAV/MP4 and loudness manifest |
| `video.mp4` | Final master |
| `transcript.json`, `captions.srt` | Transcript and reviewed captions |
| `title.txt`, `description.txt` | Publication copy |
| `thumbnail.png` or `.jpg` | Approved thumbnail |
| `creative.json` | Production metadata |
| `music-selection.json`, `music-credits.txt` | Approved music and attribution |
| `package-approval.json` | Hash-bound human approval |
| `draft.json` | Draft record, platform IDs, receipts |
| `shorts/`, `long/` | Verified public archive |

A draft is not finished when the render succeeds. It is finished when the package is approved, published on request, and the public copy is archived and verified.

## Install

Clone this repository, then run `node content-studio/scripts/cli.mjs install-skills --global`. The installer stores one versioned bundle at `~/.agents/content-studio/v<version>` and links its eleven skill folders directly under `~/.agents/skills`. [Codex](https://learn.chatgpt.com/docs/build-skills) and [OpenCode](https://opencode.ai/docs/skills) both discover that global path. It verifies the eleven matching skill entrypoints, refuses to replace unmanaged folders, then removes the obsolete global names `videogen`, `content-helper`, `video-idea-engine`, `hairline-create`, `learning-engineer`, and the superseded `content-studio-ideas`, `content-studio-animate`, and `content-studio-vlog`.

A video project can pin a tested Git tag of this private repository in `package.json`, run `npm install`, and use `npx videogen sync-skill` to install the matching animation skill locally. `npx videogen init <directory>` starts a project and `npx videogen scaffold <id> --title "Working title"` creates a draft. The root npm package includes only `content-studio/`.

The digest and channel helper are internal tools in the bundle, not separately discoverable skills. The Hairline style adapts the MIT licensed [Hairline](https://github.com/lucasmarkes/hairline) visual rules; the source attribution is retained in `content-studio/skills/content-studio-styles/hairline-source/LICENSE`. Channel media, drafts, secrets, and analytics stay in each content workspace.
