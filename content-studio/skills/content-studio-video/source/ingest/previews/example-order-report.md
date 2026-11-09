# Capture-order example

Illustrative report, not a real draft mutation. `order.py` reads capture metadata and
renames in capture order; `--dry-run` previews the plan.

```powershell
python content-studio/skills/content-studio-video/source/ingest/scripts/order.py --draft <draft> --utc-offset +04:00 --dry-run
```

Example result: three synthetic clips ordered by embedded creation time, with one
filename collision reported for review. Exact-duplicate quarantine and near-duplicate
review belong to the source preprocessor.
