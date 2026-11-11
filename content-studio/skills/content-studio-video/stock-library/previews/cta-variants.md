# CTA variant review evidence

The first shared stock production run rendered `classic-bar`, `minimal-pills`, and
`bold-stack` as 3840×2160/30, five-second silent ProRes 4444 clips with alpha.
The original `classic-bar` was copied bit for bit from the previously approved
Out of Office asset. The new variants were decoded from their delivered files
at 0.9, 1.6, 2.6, and 3.6 seconds. Their Like, Share, Subscribed, and bell
states were inspected on a neutral background; 1:1 bell crops were inspected
for legibility. All three paths, hashes, stream probes, and review frames are
recorded in the private stock library's `.content-studio/review.json`. The
editor approved the exact clips for reuse on 2026-11-10. No full-resolution
generated media or private catalogue is committed to this repository. The three
small catalogue GIFs are derived from those exact MOVs, composited over a still
from the published Out of Office Mode Dubai Fountain video at 95 seconds. They
demonstrate motion and placement, not transparent delivery pixels or color
fidelity.

Rebuild them from the private approved library and the local public-video copy:

```powershell
python content-studio/skills/content-studio-video/stock-library/scripts/build_gallery.py --library content-studio/skills/content-studio-video/stock-library/assets --background-video <published-fountain-video.mp4> --at 95
```

This approval covers the reusable clips. Each later video still needs its own
placement and color-preserving composition review.
