# Reproduce this preprocessing report

The committed `report.json` is the actual analysis report for a synthetic clip, with
absolute scratch paths removed. It is analysis-only evidence, not a processed delivery
clip.

```powershell
python content-studio/skills/content-studio-video/source/preprocess/scripts/prepare_clips.py --path <synthetic-clip> --out <scratch>/processed
```

The entrypoint forces analysis-only mode and rejects `--final`, `--apply-review`,
`--dv-proof`, and `--dv-approved`. It records capture order, quarantines byte-identical
copies, and writes per-clip review files.
