---
name: content-studio-video-timeline
description: Plan, validate, approve, and render an immutable Content Studio delivery timeline.
---

# Delivery timeline

Use this skill after the mandatory `content-studio-workflow` precheck and explicit human approval of its plan. Build a timeline for a supplied manual edit or approved source selection. The timeline is a proposal until the editor reviews the resolved timing, voice assets, picture and audio effects, transitions, output settings, and a fingerprint. Never create a human approval record on the editor's behalf.

`scripts/timeline.py` provides `init`, `revise`, `validate`, `preview`, `fingerprint`, `render`, and `verify`. Final render requires a separate human timeline approval matching the exact revision and current input bytes. Revisions create a new timeline file and need a new approval. Unsupported methods fail validation before encoding. Preserve originals and check the exact rendered video and audio before package approval.

Current delivery adapters are deliberately narrower than the specialist catalog. A specialist preview or separate render is not evidence that a method works in this single-export route. See `methods.json` for current timeline-ready methods.

## Draft and review a timeline

The production plan at `.content-studio/preflight/plan.json` must already have
its human approval and matching checklist. For a supplied manual export:

```powershell
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py init `
  --plan <draft>/.content-studio/preflight/plan.json `
  --source <draft>/<id>-manual-edit.mp4 `
  --output <draft>/<id>-final.mp4 `
  --timeline <draft>/.content-studio/timeline/timeline-v001.json
```

`init` records the whole supplied export as one picture clip. Edit the
timeline through `revise --timeline <old.json> --plan <current-approved-plan.json>
--changes <changes.json> --out <new.json> --output <new-final.mp4>`. The changes file replaces complete
top-level arrays such as `picture`, `operations`, or `audio`; the old
revision remains intact. Every referenced source, voice file, font, and ASS
sidecar needs a lowercase SHA-256 hash. `timeline.py hash --file <asset>`
prints it. Paths to those assets are relative to `source_root`.
Each revision snapshots the approved plan, its approval, and checklist beside
the timeline file. A changed plan needs its own human preflight approval before
`revise` can use it; prior revisions keep their plan snapshots.

Operation times are seconds on the resolved output timeline, after cuts and
transition overlaps. Each operation and audio cue has a stable `id`, a
`start` and `end` when applicable, a method, and `review_status`.
Use `pending_review` while drafting. `validate` prints the resolved
duration and mapping. `preview --start <seconds> --duration <seconds>
--output <preview.mp4>` makes a short composite candidate without final
approval. Keep the preview separate from the final output.

## Approve and render

After reviewing the exact timeline, voice, edits, effects, and output settings,
mark every selected operation and audio cue `approved` in a new revision.
`fingerprint --timeline <revision.json>` prints the exact approval
fingerprint. Record only a genuine human decision in an approval JSON file:

```json
{
  "actor": "human",
  "reviewer": "editor name",
  "review_note": "Reviewed timing, voice, edits, effects and output",
  "approved_at": "2026-11-08T16:00:00+05:30",
  "fingerprint": "<printed fingerprint>"
}
```

```powershell
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py render `
  --timeline <revision.json> --approval <human-approval.json>
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py verify `
  --record <final.mp4.render.json> --evidence-dir <draft>/.content-studio/timeline/final-review
```

`render` encodes one final video and audio file. `verify` checks the
exact output and creates bounded frames and audio samples for human review;
it does not approve subjective quality or package publication. A changed
timeline, source, voice, font, sidecar, plan, or renderer capability invalidates
the prior timeline approval. Do not silently fall back to the specialist
full-master scripts when an operation is unavailable in this route.

The current route is SDR only. AI upscale, HDR/Dolby Vision, and methods marked
`unsupported` in `methods.json` require further adapters and evidence.

For a full length, uncut source with no audio edits, set `audio_policy` to
`copy_source` in a timeline revision. This copies the source audio packets into
the one final export without an audio encoder; validation rejects cuts, joins,
audio cues, gain changes, missing audio, and shortened source ranges. The
default `mix` policy keeps the existing audio graph. `video_preset` accepts
`medium` (default), `fast`, or `veryfast` for the single x264 encode. Review
the chosen preset and audio policy as part of timeline approval.
