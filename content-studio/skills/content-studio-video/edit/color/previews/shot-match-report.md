# Shot-match example

Illustrative report, not a measured match. `shot_match.py` matches a clip's mean
channel balance to a supplied reference and preserves both inputs.

```powershell
python content-studio/skills/content-studio-video/edit/color/scripts/shot_match.py --input <clip> --reference <reference> --output <matched.mp4>
```

Review temporal consistency and the affected ranges against the untouched edit.
