---
name: content-studio-video-timeline
description: Plan, validate, approve, and render an immutable Content Studio delivery timeline.
---

# Delivery timeline

Use this skill after the mandatory `content-studio-workflow` precheck and explicit human approval of its plan. Build a timeline for a supplied manual edit or approved source selection. The timeline is a proposal until the editor reviews the resolved timing, voice assets, picture and audio effects, transitions, output settings, and a fingerprint. Never create a human approval record on the editor's behalf.

`scripts/timeline.py` provides `init`, `revise`, `validate`, `preview`, `fingerprint`, `render`, and `verify`. Final render requires a separate human timeline approval matching the exact revision and current input bytes. Revisions create a new timeline file and need a new approval. Unsupported methods fail validation before encoding. Preserve originals and check the exact rendered video and audio before package approval.

Current delivery adapters are deliberately narrower than the specialist catalog. A specialist preview or separate render is not evidence that a method works in this single-export route. See `methods.json` for current timeline-ready methods.

Hero-led long-form [clipping](../edit/clipping/SKILL.md) hands reviewed source intervals and stable crop proposals to this renderer as pending operations. Its crop entries bind the selection, source evidence, and proposal files by hash. A changed review file invalidates timeline validation before render; the editor still approves the exact timeline revision separately.

`text-behind-subject` is a supported SDR graphic operation. It draws a rising title behind a hashed foreground matte generated locally for each shot; see the [motion graphics preset](../edit/motion-graphics/references/text-behind-subject.md). The cue must stay within one picture shot and outside join overlaps. Review the matte and moving composite before human timeline approval.

`object-blur` is a supported SDR concealment operation for one uncut finished edit. The [object blur skill](../edit/object-blur/SKILL.md) detects the named target on each frame and supplies a hashed lossless mask. The timeline requires a matching human full-frame coverage record before approval and composites blur in the final encode.

Explicitly requested [captions](../edit/captions/SKILL.md) arrive as a `pending_review` `motion-graphics-ass` operation. Validate the sidecar and font hashes, inspect the cue/font/safe-zone preview, then approve a new timeline revision for the single final encode. No caption operation is added to ordinary vlog drafts.

For a separately recorded microphone, [sync](../source/sync/SKILL.md) first creates a hashed analysis and bounded camera-left/recorder-right audition. Reanalyze against the exact supplied manual render after any manual cuts. A reviewed `external_sync` audio cue then binds the report and recorder bytes, exact offset/drift, muted camera audio, and one uncut SDR picture. The native renderer applies alignment within the final audio mix; verify early and late lip/event sync in the exact master.

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
For cut timelines, the renderer seeks each source input to its retained span
before decoding. This avoids decoding a long source from frame zero for every
kept segment; the final picture and audio are still encoded once. A timeline
preview late in a long edit may still process preceding timeline spans, so use
short source-linked cut previews for boundary review and benchmark the actual
final route before committing to a long render.

Each revision snapshots the approved plan, its approval, and checklist beside
the timeline file. A changed plan needs its own human preflight approval before
`revise` can use it; prior revisions keep their plan snapshots.

A licensed music cue may set `"loop": true` with a finite `"duration"` in
seconds, measured from its `start`. Optional `fade_in` and `fade_out` seconds
soften the bed edges. The renderer loops the hashed source at decode time and
trims it before mixing, so the music stays on the one delivery timeline. Review
the repeat seam and the music level against narration in bounded previews.

One approved `loudnorm` operation may span the entire resolved picture duration. The renderer first measures the final source/voice/music mix without an intermediate media master. If the mix is outside -16 ±1 LUFS or exceeds -1.5 dBTP, the final encode uses the measured two-pass parameters once; an already acceptable mix records `SKIP`. `verify` remeasures the exact delivered audio and marks a missed correction `REVIEW`. Listen to voice clarity, music balance and pumping; loudness numbers alone do not approve the package. The separate [folder mastering command](../audio/mastering/SKILL.md) remains available for independent audio-only exports.

A bounded timeline preview uses provisional dynamic loudnorm; the full output uses measured parameters from the entire resolved mix. For a supplied HDR/Dolby Vision edit with audio-only changes, the same audio analysis is available while the coded picture remains in the verified packet-copy path.
Voice cues may have up to 0.12 seconds of source tail beyond the picture; the
output graph trims that tail at the resolved picture duration. Longer voice
overruns fail validation so incomplete narration is not silently dropped.

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
exact output, runs the [hash-bound final-render inspector](../review/final-render/SKILL.md)
for format, loudness, timecoded content candidates and safe-zone guide frames,
and creates bounded frames and audio samples for human review;
it does not approve subjective quality or package publication. A changed
timeline, source, voice, font, sidecar, plan, or renderer capability invalidates
the prior timeline approval. Do not silently fall back to the specialist
full-master scripts when an operation is unavailable in this route.

Picture-processing delivery remains SDR only. For an already edited HDR/Dolby Vision source with **audio-only** changes, `init --preserve-picture` creates a timeline that copies its coded video packets while mixing approved audio. It rejects cuts, joins, picture operations, or source-audio gain changes. The final render and `verify` compare every video packet payload plus HDR/Dolby Vision stream metadata against the source and stop if preservation cannot be established. A bounded preview may use a different packet range; inspect the exact final output before package approval. AI upscale and HDR/Dolby Vision picture operations remain unsupported.

The approval fingerprint binds the timeline, approved plan, source assets, and
renderer capability. Preflight checklist evidence may continue to be recorded
after timeline approval; its matching plan hash and step IDs are still checked.

For a full length, uncut source with no audio edits, set `audio_policy` to
`copy_source` in a timeline revision. This copies the source audio packets into
the one final export without an audio encoder; validation rejects cuts, joins,
audio cues, gain changes, missing audio, and shortened source ranges. The
default `mix` policy keeps the existing audio graph. `video_preset` accepts
`medium` (default), `fast`, or `veryfast` for the single x264 encode. Review
the chosen preset and audio policy as part of timeline approval.

Point transitions carry editable `start` and `end` times on the resolved edit.
`cross-blur` now eases blur up to the window midpoint and back down; a longer
window therefore changes the transition speed without shifting frames or
touching source audio. Its `blur_sigma` can be set from 1 to 80 to make the
effect readable at delivery size (default 10). Show a bounded preview after
changing times or strength.

The timeline now accepts all specialist transition IDs: six time-preserving
point effects in `operations` and 26 two-shot clip joins in `transitions`.
Every point range and join overlap is editable from 0.15 to 3 seconds. The
eight custom joins—collage, page turn, liquid streaks, liquid drops, fire,
zoom-out, spin, and heart—are labelled approximations in the transition
catalog. They need two actual clips; a continuous master cannot stand in for
a two-shot transition. The shared custom recipes and catalog are included in
the approval capability hash, so a recipe change needs a new human approval.
