# Content Studio asset catalog

`catalog.json` is the central registry for reusable video assets. Each entry records searchable tags, category, duration, aspect ratios, editable source, and optional exported files. Assets are not considered render-ready until their exports are registered.

```bash
python content-studio/scripts/asset_catalog.py list --query subscribe
python content-studio/scripts/asset_catalog.py show --id like-share-subscribe
python content-studio/scripts/asset_catalog.py plan --id like-share-subscribe --at 20 --format webm --video-duration 120 --output placement.json
```

The `plan` command intentionally refuses to place an asset whose exported file is absent. Once an alpha WebM has been rendered and reviewed, register its path relative to `content-studio/assets` under `rendered_files.webm` in `catalog.json`. The generated placement JSON is a review proposal, **not** an applied timeline edit. The canonical video timeline currently does not render an overlay track; that adapter is separate future work. Preserve original media and require human approval before final export.
