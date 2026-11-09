# Reproduce the rough-cut preview

`previews/rough-cut.gif` is a real rough cut from two synthetic 5-6 second clips using
the deterministic heuristic, `--detect-scenes`, and `--duration 6s`. The review media
and edit decisions are the actual outputs; no transcript or semantic annotation was
supplied.

```powershell
python content-studio/skills/content-studio-video/edit/autocut/scripts/autocut.py --folder <flat-folder> --duration 6s --output <rough-cut> --detect-scenes --force
```

AutoCut is experimental and explicit-request-only. The rough cut is a proposal, not
publishing approval.
