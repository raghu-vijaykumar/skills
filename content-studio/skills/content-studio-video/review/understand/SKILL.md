---
name: content-studio-video-understand
description: Analyze sparse frames from an approved vlog edit, combine verified visual evidence with human context, and draft timestamped voiceover for review.
---
# Content Studio Understand

Before changing production material, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist. Read-only evidence extraction may inform the plan.
Run only against the **approved edit** or a review candidate explicitly supplied by the user. Do not infer landmarks, identities, speech, or events from filenames. Sparse frames cannot establish everything happening between samples. Use the generated contact sheets and timestamped evidence to ask the user about ambiguous scenes.

## 1. Extract review evidence

```bash
python content-studio/skills/content-studio-video/review/understand/scripts/understand.py \
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
- Bounded `--start`/`--end` evidence retains absolute source timestamps; check the sheet labels before aligning narration, especially near the range end.
- `voiceover-template.json` and `observations-template.json`: empty scaffolds.

Use `--start`/`--end` for a range, `--no-grid` to skip sheets, and `--frame-width` to change thumbnail size. Timestamps come from the PTS of the frames FFmpeg selected and are approximate within one sample interval. These frames are review evidence, not delivery media. Contact sheets need Pillow.

Open the contact sheets first, then individual frames for ambiguous moments. Write `observations.json` as an array of `{start,end,description,confidence,frame_ids}` using only observed evidence. Cite frame IDs, not guessed timestamps. Mark uncertainty. Never infer a landmark, identity, exhibit text, or event from a filename.

Use `context.json` for human-supplied names, itinerary, language, tone, pronunciation, and personal experiences. Treat it as the source of truth for facts the footage cannot prove.

## 2. Draft and review every cue against picture

Write `voiceover.json` with `{id,start,end,text,evidence_frame_ids,needs_review,direction,notes}` segments. Keep the text in the requested language mix; read [voiceover guidance](references/voiceover.md) before writing.

After a first draft, sample the **exact locked picture** around both boundaries and the middle of every cue:

```bash
python content-studio/skills/content-studio-video/review/understand/scripts/scene_review.py prepare \
  --video /path/to/approved-final.mp4 \
  --script /path/to/understanding/voiceover.json \
  --out /path/to/understanding/cue-scene-review
```

Open **every** cue sheet, inspect individual frames around ambiguous transitions, and set `visual_start`, `visual_end`, `visual_description`, and `scene_match` in `scene-review.json`. These bounds come from the picture, not an evenly spaced narration grid. A line may start up to 0.5 seconds before its visual beat, but its spoken end must stay inside the reviewed visual end. Mark mismatches `rewrite` or `pending`, then rewrite/shorten the cue or move it to the correct scene. Regenerate the review after any script timing/text change; exact script and picture hashes prevent stale approval. The tool extracts evidence automatically but cannot infer whether Kannada-English wording describes the scene. A vision-capable reviewer must make that judgment for each cue.

Before presenting a draft, audit each location across adjacent cues. Replace repeated descriptions of the same movement, displays, or shopping with a distinct creator moment or a useful, verified fact about the place, craft, history, transport, or visit. Source facts outside the footage and creator context from a reliable primary source; record the URL in the cue's `notes`. A place fact must not imply the travelers saw, bought, or did something unsupported by the edit. When no relevant fact improves a long shot, shorten the narration and leave room for its original sound. Include the changed cues and any open fact checks in the review notes.

```bash
python content-studio/skills/content-studio-video/review/understand/scripts/voiceover.py \
  --input /path/to/understanding/voiceover.json \
  --evidence /path/to/understanding/evidence.json \
  --scene-review /path/to/understanding/cue-scene-review/scene-review.json \
  --out /path/to/understanding \
  --title "Dubai Day 3"
```

Writes `voiceover.md`, `voiceover-teleprompter.txt`, `voiceover.csv`, and `voiceover-report.json`. The validator fails on overlapping segments, out-of-range times, unknown evidence frames, speech over the pace limit, missing scene reviews, or cue windows outside reviewed picture bounds. Fix the errors, then present the markdown, cue sheets, and timing report for human review.

Voiceover must fit the **approved timeline**; use scene times in the rendered master, not raw source timestamps. Leave room for original dialogue where requested. Obtain explicit human approval of the final narration text and timing before synthesizing or recording audio. A changed final master invalidates the approval and requires regeneration or retiming.

After synthesis, measure each actual cue WAV at **1.0×** against its visual end. If it runs long, shorten the text and regenerate that cue; do not speed up, overlap another scene, or let the assembler shift the next cue. Recheck the resulting picture and audio together in the encoded mix.

`content-studio-voice` only enrolls a consented voice profile; it does not write scripts or synthesize speech. Script authoring stays here. After the script is approved, return to `content-studio-voice` for a reviewed backend and listening approval.
