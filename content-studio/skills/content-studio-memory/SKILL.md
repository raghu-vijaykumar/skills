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

## Timeline revision comparison (implemented)

Compare two **Content Studio** JSON timeline revisions, without changing either:

```bash
python content-studio/skills/content-studio-memory/scripts/timeline_diff.py --before path/to/timeline-v001.json --after path/to/timeline-v002.json --output path/to/diff.json
```

Detects removed/added clips, trims, audio gain changes, source replacements and reordering. Clip IDs are matched within a revision lineage, with source paths and source in/out ranges included as evidence. The output is **observational** and never automatically promotes a rule. Do not pass Kdenlive MLT directly; its parser and source reconciliation are still pending.

## AutoCut review capture (implemented, opt-in)

`content-studio-autocut/scripts/review.py` now accepts `--memory-db <local-db> --category travel|cooking|daily --project <id>`. When a human explicitly approves or requests changes, it writes a corresponding event to the local database. If memory recording fails, the saved review remains valid and a warning is printed. Agent revisions do not count as human approvals.

## Kdenlive import and conservative learning (initial implementation)

```bash
python content-studio/skills/content-studio-memory/scripts/kdenlive_import.py --input my-edit.kdenlive --output kdenlive-observations.json
python content-studio/skills/content-studio-memory/scripts/compare_kdenlive.py --proposed .content-studio/rough-cut/timeline.json --edited kdenlive-observations.json --output comparison.json
python content-studio/skills/content-studio-memory/scripts/learn.py --db "D:/ContentStudio/memory/memory.sqlite"
```

The importer parses simple MLT producer/chain resources and playlist entries, resolving source in/out ranges and reporting unsupported nested tractor compositing, timewarp, or unresolved media. The comparison reports source ranges that were shortened or removed relative to the proposal. **It does not reliably reconstruct Kdenlive's rendered composite**; multiple playlists, transitions, nested tractors and duplicate filenames require human verification. Do not use these observations as definitive proof that a clip was cut.

The learning command groups repeated **explicit human feedback reasons** by category and feature; requires at least three events from at least two projects; and emits reviewable preference candidates only. It does not update preferences or infer motives from Kdenlive changes. A user must confirm any candidate before adding an explicit preference with `memory.py set`.

Run tests locally using `python -m unittest discover -s content-studio/skills/content-studio-memory/tests`. Tests are committed but not verified in this environment.

## Applying confirmed preferences to AutoCut

AutoCut supports `--memory-db D:/ContentStudio/memory/memory.sqlite --category travel --project dubai-day-2`. Only explicit `autocut_fit` (pad/blur/crop), `autocut_duration` (valid time <= 4h) and `autocut_style` are applied. The exact applied values are recorded in `edit-decisions.json`. Inferred candidates are never applied. An explicitly supplied CLI value may be overridden by a stored preference; omit `--memory-db` to bypass preferences.

## Recording verified Kdenlive observations

After visually checking the imported source ranges and comparison report, the **human** may run:

```bash
python content-studio/skills/content-studio-memory/scripts/confirm_diff.py --db "D:/ContentStudio/memory/memory.sqlite" --report comparison.json --scope travel --project dubai-day-2 --confirm-reviewed --reason "Removed repetitive shots"
```

This adds observed human-confirmed events, once per report/project fingerprint. Reports with importer issues are rejected. Confirmed observations **do not become preferences** without explicit confirmation. The `learn.py` candidate generator intentionally considers only changed/rejected decisions, not generic observations. Complex Kdenlive tractor/compositing reconstruction remains unsupported; the importer explicitly reports this rather than pretending to know rendered track order.
