---
name: content-studio-video-memory
description: Store confirmed Content Studio editing preferences and review decisions in a private SQLite database shared across chats.
---

# Editing memory

The database defaults to `%LOCALAPPDATA%/ContentStudio/editing-memory.sqlite` on Windows and the XDG state directory on other systems. Set `CONTENT_STUDIO_MEMORY_DB` to use another private path, or pass `--db` to one command. Keep the database outside Git. A new chat reads the same database through the workflow precheck; if it does not exist, the plan reports that no preferences were found. Chat history itself is not the editing memory.

From the repository root:

```powershell
python content-studio/skills/content-studio-video/memory/scripts/memory.py retrieve --scope travel --project dubai-day-2
python content-studio/skills/content-studio-video/memory/scripts/memory.py set --key meme_intensity --value low --scope travel
python content-studio/skills/content-studio-video/memory/scripts/memory.py record --feature meme --decision rejected --scope travel --project dubai-day-2 --reason "Interrupts dialogue"
python content-studio/skills/content-studio-video/memory/scripts/memory.py events --scope travel
python content-studio/skills/content-studio-video/memory/scripts/memory.py forget --key meme_intensity --scope travel
```

Only save a preference after the user explicitly confirms it. `retrieve` merges `global`, category (`travel`, `cooking`, `daily`), and optional `project:<id>` layers; the most specific wins. A direct editing skill retrieves applicable values before planning its route. Explicit instructions in the current request outrank saved preferences. Memory never approves an edit or publication. `record` logs review history, not an automatically reusable preference. `forget` removes a preference; `purge-events` removes selected event history.

AutoCut is experimental and explicit-request-only. It reads confirmed `autocut_fit`, `autocut_duration`, and `autocut_style` from the shared database when present, but explicit CLI values on this invocation win. Its review command logs a real review event; it never promotes a candidate preference on its own.

`timeline_diff.py` compares Content Studio JSON timeline revisions. `kdenlive_import.py` and `compare_kdenlive.py` generate bounded source-range observations from simple Kdenlive MLT playlists; complex compositing, timewarp, and uncertain visibility are flagged. `learn_from_edit.py` writes a local review page and comparison; a human must inspect the actual project before `confirm_diff.py --confirm-reviewed` logs an observation. `learn.py` groups repeated explicit feedback into **candidates** only. Neither observations nor candidates become preferences without a separate `set` after user confirmation.

Before any production edit, use the mandatory `content-studio-workflow` precheck. It displays saved preferences and binds a reviewed plan to the selected method command. Keep event context, source hashes, and reasons with review evidence; do not claim that an uninspected Kdenlive change proves user intent.
