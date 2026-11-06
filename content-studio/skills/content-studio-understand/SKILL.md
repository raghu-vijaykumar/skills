---
name: content-studio-understand
description: Analyze sparse frames from an approved vlog edit, combine verified visual evidence with human context, and draft timestamped voiceover for review.
---
# Content Studio Understand

Before changing production material, complete the mandatory human-reviewed precheck in `content-studio-workflow` and follow its approved step checklist. Read-only evidence extraction may inform the plan.
Run only against the **approved edit** or a review candidate explicitly supplied by the user. Do not infer landmarks, identities, speech, or events from filenames. Sparse frames cannot establish everything happening between samples. Use the generated contact sheet and timestamped evidence to ask the user about ambiguous scenes.

```bash
python content-studio/skills/content-studio-understand/scripts/understand.py --video /path/to/approved-final.mp4 --out /path/to/draft/.content-studio/understanding --interval 8 --context /path/to/context.json
```

The script extracts representative frames and a JSON evidence manifest. A vision-capable agent should inspect those frames and write `observations.json` as an array of `{start,end,description,confidence,frame_ids}` using only observed evidence. The agent then drafts `voiceover.json` with `{start,end,text,evidence_frame_ids,needs_review}` and `voiceover.md`, using `context.json` for human-supplied names, experiences, language, tone, and preferences. Never fabricate observations or imply the script itself performed vision inference. Mark uncertain assertions for human review.

Voiceover must fit the **approved timeline**; use scene times in the rendered master, not raw source timestamps. Leave room for original dialogue where requested. Obtain explicit human approval of the final narration text and timing before synthesizing or recording audio. A changed final master invalidates the approval and requires regeneration or retiming.
