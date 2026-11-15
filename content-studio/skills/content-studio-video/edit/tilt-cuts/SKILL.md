---
name: content-studio-video-tilt-cuts
description: Detect sustained camera roll, review removals above a chosen angle, and hand exact picture and audio cuts to the native delivery timeline.
---

# Tilt cuts

Use this leaf when the camera is visibly slanted and the editor prefers removing the affected footage. Start with the mandatory [`content-studio-workflow`](../../../content-studio-workflow/SKILL.md) precheck. A read-only scan and short join previews can inform the plan; obtain human approval of the current detailed plan before editing or final rendering. A changed plan requires another review. Record the source, threshold, exact method commands and arguments, output, time estimate, fallback, and review criteria.

`scan` measures dominant straight-edge angle in small sampled frames. It flags sustained **scene-line angles** above `--threshold-deg 10`; that is a shortlist, not a reliable camera-roll measurement. Perspective, slanted architecture, floor views, and intentional framing can trigger it. A 90-degree camera turn can fold to 0 degrees. Inspect temporal frames, the horizon or known verticals, action, and sound inside and outside candidates. Mark each as actual camera roll, intentional angle, uncertain, or false positive. Choose exact source-frame cuts only for confirmed unwanted camera roll. Do not auto-approve or erase context, speech, or a usable shot solely because the score exceeds the threshold.

## Commands

```powershell
$tilt = 'content-studio/skills/content-studio-video/edit/tilt-cuts/scripts/tilt.py'
python $tilt scan --input <source.mp4> --threshold-deg 10 --sample-fps 1 --output <draft>/.content-studio/analysis/tilt-cuts/candidates-v001.json
python $tilt preview --input <source.mp4> --decisions <decisions-v001.json> --cut-id <id> --padding 2 --output <draft>/.content-studio/analysis/tilt-cuts/<id>-join.mp4
python $tilt timeline-changes --input <source.mp4> --decisions <approved-decisions.json> --timeline <uncut-timeline.json> --output <changes-v002.json>
```

The source must be SDR constant-frame-rate video. The scan report includes a source SHA-256, size, modification time, frame rate, per-frame samples, and unapproved candidates. The preview only encodes the context on both sides of one proposed removal, with matching audio trims. It handles a long cut without encoding the entire removed section. Watch the removed range separately and review each join for visual continuity and speech/music damage.

Build a decision file from the scan report's source fields and checked frame numbers:

```json
{
  "schema": "content-studio.tilt-decisions.v1",
  "source": "<absolute source path>",
  "source_sha256": "<scan report SHA-256>",
  "source_bytes": 123456,
  "source_mtime_ns": 123456789,
  "fps": 30,
  "threshold_deg": 10,
  "cuts": [
    {"id": "tilt-0001", "start_frame": 1800, "end_frame": 1890, "review_status": "pending_review", "reason": "confirmed camera roll"}
  ]
}
```

After a real human decision, set each selected cut's `review_status` to `approved` and add `actor: "human"`, `reviewer`, and `review_note`. `timeline-changes` checks source integrity, human approval, exact frame bounds, and the uncut single-source timeline. It emits kept spans and matching audio policy, but does not render. Continue through [timeline](../../timeline/SKILL.md) `revise`, `validate`, bounded `preview`, `fingerprint`, separate human approval of that exact fingerprint, `render`, and `verify`. Inspect the exact delivered joins and audio before claiming success; if a join is worse, revise it or record `REVIEW`/`SKIP`.

Keep the previous source and cut master intact. Current timeline rendering may repeatedly decode a long source across many kept spans; benchmark before the full run. Stabilization or rotation correction requires its own reviewed operation and is not implied by this cut skill. See the [capability matrix](README.md) and [tests](tests/test_tilt.py).
