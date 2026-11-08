---
name: content-studio-video-preprocess
description: Prepare individual camera clips for manual editing, with ordering, audio, blur, and Dolby Vision review.
---

# Camera source preprocessing

Complete the mandatory `content-studio-workflow` precheck and its approved step checklist before changing the draft. Diagnose each source issue, select the exact method script, and preserve the original video.

For a raw folder, run `python <this-skill>/scripts/prepare_clips.py --folder <folder>`; for a channel draft use `--channel <slug> --draft <id>`. The current backend adopts the canonical draft layout in that folder, moving root camera files into `original/`; copy the supplied folder first if its layout must stay unchanged. It records capture order in `.content-studio/_timeline.csv`, quarantines byte-identical copies while retaining them, flags near duplicates for review, and writes per-clip reports and `processed.mp4` or `processed.mov` under `.content-studio/processed-clips/<clip>/`.

The default entrypoint rejects `--final` and `--apply-review`: it does not join clips or remove detected blur. Review audio tuning, blur candidates, stabilization crop, and HDR/Dolby Vision handling. Use `--dv-proof` and `--dv-approved` only after a human checks the proof; when RPU preservation cannot be verified, hand off the original picture with separately cleaned audio. Read [the current backend guide](../../edit/clip-edit/references/channel-helper.md) for flags and output details.

Verify every delivered prepared clip and its audio, then stop for the user's manual edit. AutoCut, narration, upscale, graphics, and publication require later explicit requests and plans.
