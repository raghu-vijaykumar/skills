# Retime methods and review

The retime route starts with a human-approved Content Studio precheck and an
existing versioned delivery timeline for the supplied manual edit. Identify
the reason to retime and record baseline source frames, duration, source audio,
and later cue times. A no-change speed or an unsuitable source is `SKIP` or
`UNSUPPORTED`; preserve the prior revision.

`propose` splits the selected picture clip at frame-aligned source times and
writes only a `changes.json` and a report. It shifts later visual and audio
cues by the resolved duration difference. A cue crossing the retime range,
external recorder sync, or a join transition requires separate human timing
work and is rejected. Existing ASS caption sidecars and full-video object
masks after the retime must be regenerated against the new timing; the
proposal refuses them instead of shifting only their wrapper. No source or
final media is changed by proposal.

```powershell
python content-studio/skills/content-studio-video/edit/retime/scripts/retime.py propose `
  --timeline <timeline-v001.json> --clip-id p0001 `
  --source-start 2 --source-end 4 --method speed --factor 0.5 --audio tempo `
  --changes <draft>/.content-studio/timeline/retime-changes.json `
  --report <draft>/.content-studio/analysis/retime-review.json `
  --final-output <draft>/<id>-final-v002.mp4
```

Use `--method freeze --hold-seconds 1.5 --audio mute` with exactly one source
frame, `--method reverse --audio reverse` (or `mute`), or `--method loop
--count 3 --audio repeat` (or `mute`). Speed accepts 0.25–4× and `tempo` or
`mute`. Reverse input is at most 15 seconds; loop source is at most 10 seconds,
count is 2–8, and output at most 60 seconds. Freeze hold is 0.1–10 seconds.
All modes require explicitly tagged, constant-frame-rate, zero-rotation SDR
H.264 8-bit source matching timeline FPS. Source frame ranges and freeze holds
must align to picture frames. Reverse's estimated decoded picture buffer is
limited to 512 MiB and loop's to 256 MiB; use the precheck capacity benchmark
before selecting either. Other media remain `UNSUPPORTED` until tested.

Apply the proposal through the existing immutable revision route using the
current approved preflight plan:

```powershell
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py revise `
  --timeline <timeline-v001.json> --plan <draft>/.content-studio/preflight/plan.json `
  --changes <retime-changes.json> --out <timeline-v002.json> `
  --output <draft>/<id>-final-v002.mp4
python content-studio/skills/content-studio-video/edit/retime/scripts/retime.py preview `
  --timeline <timeline-v002.json> --start <review-start> --duration <short-span> `
  --out <draft>/.content-studio/tmp/retime-preview.mp4
```

Review the first, middle, and last frames of the retime, motion cadence, audio
at every boundary, the resolved duration, and all shifted narration, music,
and graphics. Record the chosen fix or `SKIP`, rejected candidates,
and human review against the new revision. The proposal contains
`retime_review_status: pending_review`; after a human passes the preview,
change that value to `approved` in a reviewed copy of the changes file and
create another immutable timeline revision with `timeline.py revise` using
`--timeline <timeline-v002.json> --changes <retime-reviewed-changes.json>
--out <timeline-v003.json> --output <draft>/<id>-final-v003.mp4` and the
current approved `--plan`. `fingerprint` and final `render` reject a pending
review. If it fails, revise a bounded
parameter or retain the previous timeline; a changed revision needs new human
approval. After separate timeline approval, run one final timeline render and
the exact-master `verify`. Check actual retimed frames, sound, later cues, and
technical findings before package approval. Publication remains separate.
