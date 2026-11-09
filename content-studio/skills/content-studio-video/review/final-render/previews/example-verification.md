# Final-render verification example

Illustrative checklist, not a delivered master. `methods.json` is intentionally empty:
this skill verifies an exact render rather than owning a media method.

- Reviewed candidate hash matches the delivered file.
- Representative affected ranges, transitions, overlay timing, color, and audio checked.
- Complete master watched and listened to at delivery size.
- Approved preflight checklist complete; objective metrics used only with a valid reference.
- Human decisions recorded for subjective quality.
- Publication remains a separate explicit authorization.

```powershell
python content-studio/skills/content-studio-video/timeline/scripts/timeline.py verify --record <final.mp4.render.json> --evidence-dir <draft>/.content-studio/timeline/final-review
```
