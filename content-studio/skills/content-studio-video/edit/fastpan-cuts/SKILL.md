---
name: content-studio-video-fastpan-cuts
description: Find fast camera pans, review frame-accurate removals with synchronized audio, and hand approved cuts to the native delivery timeline.
---

# Fast pan cuts

Use this leaf when a rapid camera sweep makes footage hard to watch and the editor prefers removing that interval to slowing blurry frames. Complete the mandatory [`content-studio-workflow`](../../../content-studio-workflow/SKILL.md) precheck and obtain approval of its current plan before any production edit. A read-only scan and short comparison previews may inform that plan. Name the exact command, source, output, time estimate, fallback, and review criterion. A changed plan needs renewed human review.

The scanner estimates global horizontal motion in small decoded frames. It can confuse a deliberate follow shot, moving foreground, scene cut, or whip transition with a disposable pan. Inspect source frames and sound around every candidate; choose exact source-frame removal bounds only where both landing and entry remain useful. Never approve cuts from score alone. Preserve the original video and do not use slow motion to conceal blur.

## Commands

```powershell
$fastpan = 'content-studio/skills/content-studio-video/edit/fastpan-cuts/scripts/fastpan.py'
python $fastpan scan --input <source.mp4> --output <draft>/.content-studio/analysis/fastpan-cuts/candidates-v001.json
python $fastpan preview --input <source.mp4> --decisions <decisions-v001.json> --cut-id <id> --output <draft>/.content-studio/analysis/fastpan-cuts/<id>-preview.mp4
python $fastpan timeline-changes --input <source.mp4> --decisions <approved-decisions.json> --timeline <timeline-v001.json> --output <changes-v002.json>
```

The scan records source SHA-256, byte size, modification time, frame rate, candidate frame bounds, screen-width motion speed, coherence, and tracking fraction. `scan` does not alter the source or authorize a cut. The preview removes exactly the requested source frames and the matching audio samples from a bounded window (30 seconds maximum). Listen for speech or music damage and inspect both sides of each join. Revise the decision file and preview again when the cut hides context or lands badly.

Create a decision file from the report's source fields, with frame indices checked against the original. Example:

```json
{
  "schema": "content-studio.fastpan-decisions.v1",
  "source": "<absolute source path>",
  "source_sha256": "<scan report SHA-256>",
  "source_bytes": 123456,
  "source_mtime_ns": 123456789,
  "fps": 30,
  "cuts": [
    {"id": "pan-0001", "start_frame": 1800, "end_frame": 1890, "review_status": "pending_review"}
  ]
}
```

Set each selected cut to `approved` only after a real human decision; record `actor: "human"`, `reviewer`, and `review_note` in that same file. `timeline-changes` requires those fields, rehashes the source, and refuses multiple source clips or an existing timed edit that would need remapping. It emits kept picture spans plus `audio_policy: "mix"` for the [native timeline](../../timeline/SKILL.md); it does not render or approve the final video. Run `timeline.py revise`, `validate`, bounded `preview`, `fingerprint`, human timeline approval, `render`, and `verify` under the approved workflow checklist. Check the exact final join and synchronized sound, and keep `REVIEW`/`SKIP` if the cut is worse than the source.

This first route accepts SDR constant-frame-rate video. It refuses HDR/Dolby Vision. The current timeline may repeatedly decode a long source when many kept spans are used; benchmark a representative range and estimate the full render before approval. Stabilization remains a separate diagnosis and review decision.

See the [capability matrix](README.md) and [synthetic tests](tests/test_fastpan.py) for limits and evidence.
