---
name: content-studio-video-reel-sfx
description: Source clean licensed sound effects for an Instagram Reel when available, or extract timestamped reference candidates without voice or music bleed.
---

# Instagram Reel sound effects

Use this skill for a user-supplied public Instagram Reel when they want its sound effects as separate files. First check whether a recognizable effect has a standalone source in an official sound library with terms that cover the intended video platforms. Prefer that clean file for reuse, and record its creator, item URL, license and attribution terms. A similar library sound is a substitute, never an identified original without evidence. The [stock library](../../stock-library/SKILL.md) owns the private catalogue; a source with unknown rights stays reference-only. Do not redistribute a licensed library file as public standalone stock if its license limits that use.

When no suitable standalone source is found, download only a public Reel that yt-dlp can access normally; if login or another access barrier is required, ask for a user-supplied file. Keep the source and candidates outside Git. The download preserves a canonical URL, creator, source hash, and media properties.

Before production extraction or catalogue import, run the [Content Studio precheck](../../../content-studio-workflow/SKILL.md) for a private working folder and obtain explicit approval of its current plan. Read the [planning guidance](../../../content-studio-workflow/references/planning.md). Profile the source, select bounded candidate ranges or a standalone candidate, and give the exact commands, outputs, estimates, fallback, rights evidence and listening criteria. Source download and small diagnostics may inform that plan.

From the repository root, after approval:

```powershell
python content-studio/skills/content-studio-video/audio/reel-sfx/scripts/reel_sfx.py download --url "https://www.instagram.com/reel/<id>/" --output-dir <private-workspace>
python content-studio/skills/content-studio-video/audio/reel-sfx/scripts/reel_sfx.py extract --source <private-workspace>/reel-<id>.mp4 --source-record <private-workspace>/reel-<id>.source.json --start <seconds> --end <seconds> --name "Short effect name" --category <category> --output <private-workspace>/candidates/<name>.wav
```

Listen to **each complete candidate**, including its start and tail, against the original. A time cut does not remove overlapping speech, music, or ambience; filtering or source separation cannot by itself establish an effects-only result. Reject or revise contaminated candidates. Mark `--effect-review passed` only after a human has heard an isolated effect with no voice or music bleed. Unknown rights remain reference-only even after audio review. Record the creator and canonical source URL; do not claim the uploader owns a third-party effect.

If an approved plan uses an external source separator to compare a mixed-track cut, preserve the raw cut and record the separator, model/checkpoint hash, settings, service destination when uploaded, and hashes of every returned stem. Compare the full raw and separated cuts with the editor before choosing one; a laugh may land in a speech stem or be damaged in the effects stem. Keep an unapproved or contaminated stem out of the catalogue. This is a comparison route, not an automatic voice-removal capability of `reel_sfx.py`.

For a private reference entry, use `scripts/library.py add --kind sfx --rights unknown --effect-review pending` in the [stock library](../../stock-library/README.md). Supply the real creator, source URL, source range and source SHA-256 from the candidate sidecar. The stock catalogue records unknown-rights or unreviewed files as `reference-only`; never use them in a delivery timeline or publish them until rights and isolation are confirmed. Do not paste audio or full reel media into this repository.

To find effects previously accepted by the editor, query the private catalogue with `python content-studio/skills/content-studio-video/stock-library/scripts/library.py --library <private-library> list --kind sfx`. The skill package contains the workflow; the catalogue and WAVs stay together in the private library outside Git. Check that the listed file hashes and review states match the assets before proposing one for a new edit.

The [method guide](README.md) records the supported commands and verification limits.
