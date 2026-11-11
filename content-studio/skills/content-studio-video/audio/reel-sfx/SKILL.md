---
name: content-studio-video-reel-sfx
description: Download a public Instagram Reel for private reference, extract timestamped sound-effect candidates, and catalogue reviewed audio without voice or music bleed.
---

# Instagram Reel sound effects

Use this skill for a user-supplied public Instagram Reel when they want its sound effects as separate files. The [stock library](../../stock-library/SKILL.md) owns the private catalogue. Download only a public reel that yt-dlp can access normally; if login or another access barrier is required, ask for a user-supplied file. Keep the source and candidates outside Git. The download preserves a canonical URL, creator, source hash, and media properties.

Before production extraction or catalogue import, run the [Content Studio precheck](../../../content-studio-workflow/SKILL.md) for a private working folder and obtain explicit approval of its current plan. Read the [planning guidance](../../../content-studio-workflow/references/planning.md). Profile the source, select bounded candidate ranges, and give the exact commands, outputs, estimates, fallback, and listening criteria. Source download and small diagnostics may inform that plan.

From the repository root, after approval:

```powershell
python content-studio/skills/content-studio-video/audio/reel-sfx/scripts/reel_sfx.py download --url "https://www.instagram.com/reel/<id>/" --output-dir <private-workspace>
python content-studio/skills/content-studio-video/audio/reel-sfx/scripts/reel_sfx.py extract --source <private-workspace>/reel-<id>.mp4 --source-record <private-workspace>/reel-<id>.source.json --start <seconds> --end <seconds> --name "Short effect name" --category <category> --output <private-workspace>/candidates/<name>.wav
```

Listen to **each complete candidate**, including its start and tail, against the original. A time cut does not remove overlapping speech, music, or ambience; filtering or source separation cannot by itself establish an effects-only result. Reject or revise contaminated candidates. Mark `--effect-review passed` only after a human has heard an isolated effect with no voice or music bleed. Unknown rights remain reference-only even after audio review. Record the creator and canonical source URL; do not claim the uploader owns a third-party effect.

For a private reference entry, use `scripts/library.py add --kind sfx --rights unknown --effect-review pending` in the [stock library](../../stock-library/README.md). Supply the real creator, source URL, source range and source SHA-256 from the candidate sidecar. The stock catalogue records unknown-rights or unreviewed files as `reference-only`; never use them in a delivery timeline or publish them until rights and isolation are confirmed. Do not paste audio or full reel media into this repository.

The [method guide](README.md) records the supported commands and verification limits.
