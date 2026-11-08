---
name: content-studio-video-memes
description: Maintain a private local meme catalogue and propose evidence-based, reviewable insertions for travel, cooking and daily vlogs.
---
# Content Studio Memes

Before inserting or rendering memes in a draft, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist.

This skill **does not download memes automatically**. The user will add meme files later. Import only user-supplied, authorized media into a local catalogue. Do not commit third-party media, generated thumbnails or the SQLite database to Git.

## Catalogue

Run from the repository root:

```bash
python content-studio/skills/content-studio-memes/scripts/memes.py --library "D:/ContentStudio/memes" init
python content-studio/skills/content-studio-memes/scripts/memes.py --library "D:/ContentStudio/memes" add --file "/path/to/approved-reaction.mp4" --name "Surprised reaction" --tags "surprise,travel,funny" --language kn --license "owned" --source "my-recording"
python content-studio/skills/content-studio-memes/scripts/memes.py --library "D:/ContentStudio/memes" search --query surprise --category travel
python content-studio/skills/content-studio-memes/scripts/memes.py --library "D:/ContentStudio/memes" list
```

Use `--license` with an accurate value (`owned`, `licensed`, `permission`, or `unknown`). Items with `unknown` rights are not eligible for publishing suggestions. The user is responsible for confirming authorization. Imports are SHA-256 deduplicated; source files are preserved and copied to the catalogue, not moved.

## Suggestion workflow

Read the approved video timeline, narration, user-provided context and candidate reactions. Suggest only contextually appropriate memes (default maximum 1–3 per 10 minutes). Do not claim visual or emotional understanding from sparse frames alone; attach a timestamp and a reason grounded in actual scene or dialogue evidence. Propose a non-destructive insertion manifest with `meme_id`, `at_seconds`, `duration_seconds`, `mode` (`cutaway`, `pip`, `audio_stinger`), `reason`, and `status: pending_review`. Do not automatically render or publish memes. Human review must approve both rights and timing before an editable timeline is modified. Avoid interrupting dialogue or emotional moments.

Preset rules live in `presets/`. The initial implementation supports catalogue management and keyword search; automated semantic detection, timeline insertion and previews are future integrations.

## Editing memory integration
Before suggesting memes, retrieve applicable explicit preferences using `content-studio-memory`; respect scoped `meme_intensity` and human-provided exclusions. After a human approves or rejects a meme proposal, record that outcome using the memory skill with `--feature meme` and the real scene context. This is a documented agent handoff, not yet an automatic code hook.
