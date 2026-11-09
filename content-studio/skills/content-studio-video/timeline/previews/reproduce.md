# Reproduce this timeline preview

The committed `timeline-preview.gif` and `validate.txt` come from a synthetic source
through the real `init -> validate -> preview` route. The fixture plan, approval, and
checklist are synthetic and are not a human production approval.

```powershell
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py init --plan <plan.json> --source <source.mp4> --output <final.mp4> --timeline <timeline-v001.json>
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py validate --timeline <timeline-v001.json>
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py preview --timeline <timeline-v001.json> --output <preview.mp4> --start 0 --duration 4
```

A final render still needs separate human timeline approval matching the exact revision.
