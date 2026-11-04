---
name: content-studio-memory
description: Learn local, reviewable editing preferences from explicit rules and human editing decisions, then retrieve them for future vlog edits.
---
# Content Studio Editing Memory

Local-first, no model training or network dependency. Store the private SQLite database **outside Git** (for example `D:/ContentStudio/memory/memory.sqlite`). Never treat an agent proposal as human feedback. Explicit user preferences take precedence over inferred ones. Do not infer motives from timeline edits without supporting feedback.

## Commands

From the repository root:

```bash
python content-studio/skills/content-studio-memory/scripts/memory.py --db "D:/ContentStudio/memory/memory.sqlite" init
python content-studio/skills/content-studio-memory/scripts/memory.py --db "D:/ContentStudio/memory/memory.sqlite" set --key meme_intensity --value low --scope travel
python content-studio/skills/content-studio-memory/scripts/memory.py --db "D:/ContentStudio/memory/memory.sqlite" record --feature meme --decision rejected --scope travel --project dubai-day-2 --reason interrupts_dialogue --context '{"dialogue_present":true}'
python content-studio/skills/content-studio-memory/scripts/memory.py --db "D:/ContentStudio/memory/memory.sqlite" retrieve --scope travel
python content-studio/skills/content-studio-memory/scripts/memory.py --db "D:/ContentStudio/memory/memory.sqlite" events --scope travel
python content-studio/skills/content-studio-memory/scripts/memory.py --db "D:/ContentStudio/memory/memory.sqlite" forget --key meme_intensity --scope travel
```

`record` only accepts explicit `--actor human` (default); agent-generated events can be logged with `--actor agent` but must never be used as evidence of preference. The `retrieve` command emits JSON for downstream editing tools. Scopes are `global`, `travel`, `cooking`, `daily`, or `project:<id>`; retrieval merges global, category and optional project with most specific override winning. `forget` deletes a preference, but leaves historical events intact; use `purge-events` to erase decision history for a project or all projects. No implicit inferred preferences are promoted to permanent rules.

## Integration contract

1. Before AutoCut, graphics, memes, voiceover or audio processing, call `retrieve --scope <category> [--project <id>]` and treat explicit preferences as configuration inputs, not commands to blindly execute.
2. At each review gate, log **real** human approvals, rejections and requested changes with feature, reason, project and optional context. Preserve source proposal IDs in context when available.
3. Keep generated timelines and final timelines for a later diff stage. Do not claim passive Kdenlive learning yet: MLT parsing and reliable source-range matching are not implemented.
4. Human approval for rendering or publishing remains mandatory. Memory never constitutes approval.

The first implementation supports deterministic event capture, explicit rules, scoped retrieval, history inspection and deletion. Automatic preference induction, embeddings and Kdenlive comparison are planned separately.
