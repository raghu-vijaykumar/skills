---
name: content-studio
description: Route a video idea through animation or vlog production, review, publishing, and backup. Use when starting or resuming the full content lifecycle.
---

# Content Studio

Choose the channel and one draft folder. Read that channel's owner rules and current draft before changing it. For new ideas use `content-studio-ideagen`; choose a treatment with `content-studio-styles`; for Remotion video use `content-studio-videogen`; for raw camera clips use `content-studio-videopreprocess` to deduplicate, order, and clean them, then `content-studio-autocut` for a reviewable rough cut, then use `content-studio-videoedit` for assembly or a supplied final export. Use `content-studio-audio` to master audio in a folder of videos. Choose background music with `content-studio-music` before publishing. Route a reviewed final export to `content-studio-publish`. Use `content-studio-archive` for an independent backup and Drive sync. Each specialist owns its checks; do not skip human review.

When this router is used, create or resume the deterministic checklist before production work:

```powershell
python <this-skill>/scripts/checklist.py `
  --channel <slug> --draft <id> --kind edited init
```

Use `--kind remotion` for code-driven videos. Update the checklist at every stage. Each item must end `done` with evidence or a note, or `not_applicable` with a reason; post-publish items may remain `deferred` with a reason until after publishing. Before approval and publishing run `verify --phase pre_publish`; before closing the draft run `verify --phase all`. The package gate rejects a main-lifecycle draft with pending or under-documented items. A direct specialist invocation is a one-off action and does not create this checklist. Read [the lifecycle checklist](references/lifecycle-checklist.md).

An idea is a brief, a reviewed render or export is a publication candidate, and a public YouTube backup is a separate archival state. Keep channel data and media in its content repository, not in this skill bundle. A draft follows one layout: `original/` for raw camera files, `.content-studio/` for per-clip working files and rough-cut review media, plus root `<id>-rough-cut.mp4`, `<id>-preprocessed.mp4`, `<id>-final.mp4`, and `<id>-audio-only.mp3`, with `title.txt`, `description.txt`, and `lifecycle-checklist.json` at the draft root. Vlog drafts do not generate transcripts or captions. A monthly archive run is user initiated.
