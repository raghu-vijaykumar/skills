---
name: content-studio-video-stock-library
description: Select and create reusable transparent video CTA variants, and catalogue self-created clips, memes, GIFs, and stickers for use across Content Studio videos.
---

# Stock library

Use this skill when an editor wants reusable authored visual assets across videos. Browse the [stock catalogue](README.md) for available CTA designs, then use `scripts/cta.py list` and `render --variant` to select one. The default `classic-bar` preserves the existing approved Like / Share / Subscribe animation; other variants use the same timed state sequence. Generated footage is silent with an alpha channel, so compositing does not alter the source picture outside the graphic or replace its audio.

Before a **full asset render or video insertion**, run the mandatory `content-studio-workflow` precheck for the target project, present the exact method, command, destination, estimate, fallback, and review criteria, and obtain human approval of that plan revision. Review a bounded comparison first. For video placement, approve the cue/timeline or supported specialist manifest separately and inspect the exact delivered picture and sound. A stock clip is never automatically placed on every video; choose placement and timing against each shot. Catalogue import of media already approved for reuse can be done independently; confirm ownership and rights before indexing.

Run from the source repository root after approval:

```powershell
python content-studio/skills/content-studio-video/stock-library/scripts/cta.py list
python content-studio/skills/content-studio-video/stock-library/scripts/cta.py render --variant minimal-pills --output <private-assets>/like-share-subscribe-minimal-pills-uhd-alpha.mov --width 3840 --height 2160 --fps 30 --duration 5.0 --position top-right
```

The renderer needs Pillow, FFmpeg, FFprobe, and a bold Arial or DejaVu Sans font. It refuses to overwrite an existing asset. Confirm the output pixel format has an alpha channel, dimensions, no audio, and the Like, Share, Subscribe, Subscribed, and bell states over representative footage. For HDR/HLG work, the existing narrow [motion-graphics composer](../edit/motion-graphics/SKILL.md) may consume a reviewed stock clip. The generic delivery timeline does not yet support this alpha overlay operation.

For **self-created** memes, GIFs, stickers, and stock clips, use `scripts/library.py` with a private folder outside Git. Supply true rights and creator metadata. The importer copies and SHA-256 deduplicates files, preserves the original, and regenerates that private folder's `README.md` catalogue. It does not make source footage or licensed assets public. See the [catalogue guide](README.md) for commands and ownership boundaries. The [memes skill](../memes/SKILL.md) continues to handle contextual reaction suggestions and rights/timing review.
