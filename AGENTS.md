# AGENTS.md

## Repository

Editable source for the `content-studio` video lifecycle bundle. The npm
package name remains `@raghu-vijaykumar/videogen`.

## Before changing code

1. Read the owning `SKILL.md`, its `references/`, and `methods.json` when present. Nested skills under `content-studio-video/` are individually callable.
2. Read `README.md` for the end-to-end draft lifecycle and current draft layout.
3. Inspect existing tests before adding parallel systems.

## Mandatory precheck before Content Studio editing

Before any production edit, including a direct specialist skill call, use the
precheck in `content-studio-workflow`. Inspect the channel, draft, source media,
system capacity, and bounded benchmarks; show the user a detailed, editable
plan with recommended routes, selected method IDs, exact script commands and
arguments, time estimates, outputs, fallbacks, and review criteria.
Incorporate requested changes and obtain explicit human approval of the current
plan revision before editing. This gate is mandatory and cannot be skipped.
Follow the checklist generated from the approved plan, record evidence for each
step, and complete it before package approval. A changed plan requires another
human review. Read-only diagnosis and short comparison previews may inform the
plan; publishing still needs its separate explicit authorization.

## Draft layout

```text
drafts/<id>/
  original/
  .content-studio/
    _timeline.csv
    processed-clips/
    autocut-input/
    analysis/
    rough-cut/                       # AutoCut only when explicitly requested
    audio/
    understanding/
    upscale/
    motion-graphics/
    preflight/
    tmp/
  <id>-manual-edit.mp4                # or the user's supplied render path
  <id>-final.mp4
  <id>-audio-only.mp3
  title.txt
  description.txt
  creative.json
  lifecycle-checklist.json
  draft.json
```

For a raw video folder, prepare individual clips and stop for the user's manual
edit. AutoCut is experimental and explicit-request-only. After the user supplies
a rendered edit, requested voice runs first, then justified full-edit upscale,
then code-generated scene overlays at delivery resolution. Vlog drafts do not
generate transcripts or captions by default. Metadata must be derived from
sampled frames and audio context, never placeholders.

## Commands

```powershell
npm run check:docs
python -m unittest discover -s content-studio/skills/content-studio-video/edit/clip-edit/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-video/edit/autocut/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-video/edit/reflection/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-video/edit/transitions/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-video/source/preprocess/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-video/edit/reflection/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-video/audio/music/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-video/audio/mastering/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-video/audio/narration/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-video/memory/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-workflow/tests -p "test_*.py"
python -m unittest discover -s content-studio/skills/content-studio-video/review/understand/tests -p "test_*.py"
node --test content-studio/tests/*.test.mjs content-studio/skills/content-studio-video/animation/videogen/tests/*.test.mjs
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
  benchmarked. Do not treat inpainting as faithful reconstruction. The bundled
  DSRNet pass attenuates a predicted reflection layer; it never reconstructs
  occluded content and always returns a review result.
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
