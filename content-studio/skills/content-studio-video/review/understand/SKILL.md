---
name: content-studio-video-understand
description: Analyze sparse frames from an approved vlog edit, combine verified visual evidence with human context, and draft timestamped voiceover for review.
---
# Content Studio Understand

Before changing production material, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist. Read-only evidence extraction may inform the plan.
Run only against the **approved edit** or a review candidate explicitly supplied by the user. Do not infer landmarks, identities, speech, or events from filenames. Sparse frames cannot establish everything happening between samples. Use the generated contact sheets and timestamped evidence to ask the user about ambiguous scenes.

## 1. Extract review evidence

```bash
python content-studio/skills/content-studio-understand/scripts/understand.py \
  --video /path/to/approved-final.mp4 \
  --out /path/to/draft/.content-studio/understanding \
  --interval 5 \
  --grid-cols 5 --grid-rows 4 --frame-width 480 \
  --context /path/to/context.json
```

Writes:

- `frames/frame-*.jpg`: low-resolution frames sampled about every `--interval` seconds.
- `sheets/sheet-*.jpg`: timestamped contact sheets for quick visual review.
- `evidence.json`: source SHA-256, duration, frame times, sheet ranges, and supplied context.
- `voiceover-template.json` and `observations-template.json`: empty scaffolds.

Use `--start`/`--end` for a range, `--no-grid` to skip sheets, and `--frame-width` to change thumbnail size. Timestamps come from the PTS of the frames FFmpeg selected and are approximate within one sample interval. These frames are review evidence, not delivery media. Contact sheets need Pillow.

Open the contact sheets first, then individual frames for ambiguous moments. Write `observations.json` as an array of `{start,end,description,confidence,frame_ids}` using only observed evidence. Cite frame IDs, not guessed timestamps. Mark uncertainty. Never infer a landmark, identity, exhibit text, or event from a filename.

Use `context.json` for human-supplied names, itinerary, language, tone, pronunciation, and personal experiences. Treat it as the source of truth for facts the footage cannot prove.

## 2. Draft and validate the voiceover

Write `voiceover.json` with `{id,start,end,text,evidence_frame_ids,needs_review,direction,notes}` segments. Keep the text in the requested language mix; read [voiceover guidance](references/voiceover.md) before writing.

```bash
python content-studio/skills/content-studio-understand/scripts/voiceover.py \
  --input /path/to/understanding/voiceover.json \
  --evidence /path/to/understanding/evidence.json \
  --out /path/to/understanding \
  --title "Dubai Day 3"
```

Writes `voiceover.md`, `voiceover-teleprompter.txt`, `voiceover.csv`, and `voiceover-report.json`. The validator fails on overlapping segments, out-of-range times, unknown evidence frames, and speech over the pace limit. Fix the errors, then present the markdown and timing report for human review.

Voiceover must fit the **approved timeline**; use scene times in the rendered master, not raw source timestamps. Leave room for original dialogue where requested. Obtain explicit human approval of the final narration text and timing before synthesizing or recording audio. A changed final master invalidates the approval and requires regeneration or retiming.

`content-studio-voice` only enrolls a consented voice profile; it does not write scripts or synthesize speech. Script authoring stays here. After the script is approved, return to `content-studio-voice` for a reviewed backend and listening approval.
