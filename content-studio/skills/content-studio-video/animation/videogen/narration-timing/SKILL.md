---
name: content-studio-video-narration-timing
description: Generate and verify narration cues for code-driven videos.
---

# content-studio-video-narration-timing

Before production edits, complete the mandatory `content-studio-workflow` precheck with the exact method, script, outputs, estimate, and review criterion. Use `scripts/narration.mjs` to build timed cues and `scripts/verify-narration.mjs` to check the exact authored phrases and audio. A changed script or recorded voice invalidates the cue cache. Review synchronization in rendered motion.

Before synthesis, run `node content-studio/skills/content-studio-video/animation/videogen/narration-timing/scripts/narration.mjs <draft-folder> --rhythm-only`. It validates authored phrases and writes `assets/generated/audio/narration-rhythm.json` without producing speech. The same advisory report refreshes during normal narration generation. Review runs of similarly long phrases and repeated openings in context; a short phrase should carry a real question, turn, or payoff. For long-form work, review chapter progress as well as individual phrase length. Rhythm suggestions never approve or reject the script.

Record needed but unconfirmed story specifics in the authoring prompt as `unknown` (for example, `ticket_status: unknown`). Do not turn those placeholders into narrated facts. Ask the creator or remove the claim before synthesis; the rhythm report does not verify factual claims.

For narrated animation, assemble and listen to the complete generated or recorded audio before scene authoring, and obtain human approval of that audio. Build scene durations on the approved cue clock. When a Core Explainer scene plan assigns one cue per scene, `videogen align-narration <id>` can update cue timing to exact frame boundaries; it retains the original generated audio, accelerates overlong phrases (up to 1.7×), and pads shorter phrases. Treat any audible alignment change as a new narration candidate: listen to the full result and obtain renewed audio approval before relying on its cues. Rewrite and regenerate phrases that sound rushed. See [the idea-to-explainer route](../references/idea-to-explainer.md).

Use the [narration review loop](../../../review/critique/references/narration-scoring.md) to compare script beats and performed takes. After a correction, verify the revised word or phrase cues on the rendered picture.
