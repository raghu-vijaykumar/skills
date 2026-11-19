---
name: content-studio-video-sync
description: Diagnose separate-recorder audio offset and drift, review a bounded audition, and hand a confirmed alignment to the delivery timeline.
---

# Separate-recorder sync

The analysis script requires FFmpeg, FFprobe, and Python NumPy.

Use this skill when camera picture and a separate recorder share audible content. During raw source preparation, compare the originals and hand the result to the editor for the manual edit; do not export enhanced full-length clips. Analysis is read-only and the audition is a short comparison preview. Before permanent alignment, complete the mandatory `content-studio-workflow` precheck with the exact selected method, commands, estimate, output and review criterion, then get human approval.

```powershell
python content-studio/skills/content-studio-video/source/sync/scripts/sync.py analyze `
  --reference <camera-or-manual-edit.mp4> --external <recorder.wav> `
  --search-seconds 60 --report <draft>/.content-studio/analysis/sync-report.json
python content-studio/skills/content-studio-video/source/sync/scripts/sync.py audition `
  --report <draft>/.content-studio/analysis/sync-report.json `
  --at 5 --duration 5 --output <draft>/.content-studio/analysis/sync-audition.wav
```

The report hashes both inputs, estimates the recorder's offset on the picture timeline and, when the sources are long enough, estimates drift from two separated windows. `REVIEW` means a bounded candidate exists; listen to the stereo audition (camera left, recorder right) and inspect early/late anchors before accepting it. Silent, steady or ambiguous audio returns `UNSUPPORTED` with no offset. A short clip can have an offset candidate with unknown drift; record an explicit zero-drift assumption if using it. These estimates are not proof of synchronization, and no automatic correction is applied.

For a supplied manual edit, **reanalyze against that exact rendered edit**. A raw-camera report cannot be transferred across manual cuts. A human-reviewed timeline may add one `external_sync` audio cue with the report/source hashes, exact `offset_seconds`, `drift_ppm` (or explicit short-clip zero-drift assumption), `start: 0`, `review_status: approved`, and the manual picture clip's `audio_gain: 0`. The [timeline](../../timeline/SKILL.md) validates one uncut SDR picture, matching source/report bytes, and separate timeline approval, then applies trim, drift tempo and delay inside its single final audio encode. Check early and late sync in the exact output. HDR/Dolby Vision picture-copy and cut timelines are currently unsupported by this adapter.

```json
{
  "id": "external-mic",
  "kind": "external_sync",
  "source": "original/recorder.wav",
  "sha256": "<recorder-sha256>",
  "sync_report_source": ".content-studio/analysis/manual-edit-sync.json",
  "sync_report_sha256": "<report-sha256>",
  "start": 0,
  "offset_seconds": 0.42,
  "drift_ppm": 75.0,
  "review_status": "approved"
}
```

For a short report with `drift_ppm: null`, set cue `drift_ppm: 0` and `drift_assumption: "zero_for_short_clip"` only after listening. Long clips with uncertain drift cannot use that assumption.
