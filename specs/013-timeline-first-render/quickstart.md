# Delivery timeline quickstart

## Prerequisites

- FFmpeg and FFprobe on `PATH`.
- An approved Content Studio plan at
  `<draft>/.content-studio/preflight/plan.json` with matching
  `approval.json` and `checklist.json`.
- An SDR manual edit or source clip. HDR, Dolby Vision, and 10/12-bit input
  currently stop before rendering.

## Initial timeline

```powershell
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py init `
  --plan <draft>/.content-studio/preflight/plan.json `
  --source <draft>/<id>-manual-edit.mp4 `
  --output <draft>/<id>-final-v001.mp4 `
  --timeline <draft>/.content-studio/timeline/timeline-v001.json
```

The timeline contains one picture clip at first. To add approved cuts,
effects, voice, music, or transitions, make a `changes.json` that replaces
the relevant complete top-level arrays and call `revise`:

```powershell
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py revise `
  --timeline <draft>/.content-studio/timeline/timeline-v001.json `
  --changes <draft>/.content-studio/timeline/changes.json `
  --out <draft>/.content-studio/timeline/timeline-v002.json `
  --output <draft>/<id>-final-v002.mp4
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py validate `
  --timeline <draft>/.content-studio/timeline/timeline-v002.json
```

Use `timeline.py hash --file <asset>` to obtain a source, voice, font,
or motion-graphics sidecar SHA-256. Paths in the timeline are relative to its
`source_root`. The [timeline contract](contracts/timeline.md) specifies
timing and approval fields.

## Preview, human approval, final render

```powershell
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py preview `
  --timeline <revision.json> --start 120 --duration 15 `
  --output <draft>/.content-studio/timeline/review-120-135.mp4
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py fingerprint `
  --timeline <approved-revision.json>
```

The preview can include `pending_review` operations. After a person
reviews the resolved timeline, voice, edits, effects, and output settings,
set selected cues to `approved` in a new revision and obtain the fingerprint.
Record the actual human decision in a JSON file with `actor: "human"`,
`reviewer`, `review_note`, `approved_at`, and the exact `fingerprint`.
The CLI does not create human approval automatically.

```powershell
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py render `
  --timeline <approved-revision.json> --approval <human-approval.json>
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py verify `
  --record <final.mp4.render.json> `
  --evidence-dir <draft>/.content-studio/timeline/final-review
```

`render` makes one final MP4 and a record. `verify` checks its hash,
duration, size, frame rate, 48 kHz audio, and approved revision, measures
requested loudness work, and optionally extracts bounded review samples.
Watch and listen to the affected ranges before package approval. A revision
uses the same sequence with a new output path and human approval.

## Current validation and limits

On 2026-11-08, 22 focused synthetic-media tests passed for cuts, range effects,
geometry, voice placement, transitions, ASS graphics, approval staleness,
HDR refusal, and exact-output checks. The source-prep test, five workflow tests,
134 legacy clip-edit tests (three skipped), and 45 JavaScript tests (one skipped)
passed. The docs check passed. These prove the bounded SDR path, not
subjective picture/audio quality on real footage.

The timeline method registry names the supported subset. AI upscale,
HDR/Dolby Vision and several specialist effects still lack delivery adapters
and must be refused rather than run as sequential full-master passes. The raw
source-prep entrypoint now writes analysis and blur evidence without permanent
clip exports; transferring a reviewed source decision onto the edited timeline
still requires an editor to map the original range into the supplied manual
edit.
