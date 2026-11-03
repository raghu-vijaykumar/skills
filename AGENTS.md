# AGENTS.md

## Repository

Editable source for the `content-studio` video lifecycle bundle. The npm
package name remains `@raghu-vijaykumar/videogen`.

## Before changing code

1. Read the owning `SKILL.md` and its `references/`.
2. Read `README.md` for the end-to-end draft lifecycle and current draft layout.
3. Inspect existing tests before adding parallel systems.

## Draft layout

```text
drafts/<id>/
  original/
  .content-studio/
    _timeline.csv
    processed-clips/
    autocut-input/
    analysis/
    rough-cut/
    audio/
    tmp/
  <id>-rough-cut.mp4
  <id>-preprocessed.mp4
  <id>-final.mp4
  <id>-audio-only.mp3
  title.txt
  description.txt
  creative.json
  lifecycle-checklist.json
  draft.json
```

Vlog drafts do not generate transcripts or captions. Metadata must be derived
from sampled frames and audio context, never placeholders.

## Commands

```powershell
npm run check:docs
python -m unittest discover -s content-studio/skills/content-studio-videoedit/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-autocut/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-music/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-audio/tests -p "test_*.py"
node --test content-studio/tests/*.test.mjs content-studio/skills/content-studio-videogen/tests/*.test.mjs
```

## Enhancement rules

- Diagnosis before correction. Never enhance because a feature is enabled.
- Record every issue independently as `SKIP`, `FIX`, `REVIEW`, or `UNSUPPORTED`.
- Color corrections are temporal, quality-gated, and non-destructive.
- Strong reflections are review/unsupported until a licensed backend is
  benchmarked. Do not treat inpainting as faithful reconstruction.
- Preserve originals, audio, and project edits.
- Cache analyses by source hash and analysis version; make renders idempotent.
- Update tests and documentation with each enhancement phase.

## Commits

Use the existing conventional style:

```text
feat: ...
fix: ...
docs: ...
change: ...
```

Commit at coherent intervals. Do not include generated media, secrets, or
machine-specific config.
