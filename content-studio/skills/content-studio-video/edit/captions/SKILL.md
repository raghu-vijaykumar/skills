---
name: content-studio-video-captions
description: Prepare and review requested captions as a hashed ASS sidecar for the Content Studio delivery timeline.
---

# Requested captions

Use this skill only when the editor explicitly requests captions or supplies an approved caption treatment. Vlog drafts do not generate transcripts or captions by default. Before creating a sidecar, run the mandatory `content-studio-workflow` precheck with `--method captions-ass`, show the exact cue/font plan, and obtain human approval of that plan revision. The `create` command checks that approval and the selected method ID.

Draft a UTF-8 cue sheet with final-picture timecodes, the intended canvas, a font file inside the draft source root, and one or two lines per cue:

```json
{
  "width": 1080,
  "height": 1920,
  "duration_seconds": 12.0,
  "font_name": "Arial",
  "font_source": "assets/arial.ttf",
  "font_size": 70,
  "margin_bottom_fraction": 0.1,
  "cues": [
    {"start": 0.4, "end": 1.9, "text": "A reviewed caption"}
  ]
}
```

```powershell
python content-studio/skills/content-studio-video/edit/captions/scripts/captions.py create `
  --draft <draft> --root <draft> --sheet <draft>/.content-studio/captions/cues.json `
  --sidecar <draft>/.content-studio/captions/captions.ass `
  --handoff <draft>/.content-studio/captions/handoff.json
python content-studio/skills/content-studio-video/edit/captions/scripts/captions.py preview `
  --source <draft>/<id>-manual-edit.mp4 --sidecar <draft>/.content-studio/captions/captions.ass `
  --font <draft>/assets/arial.ttf --start 0.4 --duration 1.5 `
  --output <draft>/.content-studio/captions/preview.mp4
```

The handoff contains a `pending_review` `motion-graphics-ass` operation spanning the entire final picture timeline, with hashes for the ASS sidecar and font. Its cues are bounded to the final picture duration and nonoverlapping; text is checked against the intended lower safe area. Review cue wording, spelling, line breaks, font rendering, occlusion, and phone-size legibility in the bounded preview. A representative source preview is provisional if the final picture has not been rendered. Add the operation to a **new** timeline revision only after review, then seek separate human approval of that exact revision. The timeline binds the sidecar and font bytes and renders them in its single final export. Verify exact cue frames and audio in the delivered master. A changed cue sheet, sidecar, font, or timeline requires fresh review; publishing needs separate authorization.
