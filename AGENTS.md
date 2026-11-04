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

- Every video or audio enhancement follows a closed loop: identify a specific
  issue in the source, record its baseline evidence and acceptance criterion,
  compare bounded candidate fixes (including leaving the source alone), and
  verify the exact delivered output against that criterion and side-effect gates.
- Diagnosis before correction. Never enhance because a feature is enabled.
  If the source has no measurable issue, record `SKIP` and preserve it.
- Record the selected candidate, rejected alternatives, source hash, parameters,
  before/after measurements, and links to playable or viewable evidence.
- A preview decision is provisional. Recheck representative affected ranges in
  the final render; a small change or a successful encode alone is not proof the
  issue improved. If verification fails, try a bounded alternative or mark the
  result `REVIEW`/`SKIP` instead of claiming success.
- Human review is required for subjective changes (including creative grading)
  and defects that objective metrics cannot establish. Label explicit overrides
  as unverified until their final output is reviewed.
- Selective upscaling is diagnosis-first: analyze the clip, render a short
  Lanczos/AI preview, gate on detail/noise/flicker, and refuse HDR/DV without an
  explicit tone-map decision.
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
