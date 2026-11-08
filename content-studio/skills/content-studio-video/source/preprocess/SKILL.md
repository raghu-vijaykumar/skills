---
name: content-studio-video-preprocess
description: Order and diagnose camera originals for manual editing; carry proposed changes into the delivery timeline.
---

# Camera source preprocessing

Complete the mandatory `content-studio-workflow` precheck and its approved step checklist before changing the draft. Diagnose each source issue, select the exact method script, and preserve the original video.

For a raw folder, run `python <this-skill>/scripts/prepare_clips.py --folder <folder>`; for a channel draft use `--channel <slug> --draft <id>`. The backend adopts the canonical draft layout in that folder, moving root camera files into `original/`; copy the supplied folder first if its layout must stay unchanged. It records capture order in `.content-studio/_timeline.csv`, quarantines byte-identical copies while retaining them, and writes per-clip source reports and blur review files under `.content-studio/analysis/source-review/<clip>/`. This entrypoint forces analysis-only mode: it creates no processed clip video and applies no audio cleanup or blur cut.

The entrypoint rejects `--final`, `--apply-review`, `--dv-proof`, and `--dv-approved`. Review blur candidates, audio needs, stabilization crop, and HDR/Dolby Vision handling. Record selected permanent changes as proposed timeline operations, linked to source hashes and reviewed ranges. Map those ranges into the final edited sequence before timeline approval. A separate bounded preview may inform the decision but does not become a delivery source. Read [the current backend guide](../../edit/clip-edit/references/channel-helper.md) for legacy flags and output details.

Stop for the user's manual edit. The supplied manual export enters a new plan, a reviewed delivery timeline, separate human timeline approval, and one final render. AutoCut remains explicit-request-only; publication requires separate authorization.
