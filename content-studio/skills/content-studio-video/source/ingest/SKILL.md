---
name: content-studio-video-ingest
description: Order and deduplicate camera clips before manual editing.
---

# content-studio-video-ingest

Before production edits, complete the mandatory `content-studio-workflow` precheck with the selected method, exact script, output, estimate, fallback, and review criterion. Use `scripts/order.py` for capture-time ordering in a draft. The source preprocessor also performs exact-duplicate quarantine and near-duplicate review; use it for a raw folder until the standalone dedupe entrypoint is extracted. Preserve originals and review renames and quarantined copies. Run the workflow precheck before mutations.
