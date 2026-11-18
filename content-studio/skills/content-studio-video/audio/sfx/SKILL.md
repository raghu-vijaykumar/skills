---
name: content-studio-video-sfx
description: Import and audition Earshot sounds, create reviewed effects, and propose evidence-linked SFX cues for edited or code-driven Content Studio video.
---

# Content Studio SFX

The [stock library](../../stock-library/SKILL.md) owns one reusable catalogue. The Earshot bank is pinned and shipped as WAVs under its `assets/media/sfx/earshot/` folder, without copying the Earshot repository into this bundle. Browse its [listening gallery](../../stock-library/assets/earshot-gallery.html) and catalogue before choosing an effect. A bank audit pass establishes technical cleanliness, not creative suitability; listen to the entire effect and tail before approving it for final use. Preserve the original source, exact recipe, license, hash, and Earshot revision when creating a new sound. `fit` outputs remain derivatives of their recording and inherit its rights.

Use `scripts/sfx.py import-bank` only when updating the pinned upstream bank; it refuses any other revision. `forge` and `fit` invoke the pinned Earshot checkout for new candidates and leave those outputs pending review. See [the SFX workflow reference](references/workflow.md) for commands and the event/proposal contract.

For a target video, run the mandatory [Content Studio precheck](../../../content-studio-workflow/SKILL.md) and obtain human approval of its exact production plan before an edit. On edited footage, use timed cut and audio evidence plus sampled frames to identify actual visible events; sparse sampling alone cannot identify an action between frames. On code-driven work, use authored scene state changes and narration cues. Record each proposal's picture evidence and original audio context. Prefer no effect for dialogue, meaningful natural sound, or uncertain meaning. An automated proposal is never a human approval.

After reviewing a bounded picture-and-sound preview, place selected cues on the approved SDR delivery timeline or in the Remotion composition and inspect the exact output. For HDR/Dolby Vision supplied edits, use only the verified audio-only stream-copy route; never render the picture through the SDR adapter. Follow separate timeline approval and exact-master listening before delivery. Publication still needs its separate authorization.
