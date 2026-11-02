---
name: content-studio-videopreprocess
description: Order and clean original vlog camera clips before editing, with blur and Dolby Vision review gates. Use when raw footage arrives for a draft.
---

# Content Studio Video Preprocess

Read the channel rules and the draft's original camera clips. Preview mixed-device capture order with `python <bundle>/skills/content-studio-videoedit/scripts/content.py order --channel <slug> --draft <id> --dry-run`. Run `order` to record `_timeline.csv` and number camera files by capture time; supply `--utc-offset` when the location offset cannot be inferred. Existing timeline timestamps remain fixed when new clips arrive.

Run `python <bundle>/skills/content-studio-videoedit/scripts/content.py preprocess --channel <slug> --draft <id>`. Inspect its blur spans, stabilization crop, audio cleanup, and review report before applying proposed cuts. Original footage remains available. Dolby Vision outputs must preserve RPU and frame alignment; otherwise use the original video with cleaned audio. Read the [preprocessing guide](../content-studio-videoedit/references/channel-helper.md) for the review flags and output paths.

Hand the reviewed clips and timeline to `content-studio-videoedit` for trim, cut, join, or manual assembly. Do not treat preprocessing as approval of a final master.
