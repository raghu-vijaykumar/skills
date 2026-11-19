---
name: content-studio-video-narration
description: Prepare a complete narration track for listening approval, then place it on an approved vlog picture edit.
---

# content-studio-video-narration

Before production edits, complete the mandatory `content-studio-workflow` precheck with the selected method, exact command, output, estimate, fallback, and review criterion. Start from a hashed, human-approved picture edit, either a manual render or an approved long cut. Draft and validate evidence-linked cues internally against that picture. Use the voice-cloning skill only if cloning was requested and consented. Assemble the complete recorded or synthesized narration track, listen through it at normal speed, and give the editor the playable audio for explicit listening approval. Share written cues if requested; written script review is not required. Apply timecoded feedback and repeat the audio review before placing narration on the video. If the picture edit or voice changes, retime and renew the affected approval.

Place the approved narration on the locked picture timeline. Review the voiced video for cue boundaries, dialogue and ambience, speech clarity, and mix before adding requested motion graphics or ASS overlays. Use the native timeline where it supports every selected operation; `scripts/mix_into_video.py` is a separate voiced-master route when the approved plan calls for it. Verify the encoded audio on the final video.

Use the [narration review loop](../../review/critique/references/narration-scoring.md) to score and fix script and voice windows, then recheck them in the encoded mix.

For a new narrated video, require the [per-cue picture review](../../review/understand/SKILL.md) before assembly. Compare each spoken cue with its frame-reviewed visual start/end. Probe the actual generated or recorded audio at 1.0x. An overlong cue requires a shorter script and a new take; do not speed it up or let it spill into another scene. Score **scene meaning and timing** per cue in the narrated picture, including the first and last audible words, and retain `pending` for unreviewed sections. Repeat that check on the exact encoded master.
