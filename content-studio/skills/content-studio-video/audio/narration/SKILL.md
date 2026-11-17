---
name: content-studio-video-narration
description: Place approved recorded or generated narration on a supplied edited-video timeline.
---

# content-studio-video-narration

Before production edits, complete the mandatory `content-studio-workflow` precheck with the selected method, exact script, output, estimate, fallback, and review criterion. Start from the user's hashed manual render and approved, evidence-linked script. Use the voice-cloning skill only if cloning was requested and consented. Assemble recorded or synthesized audio against the edit, listen to the timing and mix, then use `scripts/mix_into_video.py` for a separate voiced master. If the edit changes, retime and review before another mix.

Use the [narration review loop](../../review/critique/references/narration-scoring.md) to score and fix script and voice windows, then recheck them in the encoded mix.

For a new narrated video, require the [per-cue picture review](../../review/understand/SKILL.md) before assembly. Compare each spoken cue with its frame-reviewed visual start/end. Probe the actual generated or recorded audio at 1.0x. An overlong cue requires a shorter script and a new take; do not speed it up or let it spill into another scene. Score **scene meaning and timing** per cue in the narrated picture, including the first and last audible words, and retain `pending` for unreviewed sections. Repeat that check on the exact encoded master.
