---
name: content-studio-video-final-render
description: Verify the exact delivered video and audio before package approval.
---

# content-studio-video-final-render

Before production edits, complete the mandatory `content-studio-workflow` precheck with the selected method, exact script, output, estimate, fallback, and review criterion. Inspect representative affected ranges, transitions, overlay timing, color, audio, and the complete master. Confirm that the file hash matches the reviewed candidate and that the approved plan checklist is complete. Use objective quality tools only where a valid reference exists; record human decisions for subjective issues. This review skill does not auto-approve publication.

Run `inspect-exact-master` on the **exact delivered bytes**, using the output SHA-256 from the render record:

```powershell
python content-studio/skills/content-studio-video/review/final-render/scripts/inspect.py `
  --master <draft>/<id>-final.mp4 --sha256 <render-record-output-sha256> `
  --evidence-dir <draft>/.content-studio/timeline/final-review/safe-zones `
  --report <draft>/.content-studio/timeline/final-review/master-inspection.json
```

The inspector records container, video/audio codec, dimensions, frame-rate and color metadata, integrated loudness, true peak, timecoded black/frozen/one-frame-flash and audio-silence candidates, and 5%/10% guide frames. A duration of black, stillness, or silence may be intentional; every detector finding is `REVIEW`, not an automatic defect or correction. The guide frames are separate evidence files; assess typography, face/subject placement and destination overlays at phone size. The source master is never rewritten. A missing or changed hash fails before inspection and a changed master during inspection fails afterward.

`timeline.py verify` invokes the same inspector after checking its approved revision and exact output hash. It writes the technical report into `review-manifest.json` when an evidence directory is supplied. Compare format and color metadata with the approved delivery intent; inspect the exact output visually and listen to it before package approval. Detector thresholds are candidate finders, not quality scores. A content decision, including an intentional black or silent beat, must be recorded by a human.

Close each finding as an issue-specific feedback loop: record the affected
time, baseline signal and acceptance criterion; mark intentional content
`SKIP`, or make one bounded timeline fix and preview it. Review side effects,
create a newly approved timeline revision, rerender once, and rerun this
inspector on the **new exact master hash**. A remaining or subjective defect
stays `REVIEW`; successful encoding alone never changes it to `FIX`. Keep the
old report as evidence of the rejected or superseded candidate.
