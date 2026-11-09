# Archive example

Illustrative report, not a real channel backup.

```powershell
python content-studio/skills/content-studio-videoedit/scripts/content.py backup --channel <slug>
python content-studio/skills/content-studio-videoedit/scripts/content.py sync --channel <slug>
```

Expected evidence: exact public title/description/thumbnail, source reconciliation,
and `rclone check` output. Git tracks metadata and small source; large media stays on
Drive. Unpublished or scheduled videos remain drafts.
