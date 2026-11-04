---
name: content-studio-motion-graphics
description: Add timed ingredient callouts and like/share/subscribe graphics to an already edited Out of Office Mode cooking video, then render a separate review copy.
---

# Out of Office Mode motion graphics

Read the channel rules, this skill, and the source draft before editing. Keep the source video untouched. Extract audio and inspect sparse frames or short ranges to identify actions without decoding the entire master for analysis. Use speech as context, but only label ingredients actually supported by the frame or clear narration; do not invent quantities.

Create a JSON cue sheet with source path and timed `ingredient` or `cta` events. Each ingredient cue includes the ingredient name, action, and a brief evidence note. Place the callout when the ingredient is used, not merely when it appears on a prep board. Keep overlays away from hands, food, faces, and existing text. The renderer uses cream recipe cards, teal type, coral icons, and yellow accents from the Out of Office Mode intro. Put like/share/subscribe near a natural ending beat instead of interrupting instruction.

Use `python scripts/overlay.py validate <cues.json>` to check timing, then `python scripts/overlay.py render <cues.json> --output <review.mp4> [--start seconds --duration seconds]`. The render is a separate 1080p SDR review copy with source audio; HLG footage is tone mapped for review, not silently relabeled as the HDR master. The script writes an ASS motion-graphic source beside the output. Review isolated hero frames, then the actual composed video at opening, every callout, and ending. Revise cue timing and layout from those frames. Preserve the cue sheet and review output together; publication remains a separate request.
